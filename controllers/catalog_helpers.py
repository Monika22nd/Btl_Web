from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Brand, Category, Product


BRAND_FILTER_LIMIT = 5


def get_nav_categories(db: Session):
    return db.query(Category).order_by(Category.display_order, Category.name).all()


def get_filter_brands(db: Session, category_slugs=None, limit=BRAND_FILTER_LIMIT):
    query = (
        db.query(Brand)
        .join(Product, Product.brand_id == Brand.id)
        .group_by(Brand.id)
        .order_by(func.count(Product.id).desc(), Brand.name.asc())
    )

    if category_slugs:
        query = query.join(Category, Product.category_id == Category.id)
        query = query.filter(Category.slug.in_(category_slugs))

    return query.limit(limit).all()
