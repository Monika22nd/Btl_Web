from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import APP_NAME, ITEMS_PER_PAGE
from database import get_db
from models import Category, Brand, Product, CartItem
from controllers.catalog_helpers import get_filter_brands, get_nav_categories

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
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


# ── GET / ─────────────────────────────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    ctx = _session_ctx(request, db)
    categories = get_nav_categories(db)

    featured_products = (
        db.query(Product)
        .filter(Product.is_featured == True, Product.stock > 0)
        .order_by(Product.rating.desc())
        .limit(8).all()
    )

    # Deals = sản phẩm THẬT SỰ đang giảm giá (original_price > price)
    deal_products = (
        db.query(Product)
        .filter(
            Product.stock > 0,
            Product.original_price != None,
            Product.original_price > Product.price,
        )
        .order_by(
            ((Product.original_price - Product.price) / Product.original_price).desc()
        )
        .limit(8).all()
    )

    brands = get_filter_brands(db)
    flash = request.session.pop("flash", None)

    return templates.TemplateResponse("home.html", {
        "request": request, **ctx,
        "categories": categories,
        "featured_products": featured_products,
        "deals": deal_products,
        "brands": brands,
        "flash": flash,
    })


# ── GET /tim-kiem ─────────────────────────────────────────────────────────────
@router.get("/tim-kiem", response_class=HTMLResponse)
def search(
    request: Request,
    q: str = "",
    brand_id: str = None,
    min_price: str = None,
    max_price: str = None,
    sort: str = "newest",
    sale: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
):
    ctx = _session_ctx(request, db)
    query = db.query(Product)

    brand_id  = _parse_int(brand_id)
    min_price = _parse_int(min_price)
    max_price = _parse_int(max_price)
    brand_slugs = [s for s in request.query_params.getlist("brand") if s]
    category_slugs = [s for s in request.query_params.getlist("category") if s]

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
            Product.original_price > Product.price
        )

    sort_map = {
        "newest":     Product.created_at.desc(),
        "price_asc":  Product.price.asc(),
        "price_desc": Product.price.desc(),
        "rating":     Product.rating.desc(),
    }
    query = query.order_by(sort_map.get(sort, Product.created_at.desc()))

    total = query.count()
    total_pages = max(1, -(-total // ITEMS_PER_PAGE))
    page = max(1, min(page, total_pages))
    products = query.offset((page - 1) * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()

    return templates.TemplateResponse("products.html", {
        "request": request, **ctx,
        "products": products,
        "categories": get_nav_categories(db),
        "brands": get_filter_brands(db, category_slugs),
        "current_category_slug": category_slugs[0] if category_slugs else "",
        "q": q, "sort": sort,
        "page": page, "pages": total_pages, "total": total,
        "heading": f'Kết quả: "{q}"' if q else "Tất cả sản phẩm",
    })


# ── GET /danh-muc/{slug} ──────────────────────────────────────────────────────
@router.get("/danh-muc/{slug}", response_class=HTMLResponse)
def category_page(
    slug: str, request: Request,
    sort: str = "newest", sale: str = "", page: int = 1,
    db: Session = Depends(get_db),
):
    ctx = _session_ctx(request, db)
    category = db.query(Category).filter(Category.slug == slug).first()
    if not category:
        return templates.TemplateResponse("404.html", {"request": request, **ctx}, status_code=404)

    query = db.query(Product).filter(Product.category_id == category.id)

    brand_slugs = [s for s in request.query_params.getlist("brand") if s]
    min_price = _parse_int(request.query_params.get("min_price"))
    max_price = _parse_int(request.query_params.get("max_price"))

    if brand_slugs:
        query = query.join(Brand).filter(Brand.slug.in_(brand_slugs))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if sale == "1":
        query = query.filter(
            Product.original_price != None,
            Product.original_price > Product.price
        )

    sort_map = {
        "newest":     Product.created_at.desc(),
        "price_asc":  Product.price.asc(),
        "price_desc": Product.price.desc(),
        "rating":     Product.rating.desc(),
    }
    query = query.order_by(sort_map.get(sort, Product.created_at.desc()))

    total = query.count()
    total_pages = max(1, -(-total // ITEMS_PER_PAGE))
    page = max(1, min(page, total_pages))
    products = query.offset((page - 1) * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()

    return templates.TemplateResponse("products.html", {
        "request": request, **ctx,
        "products": products,
        "categories": get_nav_categories(db),
        "brands": get_filter_brands(db, [category.slug]),
        "current_category_slug": category.slug,
        "sort": sort, "page": page, "pages": total_pages, "total": total,
        "heading": category.name,
    })
