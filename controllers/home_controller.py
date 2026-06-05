from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import APP_NAME, ITEMS_PER_PAGE
from database import get_db
from dao import cart_dao, product_dao
from controllers.catalog_helpers import get_filter_brands, get_nav_categories

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

    featured_products = product_dao.list_featured(db, limit=8)

    # Deals = sản phẩm THẬT SỰ đang giảm giá (original_price > price)
    deal_products = product_dao.list_deals(db, limit=8)

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
    brand_id  = _parse_int(brand_id)
    min_price = _parse_int(min_price)
    max_price = _parse_int(max_price)
    brand_slugs = [s for s in request.query_params.getlist("brand") if s]
    category_slugs = [s for s in request.query_params.getlist("category") if s]

    products, page, total_pages, total = product_dao.list_catalog(
        db,
        page=page,
        per_page=ITEMS_PER_PAGE,
        q=q,
        brand_id=brand_id,
        brand_slugs=brand_slugs,
        category_slugs=category_slugs,
        min_price=min_price,
        max_price=max_price,
        sale=sale,
        sort=sort,
    )

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
    category = product_dao.get_category_by_slug(db, slug)
    if not category:
        return templates.TemplateResponse("404.html", {"request": request, **ctx}, status_code=404)

    brand_slugs = [s for s in request.query_params.getlist("brand") if s]
    min_price = _parse_int(request.query_params.get("min_price"))
    max_price = _parse_int(request.query_params.get("max_price"))

    products, page, total_pages, total = product_dao.list_catalog(
        db,
        page=page,
        per_page=ITEMS_PER_PAGE,
        category_id=category.id,
        brand_slugs=brand_slugs,
        min_price=min_price,
        max_price=max_price,
        sale=sale,
        sort=sort,
    )

    return templates.TemplateResponse("products.html", {
        "request": request, **ctx,
        "products": products,
        "categories": get_nav_categories(db),
        "brands": get_filter_brands(db, [category.slug]),
        "current_category_slug": category.slug,
        "sort": sort, "page": page, "pages": total_pages, "total": total,
        "heading": category.name,
    })
