"""
recommender.py — TechWorld Recommendation Engine
Thuật toán gợi ý sản phẩm hoàn toàn không cần AI API.

Các chiến lược:
  1. content_based   — cùng danh mục/thương hiệu, khoảng giá tương tự
  2. collab_filter   — "khách mua X cũng mua Y" từ lịch sử OrderItem
  3. popularity      — điểm nổi bật = rating × log(review_count+1) × stock_factor
  4. trending        — đơn hàng nhiều nhất trong 30 ngày gần nhất
  5. chat_suggest    — rule-based NLP tiếng Việt → gợi ý theo intent
"""

from __future__ import annotations
import math
import re
import unicodedata
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

# ── Lazy import để tránh circular ────────────────────────────────────────────
def _models():
    from models import Product, Category, Brand, Order, OrderItem
    return Product, Category, Brand, Order, OrderItem


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CONTENT-BASED FILTERING
# ═══════════════════════════════════════════════════════════════════════════════

def content_based(
    db: Session,
    product_id: int,
    limit: int = 8,
) -> List:
    """
    Trả về sản phẩm tương tự dựa trên:
      - Cùng danh mục (+3 điểm)
      - Cùng thương hiệu (+2 điểm)
      - Giá chênh lệch ≤ 30% so với sản phẩm gốc (+1 điểm)
    """
    Product, *_ = _models()

    source = db.query(Product).filter(Product.id == product_id).first()
    if not source:
        return []

    candidates = (
        db.query(Product)
        .filter(Product.id != product_id, Product.stock > 0)
        .all()
    )

    scored = []
    price_low  = source.price * 0.7
    price_high = source.price * 1.3

    for p in candidates:
        score = 0.0
        if p.category_id == source.category_id:
            score += 3
        if p.brand_id == source.brand_id:
            score += 2
        if price_low <= p.price <= price_high:
            score += 1
        # Thêm điểm phổ biến
        score += _popularity_score(p) * 0.3
        if score > 0:
            scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:limit]]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. COLLABORATIVE FILTERING (Item-Item)
# ═══════════════════════════════════════════════════════════════════════════════

def collab_filter(
    db: Session,
    product_id: int,
    limit: int = 8,
) -> List:
    """
    "Khách mua sản phẩm này cũng mua..." — item-item collaborative filtering.
    Tìm các đơn hàng chứa product_id, lấy các sản phẩm khác trong cùng đơn,
    đếm tần suất xuất hiện cùng nhau.
    """
    Product, _, __, Order, OrderItem = _models()

    # Lấy tất cả order chứa product_id
    order_ids = (
        db.query(OrderItem.order_id)
        .filter(OrderItem.product_id == product_id)
        .subquery()
    )

    # Lấy các sản phẩm khác trong cùng đơn
    co_purchased = (
        db.query(OrderItem.product_id, func.count(OrderItem.product_id).label("cnt"))
        .filter(
            OrderItem.order_id.in_(order_ids),
            OrderItem.product_id != product_id,
        )
        .group_by(OrderItem.product_id)
        .order_by(func.count(OrderItem.product_id).desc())
        .limit(limit * 2)
        .all()
    )

    if not co_purchased:
        return []

    pid_map = {row.product_id: row.cnt for row in co_purchased}
    products = (
        db.query(Product)
        .filter(Product.id.in_(pid_map.keys()), Product.stock > 0)
        .all()
    )
    products.sort(key=lambda p: pid_map.get(p.id, 0), reverse=True)
    return products[:limit]


# ═══════════════════════════════════════════════════════════════════════════════
# 3. POPULARITY SCORING
# ═══════════════════════════════════════════════════════════════════════════════

def _popularity_score(product) -> float:
    """Điểm nổi bật = rating × log(review_count+1) × stock_bonus."""
    rating       = float(product.rating or 0)
    review_count = int(product.review_count or 0)
    stock_bonus  = 1.0 if product.stock > 0 else 0.0
    return rating * math.log1p(review_count) * stock_bonus


