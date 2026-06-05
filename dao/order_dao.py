from sqlalchemy.orm import Session

from models import CartItem, Order, OrderItem


def list_by_user(db: Session, user_id: int):
    return (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )


def get_by_id(db: Session, order_id: int):
    return db.query(Order).filter(Order.id == order_id).first()


def get_by_user(db: Session, order_id: int, user_id: int):
    return (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == user_id)
        .first()
    )


def list_items(db: Session, order_id: int):
    return db.query(OrderItem).filter(OrderItem.order_id == order_id).all()


def create_from_cart(
    db: Session,
    user_id: int,
    cart_items,
    recipient_name: str,
    shipping_address: str,
    phone: str,
    note: str = "",
):
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
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price,
            )
        )
        item.product.stock -= item.quantity

    db.query(CartItem).filter(CartItem.user_id == user_id).delete()
    db.commit()
    db.refresh(order)
    return order


def cancel_order(db: Session, order: Order) -> None:
    for item in list_items(db, order.id):
        if item.product:
            item.product.stock += item.quantity
    order.status = "cancelled"
    db.commit()


def update_status(db: Session, order: Order, status: str) -> None:
    order.status = status
    db.commit()


def add_complaint(db: Session, order: Order, reason: str, description: str) -> None:
    order.status = "complaint"
    order.note = ((order.note or "") + f"\nKhiếu nại: {reason} - {description}").strip()
    db.commit()
