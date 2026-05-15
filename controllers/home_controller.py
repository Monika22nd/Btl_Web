from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import APP_NAME, ITEMS_PER_PAGE
from database import get_db
from models import Category, Brand, Product, CartItem

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


# ── GET / — Trang chủ ─────────────────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    ctx = _session_ctx(request, db)
    categories = db.query(Category).order_by(Category.display_order).all()
    featured_products = (
        db.query(Product)
        .filter(Product.is_featured == True, Product.stock > 0)
        .order_by(Product.rating.desc())
        .limit(8).all()
    )
    new_products = (
        db.query(Product)
        .filter(Product.stock > 0)
        .order_by(Product.created_at.desc())
        .limit(8).all()
    )
    brands = db.query(Brand).all()
    flash = request.session.pop("flash", None)

    return templates.TemplateResponse("home.html", {
        "request": request, **ctx,
        "categories": categories,
        "featured_products": featured_products,
        "deals": new_products,
        "brands": brands,
        "flash": flash,
    })


# ── GET /tim-kiem — Tìm kiếm ─────────────────────────────────────────────────
@router.get("/tim-kiem", response_class=HTMLResponse)
def search(
    request: Request,
    q: str = "",
    category_id: int = None,
    brand_id: int = None,
    min_price: int = None,
    max_price: int = None,
    sort: str = "newest",
    page: int = 1,
    db: Session = Depends(get_db),
):
    ctx = _session_ctx(request, db)
    query = db.query(Product)

    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if brand_id:
        query = query.filter(Product.brand_id == brand_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    sort_map = {
        "newest": Product.created_at.desc(),
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "rating": Product.rating.desc(),
    }
    query = query.order_by(sort_map.get(sort, Product.created_at.desc()))

    total = query.count()
    total_pages = max(1, -(-total // ITEMS_PER_PAGE))
    page = max(1, min(page, total_pages))
    products = query.offset((page - 1) * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()

    categories = db.query(Category).order_by(Category.display_order).all()
    brands = db.query(Brand).all()

    return templates.TemplateResponse("products.html", {
        "request": request, **ctx,
        "products": products,
        "categories": categories,
        "brands": brands,
        "q": q,
        "sort": sort,
        "page": page,
        "pages": total_pages,
        "total": total,
        "heading": f"Kết quả tìm kiếm: \"{q}\"" if q else "Tất cả sản phẩm",
    })


# ── GET /danh-muc/{slug} — Danh mục ──────────────────────────────────────────
@router.get("/danh-muc/{slug}", response_class=HTMLResponse)
def category_page(
    slug: str,
    request: Request,
    sort: str = "newest",
    page: int = 1,
    db: Session = Depends(get_db),
):
    ctx = _session_ctx(request, db)
    category = db.query(Category).filter(Category.slug == slug).first()
    if not category:
        return templates.TemplateResponse("404.html", {"request": request, **ctx}, status_code=404)

    query = db.query(Product).filter(Product.category_id == category.id)
    sort_map = {
        "newest": Product.created_at.desc(),
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "rating": Product.rating.desc(),
    }
    query = query.order_by(sort_map.get(sort, Product.created_at.desc()))

    total = query.count()
    total_pages = max(1, -(-total // ITEMS_PER_PAGE))
    page = max(1, min(page, total_pages))
    products = query.offset((page - 1) * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()
    categories = db.query(Category).order_by(Category.display_order).all()

    return templates.TemplateResponse("products.html", {
        "request": request, **ctx,
        "products": products,
        "categories": categories,
        "brands": db.query(Brand).all(),
        "sort": sort,
        "page": page,
        "pages": total_pages,
        "total": total,
        "heading": category.name,
    })