def popular_products(
    db: Session,
    category_slug: Optional[str] = None,
    limit: int = 8,
) -> List:
    """Gợi ý dựa trên điểm phổ biến, có thể lọc theo danh mục."""
    Product, Category, *_ = _models()

    query = db.query(Product).filter(Product.stock > 0)
    if category_slug:
        query = query.join(Category).filter(Category.slug == category_slug)

    products = query.all()
    products.sort(key=_popularity_score, reverse=True)
    return products[:limit]


# ═══════════════════════════════════════════════════════════════════════════════
# 4. TRENDING (đơn hàng nhiều nhất 30 ngày)
# ═══════════════════════════════════════════════════════════════════════════════

def trending_products(db: Session, limit: int = 8) -> List:
    """Sản phẩm được đặt nhiều nhất trong 30 ngày gần nhất."""
    Product, _, __, Order, OrderItem = _models()

    since = datetime.utcnow() - timedelta(days=30)

    rows = (
        db.query(OrderItem.product_id, func.sum(OrderItem.quantity).label("sold"))
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.created_at >= since)
        .group_by(OrderItem.product_id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit * 2)
        .all()
    )

    if not rows:
        return popular_products(db, limit=limit)

    pid_map = {r.product_id: r.sold for r in rows}
    products = (
        db.query(Product)
        .filter(Product.id.in_(pid_map.keys()), Product.stock > 0)
        .all()
    )
    products.sort(key=lambda p: pid_map.get(p.id, 0), reverse=True)
    return products[:limit]


# ═══════════════════════════════════════════════════════════════════════════════
# 5. PERSONALISED (dựa trên lịch sử mua của user)
# ═══════════════════════════════════════════════════════════════════════════════

def personalised(db: Session, user_id: int, limit: int = 8) -> List:
    """
    Gợi ý cá nhân hoá:
      - Lấy danh sách sản phẩm đã mua của user → lấy danh mục / thương hiệu yêu thích
      - Tính điểm cho các sản phẩm chưa mua trong danh mục đó
    """
    Product, Category, Brand, Order, OrderItem = _models()

    # Sản phẩm đã mua
    bought_ids = set(
        row.product_id
        for row in (
            db.query(OrderItem.product_id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.user_id == user_id)
            .all()
        )
    )

    if not bought_ids:
        return trending_products(db, limit=limit)

    # Đếm danh mục / thương hiệu yêu thích
    bought_products = db.query(Product).filter(Product.id.in_(bought_ids)).all()
    cat_count: dict[int, int] = {}
    brand_count: dict[int, int] = {}
    for p in bought_products:
        cat_count[p.category_id]   = cat_count.get(p.category_id, 0) + 1
        brand_count[p.brand_id]     = brand_count.get(p.brand_id, 0) + 1

    # Gợi ý từ các sản phẩm chưa mua
    candidates = (
        db.query(Product)
        .filter(Product.id.notin_(bought_ids), Product.stock > 0)
        .all()
    )

    scored = []
    max_cat   = max(cat_count.values(), default=1)
    max_brand = max(brand_count.values(), default=1)

    for p in candidates:
        score = 0.0
        score += (cat_count.get(p.category_id, 0) / max_cat) * 4
        score += (brand_count.get(p.brand_id, 0) / max_brand) * 2
        score += _popularity_score(p) * 0.5
        scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:limit]]


# ═══════════════════════════════════════════════════════════════════════════════
# 6. RULE-BASED CHAT NLP (Tiếng Việt)
# ═══════════════════════════════════════════════════════════════════════════════

