"""
import_bestbuy.py — Import dữ liệu Best Buy vào TechWorld database

Cách dùng:
    python import_bestbuy.py

Đặt file products.json vào cùng thư mục với script này (thư mục Btl_Web).
Script sẽ:
  1. Xoá toàn bộ dữ liệu cũ (sản phẩm, danh mục, thương hiệu)
  2. Import ~15.000 sản phẩm công nghệ từ Best Buy dataset
  3. Giữ lại tài khoản admin và demo user
"""

import json
import re
import sys
import os

# ── Chạy từ thư mục Btl_Web ──────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, create_tables
from models import Category, Brand, Product, ProductSpec, User, CartItem, Order, OrderItem

# ═══════════════════════════════════════════════════════════════════════════════
# CẤU HÌNH
# ═══════════════════════════════════════════════════════════════════════════════

PRODUCTS_JSON = "products.json"   # Đổi thành đường dẫn đầy đủ nếu cần

# Chỉ lấy các danh mục công nghệ phù hợp với TechWorld
CATEGORY_MAP = {
    "Cell Phones":           ("Điện thoại",      "dien-thoai",   "📱", 1),
    "Computers & Tablets":   ("Laptop & Máy tính","laptop",       "💻", 2),
    "TV & Home Theater":     ("TV & Màn hình",    "tv-man-hinh",  "📺", 3),
    "Audio":                 ("Âm thanh",         "am-thanh",     "🔊", 4),
    "Cameras & Camcorders":  ("Camera",           "camera",       "📷", 5),
    "Car Electronics & GPS": ("Điện tử xe hơi",  "dien-tu-xe",   "🚗", 6),
    "Wearable Technology":   ("Thiết bị đeo",     "thiet-bi-deo", "⌚", 7),
    "Connected Home & Housewares": ("Nhà thông minh", "nha-thong-minh", "🏠", 8),
    "Video Games":           ("Video Games",      "video-games",  "🎮", 9),
    "Musical Instruments":   ("Nhạc cụ",          "nhac-cu",      "🎸", 10),
}

# Tỷ giá USD → VND (nhân giá USD với hệ số này)
USD_TO_VND = 25_000

# Giới hạn số sản phẩm import (None = lấy tất cả)
MAX_PRODUCTS = 5_000

