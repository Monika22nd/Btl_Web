from sqlalchemy.orm import Session

from models import CartItem


def count_by_user(db: Session, user_id: int) -> int:
    return db.query(CartItem).filter(CartItem.user_id == user_id).count()


def list_by_user(db: Session, user_id: int):
    return db.query(CartItem).filter(CartItem.user_id == user_id).all()


def get_item(db: Session, item_id: int, user_id: int):
    return (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.user_id == user_id)
        .first()
    )


def get_by_user_and_product(db: Session, user_id: int, product_id: int):
    return (
        db.query(CartItem)
        .filter(CartItem.user_id == user_id, CartItem.product_id == product_id)
        .first()
    )


def add_or_update_item(db: Session, user_id: int, product, quantity: int):
    quantity = max(1, quantity)
    existing = get_by_user_and_product(db, user_id, product.id)

    if existing:
        existing.quantity = min(existing.quantity + quantity, product.stock)
    else:
        existing = CartItem(
            user_id=user_id,
            product_id=product.id,
            quantity=min(quantity, product.stock),
        )
        db.add(existing)

    db.commit()
    return existing


def update_quantity(db: Session, item: CartItem, quantity: int) -> None:
    item.quantity = min(quantity, item.product.stock)
    db.commit()


def remove_item(db: Session, item: CartItem) -> None:
    db.delete(item)
    db.commit()


def clear_by_user(db: Session, user_id: int) -> None:
    db.query(CartItem).filter(CartItem.user_id == user_id).delete()
    db.commit()


def total(cart_items) -> int:
    return sum(item.product.price * item.quantity for item in cart_items)
