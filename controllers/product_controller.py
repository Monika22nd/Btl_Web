from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import APP_NAME, ITEMS_PER_PAGE
from database import get_db
from models import Product, ProductSpec, Category, Brand, CartItem
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
    query = db.query(Product)

    brand_id  = _parse_int(brand_id)
    min_price = _parse_int(min_price)
    max_price = _parse_int(max_price)
    brand_slugs = [s for s in request.query_params.getlist("brand") if s]

    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
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
        "popular":    Product.review_count.desc(),
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
    product = db.query(Product).filter(Product.slug == slug).first()
    if not product:
        return templates.TemplateResponse("404.html", {"request": request, **ctx}, status_code=404)

    specs = db.query(ProductSpec).filter(ProductSpec.product_id == product.id).all()
    related = (
        db.query(Product)
        .filter(Product.category_id == product.category_id,
                Product.id != product.id, Product.stock > 0)
        .order_by(Product.rating.desc())
        .limit(4).all()
    )
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

    product = db.query(Product).filter(Product.slug == slug).first()
    if not product:
        return RedirectResponse(url="/san-pham", status_code=303)

    rating = max(1, min(5, rating))

    # Cập nhật rating trung bình
    total_score = product.rating * product.review_count + rating
    product.review_count += 1
    product.rating = round(total_score / product.review_count, 1)
    db.commit()

    request.session["flash"] = "Cảm ơn bạn đã đánh giá sản phẩm!"
    return RedirectResponse(url=f"/san-pham/{slug}", status_code=303)
