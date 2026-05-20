import json
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import APP_NAME
from database import get_db
from models import User, CartItem

router = APIRouter()
templates = Jinja2Templates(directory="views")


def _session_ctx(request: Request, db: Session) -> dict:
    user_id = request.session.get("user_id")
    user_name = request.session.get("user_name")
    cart_count = 0
    if user_id:
        cart_count = db.query(CartItem).filter(CartItem.user_id == user_id).count()
    return {
        "user_id": user_id,
        "user_name": user_name,
        "is_admin": request.session.get("is_admin", False),
        "cart_count": cart_count,
        "APP_NAME": APP_NAME,
    }


async def _read_api_data(request: Request) -> dict:
    body = await request.body()
    if not body:
        return {}

    try:
        data = json.loads(body)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        parsed = parse_qs(body.decode("utf-8", errors="ignore"))
        return {key: values[-1] for key, values in parsed.items()}


# ── GET /dang-ky ──────────────────────────────────────────────────────────────
@router.get("/dang-ky", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        "register.html", {"request": request, **_session_ctx(request, db), "error": None}
    )


# ── POST /dang-ky ─────────────────────────────────────────────────────────────
@router.post("/dang-ky", response_class=HTMLResponse)
def register(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(default=""),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    ctx = {**_session_ctx(request, db), "full_name": full_name, "email": email, "phone": phone}

    if len(password) < 6:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, **ctx, "error": "Mật khẩu phải có ít nhất 6 ký tự."},
            status_code=400,
        )

    existing = db.query(User).filter(User.email == email.lower().strip()).first()
    if existing:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, **ctx, "error": "Email này đã được đăng ký."},
            status_code=400,
        )

    user = User(full_name=full_name.strip(), email=email.lower().strip(), phone=phone.strip() or None)
    user.set_password(password)
    db.add(user)
    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id
    request.session["user_name"] = user.full_name
    request.session["is_admin"] = user.is_admin
    request.session["flash"] = f"Chào mừng {user.full_name}! Đăng ký thành công."
    return RedirectResponse(url="/", status_code=303)


# ── GET /dang-nhap ────────────────────────────────────────────────────────────
@router.get("/dang-nhap", response_class=HTMLResponse)
def login_page(request: Request, next: str = "/", db: Session = Depends(get_db)):
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=303)
    if not next.startswith("/"):
        next = "/"
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, **_session_ctx(request, db), "error": None, "flash": flash, "next": next},
    )


# ── POST /dang-nhap ───────────────────────────────────────────────────────────
@router.post("/dang-nhap", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form(default="/"),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email.lower().strip()).first()

    if not user or not user.verify_password(password):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                **_session_ctx(request, db),
                "error": "Email hoặc mật khẩu không đúng.",
                "email": email,
                "flash": None,
                "next": next,
            },
            status_code=401,
        )

    request.session["user_id"] = user.id
    request.session["user_name"] = user.full_name
    request.session["is_admin"] = user.is_admin
    request.session["flash"] = f"Đăng nhập thành công! Chào {user.full_name}."

    if not next.startswith("/"):
        next = "/"
    return RedirectResponse(url=next, status_code=303)


# ── JSON auth API ─────────────────────────────────────────────────────────────
@router.post("/api/auth/login")
async def api_login(request: Request, db: Session = Depends(get_db)):
    data = await _read_api_data(request)
    email = str(data.get("email", "")).lower().strip()
    password = str(data.get("password", ""))

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.verify_password(password):
        return JSONResponse(
            {"success": False, "message": "Email hoặc mật khẩu không đúng."},
            status_code=401,
        )

    request.session["user_id"] = user.id
    request.session["user_name"] = user.full_name
    request.session["is_admin"] = user.is_admin

    return {
        "success": True,
        "message": "Đăng nhập thành công.",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "is_admin": user.is_admin,
        },
    }


@router.post("/api/auth/register")
async def api_register(request: Request, db: Session = Depends(get_db)):
    data = await _read_api_data(request)
    full_name = str(data.get("full_name") or data.get("name") or "").strip()
    email = str(data.get("email", "")).lower().strip()
    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", ""))

    if not full_name or not email or not password:
        return JSONResponse(
            {"success": False, "message": "Vui lòng nhập đầy đủ họ tên, email và mật khẩu."},
            status_code=400,
        )
    if len(password) < 6:
        return JSONResponse(
            {"success": False, "message": "Mật khẩu phải có ít nhất 6 ký tự."},
            status_code=400,
        )
    if db.query(User).filter(User.email == email).first():
        return JSONResponse(
            {"success": False, "message": "Email này đã được đăng ký."},
            status_code=400,
        )

    user = User(full_name=full_name, email=email, phone=phone or None)
    user.set_password(password)
    db.add(user)
    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id
    request.session["user_name"] = user.full_name
    request.session["is_admin"] = user.is_admin

    return {
        "success": True,
        "message": "Đăng ký thành công.",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "is_admin": user.is_admin,
        },
    }


@router.post("/api/auth/logout")
def api_logout(request: Request):
    request.session.clear()
    return {"success": True, "message": "Đăng xuất thành công."}


# ── GET /dang-xuat ────────────────────────────────────────────────────────────
@router.get("/dang-xuat")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


# ── GET /tai-khoan ────────────────────────────────────────────────────────────
@router.get("/tai-khoan", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/dang-nhap", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        return RedirectResponse(url="/dang-nhap", status_code=303)

    from models import Order
    orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
    flash = request.session.pop("flash", None)

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            **_session_ctx(request, db),
            "current_user": user,
            "orders": orders,
            "flash": flash,
            "error": None,
        },
    )


# ── POST /tai-khoan ───────────────────────────────────────────────────────────
@router.post("/tai-khoan", response_class=HTMLResponse)
def profile_update(
    request: Request,
    full_name: str = Form(...),
    phone: str = Form(default=""),
    address: str = Form(default=""),
    current_password: str = Form(default=""),
    new_password: str = Form(default=""),
    confirm_new_password: str = Form(default=""),
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/dang-nhap", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()

    from models import Order
    orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()

    def error(msg):
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                **_session_ctx(request, db),
                "current_user": user,
                "orders": orders,
                "flash": None,
                "error": msg,
            },
            status_code=400,
        )

    if current_password:
        if not user.verify_password(current_password):
            return error("Mật khẩu hiện tại không đúng.")
        if len(new_password) < 6:
            return error("Mật khẩu mới phải có ít nhất 6 ký tự.")
        if new_password != confirm_new_password:
            return error("Mật khẩu mới xác nhận không khớp.")
        user.set_password(new_password)

    user.full_name = full_name.strip()
    user.phone = phone.strip() or None
    user.address = address.strip() or None
    db.commit()

    request.session["user_name"] = user.full_name
    request.session["flash"] = "Cập nhật thông tin thành công!"
    return RedirectResponse(url="/tai-khoan", status_code=303)
