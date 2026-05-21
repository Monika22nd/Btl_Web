from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import APP_NAME
from database import get_db
from models import Order, OrderItem, CartItem, Product, User
from models.order import ORDER_STATUS

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
        "is_admin": request.session.get("is_admin", False),
        "cart_count": cart_count,
        "APP_NAME": APP_NAME,
    }


# ── GET /thanh-toan ───────────────────────────────────────────────────────────
@router.get("/thanh-toan", response_class=HTMLResponse)
def checkout_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/dang-nhap", status_code=303)

    cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    if not cart_items:
        return RedirectResponse(url="/gio-hang", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    cart_total = sum(item.product.price * item.quantity for item in cart_items)

    return templates.TemplateResponse("checkout.html", {
        "request": request,
        **_session_ctx(request, db),
        "cart_items": cart_items,
        "cart_total": cart_total,
        "current_user": user,
        "error": None,
    })


# ── POST /thanh-toan — nhận thêm recipient_name ───────────────────────────────
@router.post("/thanh-toan")
def checkout_submit(
    request: Request,
    recipient_name: str = Form(...),
    shipping_address: str = Form(...),
    phone: str = Form(...),
    note: str = Form(default=""),
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/dang-nhap", status_code=303)

    cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    if not cart_items:
        return RedirectResponse(url="/gio-hang", status_code=303)

    for item in cart_items:
        if item.product.stock < item.quantity:
            cart_total = sum(i.product.price * i.quantity for i in cart_items)
            user = db.query(User).filter(User.id == user_id).first()
            return templates.TemplateResponse("checkout.html", {
                "request": request,
                **_session_ctx(request, db),
                "cart_items": cart_items,
                "cart_total": cart_total,
                "current_user": user,
                "error": f"'{item.product.name}' chỉ còn {item.product.stock} trong kho.",
            }, status_code=400)

    total = sum(item.product.price * item.quantity for item in cart_items)

    order = Order(
        user_id=user_id,
        total=total,
        status="pending",
        shipping_address=shipping_address.strip(),
        phone=phone.strip(),
        note=note.strip() or None,
        recipient_name=recipient_name.strip(),
    )
    db.add(order)
    db.flush()

    for item in cart_items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price,
        ))
        item.product.stock -= item.quantity

    db.query(CartItem).filter(CartItem.user_id == user_id).delete()
    db.commit()

    request.session["flash"] = f"Đặt hàng thành công! Mã đơn hàng: #{order.id}"
    return RedirectResponse(url=f"/don-hang/{order.id}", status_code=303)


# ── GET /don-hang ─────────────────────────────────────────────────────────────
@router.get("/don-hang", response_class=HTMLResponse)
def order_list(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/dang-nhap", status_code=303)

    orders = (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )
    flash = request.session.pop("flash", None)

    return templates.TemplateResponse("orders.html", {
        "request": request,
        **_session_ctx(request, db),
        "orders": orders,
        "ORDER_STATUS": ORDER_STATUS,
        "flash": flash,
    })


# ── GET /don-hang/{id} ────────────────────────────────────────────────────────
@router.get("/don-hang/{order_id}", response_class=HTMLResponse)
def order_detail(order_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/dang-nhap", status_code=303)

    ctx = _session_ctx(request, db)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return templates.TemplateResponse("404.html", {"request": request, **ctx}, status_code=404)

    is_admin = request.session.get("is_admin", False)
    if order.user_id != user_id and not is_admin:
        return templates.TemplateResponse("404.html", {"request": request, **ctx}, status_code=403)

    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    flash = request.session.pop("flash", None)

    return templates.TemplateResponse("order_detail.html", {
        "request": request, **ctx,
        "order": order,
        "items": items,
        "ORDER_STATUS": ORDER_STATUS,
        "flash": flash,
    })


# ── POST /don-hang/{id}/huy — Huỷ (user, chỉ khi pending) ───────────────────
@router.post("/don-hang/{order_id}/huy")
def order_cancel(order_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/dang-nhap", status_code=303)

    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
    if not order:
        return RedirectResponse(url="/don-hang", status_code=303)

    if order.status != "pending":
        request.session["flash"] = "Chỉ có thể huỷ đơn hàng đang chờ xác nhận."
        return RedirectResponse(url=f"/don-hang/{order_id}", status_code=303)

    for item in db.query(OrderItem).filter(OrderItem.order_id == order_id).all():
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity

    order.status = "cancelled"
    db.commit()
    request.session["flash"] = f"Đã huỷ đơn hàng #{order_id}."
    return RedirectResponse(url=f"/don-hang/{order_id}", status_code=303)


# ── POST /don-hang/{id}/da-nhan — User xác nhận đã nhận hàng ────────────────
@router.post("/don-hang/{order_id}/da-nhan")
def order_confirm_received(order_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/dang-nhap", status_code=303)

    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
    if not order:
        return RedirectResponse(url="/don-hang", status_code=303)

    if order.status != "shipping":
        request.session["flash"] = "Chỉ có thể xác nhận khi đơn đang được giao."
        return RedirectResponse(url=f"/don-hang/{order_id}", status_code=303)

    order.status = "delivered"
    db.commit()
    request.session["flash"] = f"Cảm ơn bạn! Đơn hàng #{order_id} đã hoàn tất."
    return RedirectResponse(url=f"/don-hang/{order_id}", status_code=303)