# Từ điển intent → từ khóa nhận diện
_INTENTS = {
    "greeting": [
        r"xin chào", r"chào", r"hello", r"hi\b", r"alo",
    ],
    "phone": [
        r"điện thoại", r"dien thoai", r"smartphone", r"iphone", r"samsung.*galaxy",
        r"xiaomi", r"oppo", r"điện thoại rẻ", r"điện thoại tốt",
    ],
    "laptop": [
        r"laptop", r"máy tính xách tay", r"macbook", r"máy tính",
        r"notebook", r"dell", r"asus.*laptop", r"lenovo",
    ],
    "tablet": [
        r"tablet", r"máy tính bảng", r"ipad", r"tab\b",
    ],
    "headphone": [
        r"tai nghe", r"loa", r"airpods", r"headphone", r"earphone",
        r"wh-1000", r"buds",
    ],
    "tv": [
        r"tivi", r"tv\b", r"television", r"màn hình lớn",
    ],
    "accessory": [
        r"phụ kiện", r"ốp lưng", r"sạc", r"cáp", r"chuột", r"bàn phím",
        r"tai nghe.*dây",
    ],
    "cheap": [
        r"rẻ", r"giá rẻ", r"tiết kiệm", r"bình dân", r"dưới \d",
        r"không quá \d", r"budget", r"tầm giá thấp",
    ],
    "premium": [
        r"xịn", r"cao cấp", r"flagship", r"pro\b", r"max\b",
        r"tốt nhất", r"đỉnh", r"premium",
    ],
    "discount": [
        r"giảm giá", r"sale", r"khuyến mãi", r"ưu đãi", r"deal",
        r"giá tốt", r"flash sale",
    ],
    "trending": [
        r"hot", r"xu hướng", r"bán chạy", r"phổ biến", r"nhiều người mua",
        r"trending", r"nổi bật",
    ],
    "recommend": [
        r"gợi ý", r"tư vấn", r"nên mua", r"mua gì", r"chọn gì",
        r"recommend", r"suggest", r"giới thiệu", r"cho tôi xem",
    ],
    "brand_apple": [r"apple", r"iphone", r"macbook", r"ipad", r"airpods"],
    "brand_samsung": [r"samsung", r"galaxy"],
    "brand_xiaomi": [r"xiaomi", r"mi\b", r"redmi"],
    "brand_sony": [r"sony"],
    "farewell": [
        r"cảm ơn", r"thank", r"bye", r"tạm biệt", r"ok rồi", r"được rồi",
    ],
}

# Ánh xạ intent → category slug
_INTENT_TO_CATEGORY = {
    "phone":     "dien-thoai",
    "laptop":    "laptop",
    "tablet":    "tablet",
    "headphone": "tai-nghe",
    "tv":        "tv",
    "accessory": "phu-kien-dt",
}

# Ánh xạ intent brand → brand slug
_INTENT_TO_BRAND = {
    "brand_apple":   "apple",
    "brand_samsung": "samsung",
    "brand_xiaomi":  "xiaomi",
    "brand_sony":    "sony",
}

def _detect_intents(text: str) -> set:
    """Nhận diện intent từ văn bản người dùng."""
    text = text.lower().strip()
    # Bỏ dấu đơn giản để tăng recall
    no_accent = _remove_accent(text)
    found = set()
    for intent, patterns in _INTENTS.items():
        for pat in patterns:
            if re.search(pat, text) or re.search(pat, no_accent):
                found.add(intent)
                break
    return found


def _remove_accent(s: str) -> str:
    """Bỏ dấu tiếng Việt đơn giản."""
    normalized = unicodedata.normalize("NFD", s)
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return without_marks.replace("đ", "d").replace("Đ", "D")


def _parse_price_value(raw_value: str, raw_unit: str = "") -> Optional[int]:
    """Chuyển '500k', '1.5 triệu', '2 tỷ', '12000000' sang VND."""
    value_text = (raw_value or "").strip().lower().replace(",", ".")
    unit = _remove_accent(raw_unit or "").strip().lower()
    if not value_text:
        return None

    compact_number = re.fullmatch(r"\d{1,3}(?:\.\d{3})+", value_text)
    if compact_number:
        number = float(value_text.replace(".", ""))
    else:
        try:
            number = float(value_text)
        except ValueError:
            digits = re.sub(r"\D", "", value_text)
            if not digits:
                return None
            number = float(digits)

    if unit in {"k", "nghin", "ngan"}:
        return int(number * 1_000)
    if unit in {"tr", "trieu", "m"}:
        return int(number * 1_000_000)
    if unit in {"ty", "ti"}:
        return int(number * 1_000_000_000)

    # Không có đơn vị: số lớn được hiểu là VND, số nhỏ thường là triệu.
    if number >= 100_000:
        return int(number)
    if number >= 1:
        return int(number * 1_000_000)
    return None


