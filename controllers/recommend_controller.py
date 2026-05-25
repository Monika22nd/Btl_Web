"""
controllers/recommend_controller.py
API endpoints cho hệ thống gợi ý sản phẩm.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from recommender import (
    content_based,
    collab_filter,
    popular_products,
    trending_products,
    personalised,
    hybrid_recommend,
    chat_recommend,
)

router = APIRouter(prefix="/api/recommend")


def _product_dict(p) -> dict:
    """Chuyển Product object sang dict JSON-safe."""
    discount = 0
    if p.original_price and p.original_price > p.price:
        discount = round((1 - p.price / p.original_price) * 100)
    return {
        "id":             p.id,
        "name":           p.name,
        "slug":           p.slug,
        "price":          p.price,
        "original_price": p.original_price,
        "discount":       discount,
        "image_url":      p.image_url or "",
        "rating":         float(p.rating or 0),
        "review_count":   int(p.review_count or 0),
        "stock":          p.stock,
        "brand":          p.brand.name if p.brand else "",
        "category":       p.category.name if p.category else "",
        "category_slug":  p.category.slug if p.category else "",
        "url":            f"/san-pham/{p.slug}",
        "formatted_price": f"{p.price:,}đ".replace(",", "."),
        "formatted_original": f"{p.original_price:,}đ".replace(",", ".") if p.original_price else None,
    }


# ── GET /api/recommend/trending ───────────────────────────────────────────────
@router.get("/trending")
def api_trending(limit: int = 8, db: Session = Depends(get_db)):
    products = trending_products(db, limit=limit)
    return {"products": [_product_dict(p) for p in products]}


# ── GET /api/recommend/popular ────────────────────────────────────────────────
@router.get("/popular")
def api_popular(
    category: str = "",
    limit: int = 8,
    db: Session = Depends(get_db),
):
    products = popular_products(db, category_slug=category or None, limit=limit)
    return {"products": [_product_dict(p) for p in products]}


# ── GET /api/recommend/similar/{product_id} ───────────────────────────────────
@router.get("/similar/{product_id}")
def api_similar(product_id: int, limit: int = 6, db: Session = Depends(get_db)):
    cb = content_based(db, product_id, limit=limit)
    cf = collab_filter(db, product_id, limit=limit)
    # Gộp, ưu tiên collab nếu có
    seen = set()
    merged = []
    for p in (cf + cb):
        if p.id not in seen:
            seen.add(p.id)
            merged.append(p)
    return {"products": [_product_dict(p) for p in merged[:limit]]}


# ── GET /api/recommend/personalised/{user_id} ─────────────────────────────────
@router.get("/personalised/{user_id}")
def api_personalised(user_id: int, limit: int = 8, db: Session = Depends(get_db)):
    products = personalised(db, user_id=user_id, limit=limit)
    return {"products": [_product_dict(p) for p in products]}


# ── GET /api/recommend/hybrid ─────────────────────────────────────────────────
@router.get("/hybrid")
def api_hybrid(
    product_id: int = None,
    user_id: int = None,
    category: str = "",
    limit: int = 8,
    db: Session = Depends(get_db),
):
    products = hybrid_recommend(
        db,
        product_id=product_id,
        user_id=user_id,
        category_slug=category or None,
        limit=limit,
    )
    return {"products": [_product_dict(p) for p in products]}


# ── POST /api/recommend/chat ──────────────────────────────────────────────────
@router.post("/chat")
async def api_chat(request: Request, db: Session = Depends(get_db)):
    """
    Body JSON: { "message": "...", "user_id": null }
    Trả về: { "reply": "...", "products": [...], "action_url": "..." }
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    message = str(body.get("message", "")).strip()
    user_id = body.get("user_id")

    if not message:
        return JSONResponse({"error": "Empty message"}, status_code=400)

    result = chat_recommend(db, user_message=message, user_id=user_id, limit=5)
    return {
        "reply":      result["reply"],
        "products":   [_product_dict(p) for p in result["products"]],
        "action_url": result["action_url"],
    }
