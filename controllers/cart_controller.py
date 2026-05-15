from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import APP_NAME
from database import get_db
from models import CartItem, Product

router = APIRouter()
templates = Jinja2Templates(directory="views")


def _session_ctx(request: Request, db: Session) -> dict:
    user_id = request.session.get("user_id")
    cart_count = 0
    if user_id:
        cart_count = db.query(CartItem).filter(CartItem.user_id == user_id).count()
    return {
        "user_id": user_id,
        "user_name": request.session.get("user_name"),
        "cart_count": cart_count,
        "APP_NAME": APP_NAME,
    }


# ── GET /gio-hang ─────────────────────────────────────────────────────────────
@router.get("/gio-hang", response_class=HTMLResponse)
def cart_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/dang-nhap", status_code=303)

    ctx = _session_ctx(request, db)
    cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    cart_total = sum(item.product.price * item.quantity for item in cart_items)
    flash = request.session.pop("flash", None)

    return templates.TemplateResponse(
        "cart.html",
        {"request": request, **ctx, "cart_items": cart_items, "cart_total": cart_total, "flash": flash},
    )


# ── POST /gio-hang/them/{product_id} — Thêm vào giỏ ─────────────────────────
@router.post("/gio-hang/them/{product_id}")
def cart_add(
    product_id: int,
    request: Request,
    quantity: int = Form(default=1),
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/dang-nhap", status_code=303)

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/", status_code=303)

    quantity = max(1, quantity)
    existing = db.query(CartItem).filter(
        CartItem.user_id == user_id, CartItem.product_id == product_id
    ).first()

    if existing:
        existing.quantity = min(existing.quantity + quantity, product.stock)
    else:
        db.add(CartItem(user_id=user_id, product_id=product_id, quantity=min(quantity, product.stock)))

    db.commit()
    request.session["flash"] = f"Đã thêm '{product.name}' vào giỏ hàng!"
    # Redirect về trang trước (referer) hoặc trang sản phẩm
    referer = request.headers.get("referer", f"/san-pham/{product.slug}")
    return RedirectResponse(url=referer, status_code=303)


# ── POST /gio-hang/cap-nhat/{item_id} — Cập nhật số lượng ────────────────────
@router.post("/gio-hang/cap-nhat/{item_id}")
def cart_update(
    item_id: int,
    request: Request,
    quantity: int = Form(...),
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/dang-nhap", status_code=303)

    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user_id).first()
    if item:
        if quantity <= 0:
            db.delete(item)
            request.session["flash"] = f"Đã xoá '{item.product.name}' khỏi giỏ hàng."
        else:
            item.quantity = min(quantity, item.product.stock)
        db.commit()

    return RedirectResponse(url="/gio-hang", status_code=303)


# ── POST /gio-hang/xoa/{item_id} — Xoá một sản phẩm ─────────────────────────
@router.post("/gio-hang/xoa/{item_id}")
def cart_remove(item_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/dang-nhap", status_code=303)

    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user_id).first()
    if item:
        request.session["flash"] = f"Đã xoá '{item.product.name}' khỏi giỏ hàng."
        db.delete(item)
        db.commit()

    return RedirectResponse(url="/gio-hang", status_code=303)


# ── POST /gio-hang/xoa-tat-ca — Xoá toàn bộ giỏ ─────────────────────────────
@router.post("/gio-hang/xoa-tat-ca")
def cart_clear(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/dang-nhap", status_code=303)

    db.query(CartItem).filter(CartItem.user_id == user_id).delete()
    db.commit()
    request.session["flash"] = "Đã xoá toàn bộ giỏ hàng."
    return RedirectResponse(url="/gio-hang", status_code=303)