def _format_price_vnd(amount: int) -> str:
    """Hiển thị giá gọn cho câu trả lời chatbot."""
    def compact(value: float) -> str:
        text = f"{value:.1f}".rstrip("0").rstrip(".")
        return text.replace(".", ",")

    if amount >= 1_000_000_000 and amount % 1_000_000_000 == 0:
        return f"{amount // 1_000_000_000} tỷ"
    if amount >= 1_000_000_000:
        return f"{compact(amount / 1_000_000_000)} tỷ"
    if amount >= 1_000_000 and amount % 1_000_000 == 0:
        return f"{amount // 1_000_000} triệu"
    if amount >= 1_000_000:
        return f"{compact(amount / 1_000_000)} triệu"
    if amount >= 1_000 and amount % 1_000 == 0 and amount < 1_000_000:
        return f"{amount // 1_000} nghìn"
    return f"{amount:,}đ".replace(",", ".")


def _extract_price_range(text: str):
    """Trích xuất khoảng giá: dưới/trên/tầm, k/nghìn/triệu/tỷ hoặc số VND đầy đủ."""
    text = text.lower()
    plain_text = _remove_accent(text)
    searchable = (text, plain_text)
    number = r"(\d+(?:[\.,]\d+)*)"
    unit = r"(k|nghìn|nghin|ngàn|ngan|triệu|trieu|tr|m\b|tỷ|ty|tỉ|ti|đ|d|vnd)?"

    def parse(value, unit_value=""):
        return _parse_price_value(value, unit_value)

    # X đến Y đơn vị, X-Y đơn vị, hoặc từ X đến Y đơn vị.
    range_pattern = number + r"\s*(?:" + unit + r")?\s*(?:-|–|đến|den|tới|toi)\s*" + number + r"\s*" + unit
    for value in searchable:
        m = re.search(range_pattern, value)
        if m:
            shared_unit = m.group(4) or m.group(2) or ""
            low = parse(m.group(1), m.group(2) or shared_unit)
            high = parse(m.group(3), shared_unit)
            if low is not None and high is not None:
                return min(low, high), max(low, high)

    under = r"(dưới|duoi|không quá|khong qua|<=|=<|tối đa|toi da)\s*" + number + r"\s*" + unit
    for value in searchable:
        m = re.search(under, value)
        if m:
            high = parse(m.group(2), m.group(3) or "")
            if high is not None:
                return None, high

    over = r"(trên|tren|từ|tu|hơn|hon|>=|=>|ít nhất|it nhat|tối thiểu|toi thieu)\s*" + number + r"\s*" + unit
    for value in searchable:
        m = re.search(over, value)
        if m:
            low = parse(m.group(2), m.group(3) or "")
            if low is not None:
                return low, None

    around = r"(tầm|tam|khoảng|khoang)\s*" + number + r"\s*" + unit
    for value in searchable:
        m = re.search(around, value)
        if m:
            val = parse(m.group(2), m.group(3) or "")
            if val is not None:
                return int(val * 0.8), int(val * 1.2)

    return None, None


