from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
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
    return {"user_id": user_id, "user_name": user_name, "cart_count": cart_count, "APP_NAME": APP_NAME}


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
def login_page(request: Request, db: Session = Depends(get_db)):
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=303)
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, **_session_ctx(request, db), "error": None, "flash": flash},
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