# Chỉ lấy sản phẩm có giá > 0 và có ảnh
REQUIRE_IMAGE = True
REQUIRE_PRICE = True


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def slugify(text: str) -> str:
    """Chuyển text thành slug URL-safe."""
    text = text.lower().strip()
    text = re.sub(r"[àáạảãâầấậẩẫăằắặẳẵ]", "a", text)
    text = re.sub(r"[èéẹẻẽêềếệểễ]", "e", text)
    text = re.sub(r"[ìíịỉĩ]", "i", text)
    text = re.sub(r"[òóọỏõôồốộổỗơờớợởỡ]", "o", text)
    text = re.sub(r"[ùúụủũưừứựửữ]", "u", text)
    text = re.sub(r"[ỳýỵỷỹ]", "y", text)
    text = re.sub(r"đ", "d", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def usd_to_vnd(usd: float) -> int:
    """Làm tròn giá VND đẹp (bội số 1000)."""
    vnd = int(usd * USD_TO_VND)
    return round(vnd / 1000) * 1000


def clean_html(text: str) -> str:
    """Loại bỏ HTML entities cơ bản."""
    if not text:
        return ""
    text = text.replace("&#174;", "®").replace("&#8482;", "™")
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return text.strip()


def get_top_category(product_categories: list) -> str | None:
    """Lấy category phù hợp đầu tiên từ danh sách."""
    for cat in product_categories:
        name = cat.get("name", "")
        if name in CATEGORY_MAP:
            return name
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def run_import():
    # 1. Kiểm tra file
    if not os.path.exists(PRODUCTS_JSON):
        print(f"[ERROR] Không tìm thấy file '{PRODUCTS_JSON}'")
        print("        Đặt file products.json vào cùng thư mục với script này.")
        sys.exit(1)

    print(f"[import] Đọc file {PRODUCTS_JSON}...")
    with open(PRODUCTS_JSON, encoding="utf-8") as f:
        raw_products = json.load(f)
    print(f"[import] Tổng sản phẩm trong file: {len(raw_products):,}")

    create_tables()
    db = SessionLocal()

    try:
        # 2. Xoá dữ liệu cũ (giữ user)
        print("[import] Xoá dữ liệu sản phẩm cũ...")
        db.query(OrderItem).delete()
        db.query(Order).delete()
        db.query(CartItem).delete()
        db.query(ProductSpec).delete()
        db.query(Product).delete()
        db.query(Category).delete()
        db.query(Brand).delete()
        db.commit()

        # 3. Tạo danh mục
        print("[import] Tạo danh mục...")
        cat_objects = {}
        for eng_name, (vn_name, slug, icon, order) in CATEGORY_MAP.items():
            cat = Category(name=vn_name, slug=slug, icon=icon, display_order=order)
            db.add(cat)
            db.flush()
            cat_objects[eng_name] = cat
        db.commit()
        print(f"[import] Tạo {len(cat_objects)} danh mục.")

        # 4. Lọc sản phẩm hợp lệ
        print("[import] Lọc sản phẩm...")
        valid = []
        seen_slugs = set()

        for p in raw_products:
            # Phải có danh mục phù hợp
            top_cat = get_top_category(p.get("category", []))
            if not top_cat:
                continue

            # Giá hợp lệ
            price_usd = p.get("price", 0)
            if REQUIRE_PRICE and (not price_usd or price_usd <= 0):
                continue

            # Có ảnh
            if REQUIRE_IMAGE and not p.get("image"):
                continue

            # Slug unique
            raw_slug = slugify(p.get("name", ""))[:80] + "-" + str(p.get("sku", ""))
            if raw_slug in seen_slugs:
                continue
            seen_slugs.add(raw_slug)

            valid.append((p, top_cat, raw_slug))

            if MAX_PRODUCTS and len(valid) >= MAX_PRODUCTS:
                break

        print(f"[import] Sản phẩm hợp lệ: {len(valid):,}")

        # 5. Tạo brand objects (lazy)
        brand_objects = {}

        def get_or_create_brand(name: str):
            if not name:
                name = "Unknown"
            if name not in brand_objects:
                slug = slugify(name)[:50]
                # Tránh slug trùng
                final_slug = slug
                counter = 2
                while any(b.slug == final_slug for b in brand_objects.values()):
                    final_slug = f"{slug}-{counter}"
                    counter += 1
                brand = Brand(name=name, slug=final_slug)
                db.add(brand)
                db.flush()
                brand_objects[name] = brand
            return brand_objects[name]

        # 6. Import sản phẩm
        print("[import] Import sản phẩm...")
        count = 0

        for p, top_cat, slug in valid:
            category = cat_objects[top_cat]
            brand = get_or_create_brand(p.get("manufacturer", ""))

            price_usd = float(p.get("price", 0))
            price_vnd = usd_to_vnd(price_usd)
            # Giả lập giá gốc +15% cho sản phẩm có vẻ đang sale
            original_vnd = usd_to_vnd(price_usd * 1.15) if price_usd > 20 else None

            product = Product(
                name=clean_html(p.get("name", ""))[:200],
                slug=slug,
                description=clean_html(p.get("description", "")),
                price=price_vnd,
                original_price=original_vnd,
                image_url=p.get("image", ""),
                stock=10,          # mặc định tồn kho 10
                rating=4.0,        # mặc định rating 4.0
                review_count=0,
                is_featured=(price_usd > 200),   # sản phẩm > $200 → nổi bật
                category_id=category.id,
                brand_id=brand.id,
            )
            db.add(product)
            db.flush()

            # Specs từ các field có sẵn
            specs = []
            if p.get("model"):
                specs.append(("Model", p["model"]))
            if p.get("upc"):
                specs.append(("UPC", p["upc"]))
            specs.append(("Danh mục gốc", top_cat))

            for spec_name, spec_value in specs:
                db.add(ProductSpec(
                    product_id=product.id,
                    spec_name=spec_name,
                    spec_value=str(spec_value)[:200],
                ))

            count += 1
            if count % 500 == 0:
                db.commit()
                print(f"[import]   {count:,}/{len(valid):,} sản phẩm...")

        db.commit()
        print(f"[import] Hoàn thành: {count:,} sản phẩm, {len(brand_objects)} thương hiệu.")

        # 7. Đảm bảo admin tồn tại
        from config import DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_NAME
        if not db.query(User).filter(User.email == DEFAULT_ADMIN_EMAIL).first():
            admin = User(full_name=DEFAULT_ADMIN_NAME, email=DEFAULT_ADMIN_EMAIL, is_admin=True)
            admin.set_password(DEFAULT_ADMIN_PASSWORD)
            db.add(admin)

        if not db.query(User).filter(User.email == "user@techworld.vn").first():
            demo = User(full_name="Nguyễn Văn A", email="user@techworld.vn",
                        phone="0901234567", is_admin=False)
            demo.set_password("user123")
            db.add(demo)

        db.commit()
        print("[import] Tài khoản admin và demo đã sẵn sàng.")
        print("[import] ✓ Import thành công!")
        print()
        print("  Chạy app: python -m uvicorn main:app --reload")
        print("  Admin:    http://127.0.0.1:8000/admin/")

    finally:
        db.close()


if __name__ == "__main__":
    run_import()
