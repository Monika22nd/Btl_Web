from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import APP_NAME
from database import get_db
from dao import cart_dao, product_dao

router = APIRouter()
templates = Jinja2Templates(directory="views")


def _session_ctx(request: Request, db: Session) -> dict:
    user_id = request.session.get("user_id")
    cart_count = 0
    if user_id:
        cart_count = cart_dao.count_by_user(db, user_id)
    return {
        "user_id": user_id,
        "user_name": request.session.get("user_name"),
        "is_admin": request.session.get("is_admin", False),
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
    cart_items = cart_dao.list_by_user(db, user_id)
    cart_total = cart_dao.total(cart_items)
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

    product = product_dao.get_by_id(db, product_id)
    if not product:
        return RedirectResponse(url="/", status_code=303)

    cart_dao.add_or_update_item(db, user_id, product, quantity)
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

    item = cart_dao.get_item(db, item_id, user_id)
    if item:
        if quantity <= 0:
            product_name = item.product.name
            cart_dao.remove_item(db, item)
            request.session["flash"] = f"Đã xoá '{product_name}' khỏi giỏ hàng."
        else:
            cart_dao.update_quantity(db, item, quantity)

    return RedirectResponse(url="/gio-hang", status_code=303)


# ── POST /gio-hang/xoa/{item_id} — Xoá một sản phẩm ─────────────────────────
@router.post("/gio-hang/xoa/{item_id}")
def cart_remove(item_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/dang-nhap", status_code=303)

    item = cart_dao.get_item(db, item_id, user_id)
    if item:
        request.session["flash"] = f"Đã xoá '{item.product.name}' khỏi giỏ hàng."
        cart_dao.remove_item(db, item)

    return RedirectResponse(url="/gio-hang", status_code=303)


# ── POST /gio-hang/xoa-tat-ca — Xoá toàn bộ giỏ ─────────────────────────────
@router.post("/gio-hang/xoa-tat-ca")
def cart_clear(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/dang-nhap", status_code=303)

    cart_dao.clear_by_user(db, user_id)
    request.session["flash"] = "Đã xoá toàn bộ giỏ hàng."
    return RedirectResponse(url="/gio-hang", status_code=303)
