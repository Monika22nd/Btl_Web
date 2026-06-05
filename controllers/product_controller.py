from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
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


# ── GET /san-pham ─────────────────────────────────────────────────────────────
@router.get("/san-pham", response_class=HTMLResponse)
def product_list(
    request: Request,
    q: str = "",
    brand_id: str = None,
    min_price: str = None,
    max_price: str = None,
    sort: str = "newest",
    sale: str = "",          # "1" = chỉ sản phẩm giảm giá
    page: int = 1,
    db: Session = Depends(get_db),
):
    ctx = _session_ctx(request, db)
    brand_id  = _parse_int(brand_id)
    min_price = _parse_int(min_price)
    max_price = _parse_int(max_price)
    brand_slugs = [s for s in request.query_params.getlist("brand") if s]

    products, page, total_pages, total = product_dao.list_catalog(
        db,
        page=page,
        per_page=ITEMS_PER_PAGE,
        q=q,
        brand_id=brand_id,
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
        "brands": get_filter_brands(db),
        "current_category_slug": "",
        "q": q, "sort": sort,
        "page": page, "pages": total_pages, "total": total,
        "heading": "🔥 Đang giảm giá" if sale == "1" else "Tất cả sản phẩm",
    })


# ── GET /san-pham/{slug} ──────────────────────────────────────────────────────
@router.get("/san-pham/{slug}", response_class=HTMLResponse)
def product_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    ctx = _session_ctx(request, db)
    product = product_dao.get_by_slug(db, slug)
    if not product:
        return templates.TemplateResponse("404.html", {"request": request, **ctx}, status_code=404)

    specs = product_dao.list_specs(db, product.id)
    related = product_dao.list_related(db, product, limit=4)
    product.specs = specs

    flash = request.session.pop("flash", None)
    return templates.TemplateResponse("product_detail.html", {
        "request": request, **ctx,
        "product": product,
        "related_products": related,
        "flash": flash,
    })


# ── POST /san-pham/{slug}/danh-gia — Gửi đánh giá ───────────────────────────
@router.post("/san-pham/{slug}/danh-gia")
def product_review(
    slug: str,
    request: Request,
    rating: int = Form(...),
    comment: str = Form(default=""),
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url=f"/dang-nhap?next=/san-pham/{slug}", status_code=303)

    product = product_dao.get_by_slug(db, slug)
    if not product:
        return RedirectResponse(url="/san-pham", status_code=303)

    product_dao.update_rating(db, product, rating)

    # Cập nhật rating trung bình

    request.session["flash"] = "Cảm ơn bạn đã đánh giá sản phẩm!"
    return RedirectResponse(url=f"/san-pham/{slug}", status_code=303)
