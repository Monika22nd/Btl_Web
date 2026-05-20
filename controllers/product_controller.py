from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import APP_NAME, ITEMS_PER_PAGE
from database import get_db
from models import Product, ProductSpec, Category, Brand, CartItem

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


def _parse_int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# ── GET /san-pham — Danh sách sản phẩm ───────────────────────────────────────
@router.get("/san-pham", response_class=HTMLResponse)
def product_list(
    request: Request,
    q: str = "",
    category_id: str = None,
    brand_id: str = None,
    min_price: str = None,
    max_price: str = None,
    sort: str = "newest",
    page: int = 1,
    db: Session = Depends(get_db),
):
    ctx = _session_ctx(request, db)
    query = db.query(Product)
    category_id = _parse_int(category_id)
    brand_id = _parse_int(brand_id)
    min_price = _parse_int(min_price)
    max_price = _parse_int(max_price)
    category_slugs = [slug for slug in request.query_params.getlist("category") if slug]
    brand_slugs = [slug for slug in request.query_params.getlist("brand") if slug]

    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    elif category_slugs:
        query = query.join(Category).filter(Category.slug.in_(category_slugs))
    if brand_id:
        query = query.filter(Product.brand_id == brand_id)
    elif brand_slugs:
        query = query.join(Brand).filter(Brand.slug.in_(brand_slugs))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    sort_map = {
        "newest": Product.created_at.desc(),
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "rating": Product.rating.desc(),
        "popular": Product.review_count.desc(),
    }
    query = query.order_by(sort_map.get(sort, Product.created_at.desc()))

    total = query.count()
    total_pages = max(1, -(-total // ITEMS_PER_PAGE))
    page = max(1, min(page, total_pages))
    products = query.offset((page - 1) * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()

    return templates.TemplateResponse("products.html", {
        "request": request, **ctx,
        "products": products,
        "categories": db.query(Category).order_by(Category.display_order).all(),
        "brands": db.query(Brand).all(),
        "q": q,
        "sort": sort,
        "page": page,
        "pages": total_pages,
        "total": total,
        "heading": "Tất cả sản phẩm",
    })


# ── GET /san-pham/{slug} — Chi tiết sản phẩm ─────────────────────────────────
@router.get("/san-pham/{slug}", response_class=HTMLResponse)
def product_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    ctx = _session_ctx(request, db)
    product = db.query(Product).filter(Product.slug == slug).first()
    if not product:
        return templates.TemplateResponse("404.html", {"request": request, **ctx}, status_code=404)

    specs = db.query(ProductSpec).filter(ProductSpec.product_id == product.id).all()
    related = (
        db.query(Product)
        .filter(Product.category_id == product.category_id, Product.id != product.id, Product.stock > 0)
        .order_by(Product.rating.desc())
        .limit(4).all()
    )

    # Gán specs vào product để template dùng product.specs
    product.specs = specs

    flash = request.session.pop("flash", None)
    return templates.TemplateResponse("product_detail.html", {
        "request": request, **ctx,
        "product": product,
        "related_products": related,
        "flash": flash,
    })