def chat_recommend(
    db: Session,
    user_message: str,
    user_id: Optional[int] = None,
    limit: int = 5,
) -> dict:
    """
    Xử lý tin nhắn người dùng → trả về dict:
      {
        "reply": str,            # Câu trả lời văn bản
        "products": [...],       # Danh sách sản phẩm gợi ý
        "action_url": str|None,  # Link xem thêm
      }
    """
    Product, Category, Brand, Order, OrderItem = _models()

    intents = _detect_intents(user_message)
    min_price, max_price = _extract_price_range(user_message)
    products = []
    reply = ""
    action_url = None

    # ── Chào hỏi ──────────────────────────────────────────────────────────────
    if "greeting" in intents and not (intents - {"greeting"}):
        reply = ("Xin chào! Tôi là trợ lý mua sắm TechWorld 🛍️\n"
                 "Tôi có thể giúp bạn tìm điện thoại, laptop, tai nghe, TV và nhiều hơn nữa!\n"
                 "Bạn đang tìm sản phẩm gì hôm nay?")
        products = trending_products(db, limit=4)
        action_url = "/san-pham"
        return {"reply": reply, "products": products, "action_url": action_url}

    # ── Tạm biệt ──────────────────────────────────────────────────────────────
    if "farewell" in intents and not (intents - {"farewell", "greeting"}):
        reply = "Cảm ơn bạn đã ghé thăm TechWorld! Chúc bạn mua sắm vui vẻ 😊"
        return {"reply": reply, "products": [], "action_url": None}

    # ── Xây dựng query sản phẩm ───────────────────────────────────────────────
    query = db.query(Product).filter(Product.stock > 0)
    filters_applied = []

    # Lọc danh mục
    cat_slug = None
    for intent, slug in _INTENT_TO_CATEGORY.items():
        if intent in intents:
            cat_slug = slug
            query = query.join(Category).filter(Category.slug == slug)
            break

    # Lọc thương hiệu
    brand_slug = None
    for intent, bslug in _INTENT_TO_BRAND.items():
        if intent in intents:
            brand_slug = bslug
            query = query.join(Brand, Product.brand_id == Brand.id).filter(Brand.slug == bslug)
            filters_applied.append(f"thương hiệu **{bslug.title()}**")
            break

    # Lọc giá
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
        filters_applied.append(f"từ {min_price // 1_000_000}tr")
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
        filters_applied.append(f"đến {max_price // 1_000_000}tr")

    # Lọc giảm giá
    if "discount" in intents:
        query = query.filter(
            Product.original_price != None,
            Product.original_price > Product.price,
        )
        filters_applied.append("đang giảm giá")

    # Sắp xếp
    if "cheap" in intents:
        query = query.order_by(Product.price.asc())
    elif "premium" in intents:
        query = query.order_by(Product.price.desc())
    elif "trending" in intents:
        query = query.order_by(Product.review_count.desc(), Product.rating.desc())
    else:
        query = query.order_by(
            (Product.rating * func.log(Product.review_count + 1)).desc()
        )

    products = query.limit(limit).all()

    # ── Fallback: gợi ý cá nhân hoá nếu không có sản phẩm ───────────────────
    used_fallback = False
    if not products:
        used_fallback = True
        if user_id:
            products = personalised(db, user_id, limit=limit)
        else:
            products = trending_products(db, limit=limit)

    # ── Sinh câu trả lời ──────────────────────────────────────────────────────
    cat_names = {
        "dien-thoai": "điện thoại", "laptop": "laptop",
        "tablet": "máy tính bảng", "tai-nghe": "tai nghe & loa",
        "tv": "TV", "phu-kien-dt": "phụ kiện điện thoại",
        "phu-kien-pc": "phụ kiện máy tính", "man-hinh": "màn hình",
    }
    price_label = ""
    price_params = []
    if min_price and max_price:
        price_label = f"tầm {_format_price_vnd(min_price)}–{_format_price_vnd(max_price)}"
        price_params = [f"min_price={min_price}", f"max_price={max_price}"]
    elif max_price:
        price_label = f"dưới {_format_price_vnd(max_price)}"
        price_params = [f"max_price={max_price}"]
    elif min_price:
        price_label = f"trên {_format_price_vnd(min_price)}"
        price_params = [f"min_price={min_price}"]

    if "recommend" in intents and not cat_slug and not brand_slug and min_price is None and max_price is None:
        if user_id:
            reply = "Dựa trên lịch sử mua sắm của bạn, đây là những sản phẩm bạn có thể thích 👇"
            products = personalised(db, user_id, limit=limit)
        else:
            reply = "Đây là những sản phẩm đang được quan tâm nhiều nhất tại TechWorld 🔥"
            products = trending_products(db, limit=limit)
        action_url = "/san-pham"
    elif cat_slug:
        cat_label = cat_names.get(cat_slug, cat_slug)
        extras = ""
        if min_price or max_price:
            range_str = ""
            if min_price and max_price:
                range_str = f" tầm {_format_price_vnd(min_price)}–{_format_price_vnd(max_price)}"
            elif max_price:
                range_str = f" dưới {_format_price_vnd(max_price)}"
            elif min_price:
                range_str = f" trên {_format_price_vnd(min_price)}"
            extras += range_str
        if "cheap" in intents:
            extras += " giá tốt nhất"
        elif "premium" in intents:
            extras += " cao cấp"
        if "discount" in intents:
            extras += " đang giảm giá"

        brand_label = f" {brand_slug.title()}" if brand_slug else ""

        if products and not used_fallback:
            reply = f"Tôi tìm thấy **{len(products)}** {cat_label}{brand_label}{extras} phù hợp cho bạn 👇"
        else:
            reply = f"Hiện chưa có {cat_label}{extras} phù hợp. Đây là một số gợi ý khác:"
            products = trending_products(db, limit=limit)
        action_url = f"/danh-muc/{cat_slug}"
        if price_params:
            action_url = "/san-pham?" + "&".join([f"category={cat_slug}"] + price_params)
    elif brand_slug:
        if products:
            price_extra = f" {price_label}" if price_label else ""
            reply = f"Sản phẩm {brand_slug.title()}{price_extra} nổi bật tại TechWorld 👇"
        else:
            price_extra = f" {price_label}" if price_label else ""
            reply = f"Không tìm thấy sản phẩm {brand_slug.title()}{price_extra} phù hợp. Đây là gợi ý khác:"
        action_url = f"/san-pham?brand={brand_slug}"
        if price_params:
            action_url += "&" + "&".join(price_params)
    elif min_price is not None or max_price is not None:
        if products and not used_fallback:
            reply = f"Tôi tìm thấy **{len(products)}** sản phẩm {price_label} phù hợp cho bạn 👇"
        else:
            reply = f"Hiện chưa có sản phẩm {price_label} phù hợp. Đây là một số gợi ý khác:"
            products = trending_products(db, limit=limit)
        action_url = "/san-pham"
        if price_params:
            action_url += "?" + "&".join(price_params)
    elif "trending" in intents:
        reply = "Đây là những sản phẩm đang bán chạy nhất tuần này 🔥"
        products = trending_products(db, limit=limit)
        action_url = "/san-pham"
    elif "discount" in intents:
        reply = "Các sản phẩm đang có ưu đãi giảm giá hôm nay 🎉"
        action_url = "/san-pham?sale=1"
    else:
        # Không rõ intent → gợi ý chung
        if user_id:
            reply = ("Tôi chưa hiểu rõ yêu cầu của bạn 😅\n"
                     "Bạn có thể hỏi kiểu: *'Gợi ý điện thoại Samsung dưới 10 triệu'*\n"
                     "Trong lúc đó, đây là gợi ý dành riêng cho bạn:")
            products = personalised(db, user_id, limit=limit)
        else:
            reply = ("Tôi chưa hiểu rõ yêu cầu của bạn 😅\n"
                     "Hãy thử hỏi: *'Điện thoại iPhone giá tốt'*, *'Laptop dưới 20 triệu'*...\n"
                     "Dưới đây là sản phẩm đang hot:")
            products = trending_products(db, limit=limit)
        action_url = "/san-pham"

    return {"reply": reply, "products": products, "action_url": action_url}


# ═══════════════════════════════════════════════════════════════════════════════
# 7. HYBRID RECOMMENDATION (tổng hợp tất cả thuật toán)
# ═══════════════════════════════════════════════════════════════════════════════

def hybrid_recommend(
    db: Session,
    product_id: Optional[int] = None,
    user_id: Optional[int] = None,
    category_slug: Optional[str] = None,
    limit: int = 8,
) -> List:
    """
    Kết hợp nhiều thuật toán:
      - Nếu có product_id: content_based + collab_filter
      - Nếu có user_id: personalised
      - Còn lại: popular + trending
    """
    seen_ids = set()
    results = []

    def add(products):
        for p in products:
            if p.id not in seen_ids:
                seen_ids.add(p.id)
                results.append(p)
                if product_id:
                    seen_ids.add(product_id)

    if product_id:
        add(collab_filter(db, product_id, limit=limit))
        add(content_based(db, product_id, limit=limit))
    if user_id:
        add(personalised(db, user_id, limit=limit))
    if category_slug:
        add(popular_products(db, category_slug, limit=limit))
    if len(results) < limit:
        add(trending_products(db, limit=limit))
    if len(results) < limit:
        add(popular_products(db, limit=limit))

    return results[:limit]
