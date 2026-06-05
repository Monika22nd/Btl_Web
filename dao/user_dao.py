from sqlalchemy.orm import Session

from models import User


def normalize_email(email: str) -> str:
    return email.lower().strip()


def get_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == normalize_email(email)).first()


def create_user(
    db: Session,
    full_name: str,
    email: str,
    password: str,
    phone: str = "",
):
    user = User(
        full_name=full_name.strip(),
        email=normalize_email(email),
        phone=phone.strip() or None,
    )
    user.set_password(password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_profile(
    db: Session,
    user: User,
    full_name: str,
    phone: str = "",
    address: str = "",
) -> None:
    user.full_name = full_name.strip()
    user.phone = phone.strip() or None
    user.address = address.strip() or None
    db.commit()
