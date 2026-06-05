from sqlalchemy.orm import Session

from models import Brand, Category, Product, ProductSpec


def get_by_id(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()


def get_by_slug(db: Session, slug: str):
    return db.query(Product).filter(Product.slug == slug).first()


def get_category_by_slug(db: Session, slug: str):
    return db.query(Category).filter(Category.slug == slug).first()


def list_specs(db: Session, product_id: int):
    return db.query(ProductSpec).filter(ProductSpec.product_id == product_id).all()


def list_related(db: Session, product: Product, limit: int = 4):
    return (
        db.query(Product)
        .filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.stock > 0,
        )
        .order_by(Product.rating.desc())
        .limit(limit)
        .all()
    )


def list_featured(db: Session, limit: int = 8):
    return (
        db.query(Product)
        .filter(Product.is_featured == True, Product.stock > 0)
        .order_by(Product.rating.desc())
        .limit(limit)
        .all()
    )


def list_deals(db: Session, limit: int = 8):
    return (
        db.query(Product)
        .filter(
            Product.stock > 0,
            Product.original_price != None,
            Product.original_price > Product.price,
        )
        .order_by(((Product.original_price - Product.price) / Product.original_price).desc())
        .limit(limit)
        .all()
    )


def build_catalog_query(
    db: Session,
    q: str = "",
    brand_id: int = None,
    brand_slugs=None,
    category_slugs=None,
    category_id: int = None,
    min_price: int = None,
    max_price: int = None,
    sale: str = "",
    sort: str = "newest",
):
    query = db.query(Product)

    if category_id:
        query = query.filter(Product.category_id == category_id)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if category_slugs:
        query = query.join(Category).filter(Category.slug.in_(category_slugs))
    if brand_id:
        query = query.filter(Product.brand_id == brand_id)
    elif brand_slugs:
        query = query.join(Brand).filter(Brand.slug.in_(brand_slugs))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if sale == "1":
        query = query.filter(
            Product.original_price != None,
            Product.original_price > Product.price,
        )

    sort_map = {
        "newest": Product.created_at.desc(),
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "rating": Product.rating.desc(),
        "popular": Product.review_count.desc(),
    }
    return query.order_by(sort_map.get(sort, Product.created_at.desc()))


def paginate(query, page: int, per_page: int):
    total = query.count()
    total_pages = max(1, -(-total // per_page))
    page = max(1, min(page, total_pages))
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, page, total_pages, total


def list_catalog(
    db: Session,
    page: int,
    per_page: int,
    q: str = "",
    brand_id: int = None,
    brand_slugs=None,
    category_slugs=None,
    category_id: int = None,
    min_price: int = None,
    max_price: int = None,
    sale: str = "",
    sort: str = "newest",
):
    query = build_catalog_query(
        db,
        q=q,
        brand_id=brand_id,
        brand_slugs=brand_slugs,
        category_slugs=category_slugs,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        sale=sale,
        sort=sort,
    )
    return paginate(query, page, per_page)


def update_rating(db: Session, product: Product, rating: int) -> None:
    rating = max(1, min(5, rating))
    total_score = product.rating * product.review_count + rating
    product.review_count += 1
    product.rating = round(total_score / product.review_count, 1)
    db.commit()
