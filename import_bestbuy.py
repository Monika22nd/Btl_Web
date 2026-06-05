"""
import_bestbuy.py — Import dữ liệu Best Buy vào TechWorld (chỉ lấy danh mục công nghệ)

Cách dùng:
    python import_bestbuy.py

Đặt file products.json vào cùng thư mục Btl_Web trước khi chạy.
"""

import json, re, sys, os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import SessionLocal, create_tables
from models import Category, Brand, Product, ProductSpec, User, CartItem, Order, OrderItem

# ═══════════════════════════════════════════════════════════════════════════════
# CẤU HÌNH
# ═══════════════════════════════════════════════════════════════════════════════

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCTS_JSON = os.path.join(BASE_DIR, "products.json")
USD_TO_VND    = 25_000
MAX_PRODUCTS  = None              # None = lấy tất cả

# ── Danh mục TechWorld (tên VN, icon, thứ tự hiển thị) ───────────────────────
CATEGORIES_VN = {
    "dien-thoai":  ("Điện thoại",          "📱", 1),
    "tablet":      ("Máy tính bảng",        "📲", 2),
    "laptop":      ("Laptop",               "💻", 3),
    "man-hinh":    ("Màn hình",             "🖥️", 4),
    "tai-nghe":    ("Tai nghe & Loa",       "🎧", 5),
    "phu-kien-dt": ("Phụ kiện điện thoại",  "📦", 6),
    "phu-kien-pc": ("Phụ kiện máy tính",    "🖱️", 7),
    "tv":          ("TV",                   "📺", 8),
}

# ── Quy tắc phân loại: tất cả tên trong list phải có trong category path ─────
# Ưu tiên từ trên xuống (rule đầu tiên khớp thắng)
RULES = [
    # Điện thoại thật (không lấy accessories ở đây)
    (["Cell Phones", "Unlocked Cell Phones"],            "dien-thoai"),
    (["Cell Phones", "All Cell Phones with Plans"],      "dien-thoai"),
    (["Cell Phones", "iPhone"],                          "dien-thoai"),
    (["Cell Phones", "No-Contract Phones"],              "dien-thoai"),
    (["Cell Phones", "Refurbished & Pre-Owned Phones"],  "dien-thoai"),
    # Tablet & iPad
    (["Computers & Tablets", "Tablets"],                             "tablet"),
    (["Computers & Tablets", "iPad & Tablet Accessories"],           "tablet"),
    # Laptop
    (["Computers & Tablets", "Laptops"],                             "laptop"),
    # Màn hình PC
    (["Computers & Tablets", "Monitors"],                            "man-hinh"),
    # Tai nghe & loa bluetooth
    (["Audio", "Headphones"],                                        "tai-nghe"),
    (["Audio", "Bluetooth & Wireless Speakers"],                     "tai-nghe"),
    # Phụ kiện điện thoại (ốp lưng, sạc, cáp, pin...)
    (["Cell Phones", "Cell Phone Accessories"],                      "phu-kien-dt"),
    # Phụ kiện laptop/PC (chuột, bàn phím, USB, túi...)
    (["Computers & Tablets", "Computer Accessories & Peripherals"],  "phu-kien-pc"),
    # TV
    (["TV & Home Theater", "TVs"],                                   "tv"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def classify(product_categories: list):
    names = {c["name"] for c in product_categories}
    for required, slug in RULES:
        if all(r in names for r in required):
            return slug
    return None


def slugify(text: str) -> str:
    text = text.lower().strip()
    for src, dst in [
        ("àáạảãâầấậẩẫăằắặẳẵ","a"), ("èéẹẻẽêềếệểễ","e"),
        ("ìíịỉĩ","i"), ("òóọỏõôồốộổỗơờớợởỡ","o"),
        ("ùúụủũưừứựửữ","u"), ("ỳýỵỷỹ","y"), ("đ","d"),
    ]:
        for ch in src:
            text = text.replace(ch, dst)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def usd_vnd(usd: float) -> int:
    return round(int(usd * USD_TO_VND) / 1000) * 1000


def clean(text: str) -> str:
    if not text:
        return ""
    return (text.replace("&#174;","®").replace("&#8482;","™")
                .replace("&amp;","&").replace("&lt;","<").replace("&gt;",">").strip())


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def run_import():
    if not os.path.exists(PRODUCTS_JSON):
        print(f"[ERROR] Không tìm thấy '{PRODUCTS_JSON}'")
        print("        Đặt file products.json vào thư mục Btl_Web rồi chạy lại.")
        sys.exit(1)

    print(f"[1/6] Đọc {PRODUCTS_JSON}...")
    with open(PRODUCTS_JSON, encoding="utf-8") as f:
        raw = json.load(f)
    print(f"      → {len(raw):,} bản ghi trong file")

    create_tables()
    db = SessionLocal()

    try:
        # ── Xoá data cũ ──────────────────────────────────────────────────────
        print("[2/6] Xoá data cũ...")
        db.query(OrderItem).delete()
        db.query(Order).delete()
        db.query(CartItem).delete()
        db.query(ProductSpec).delete()
        db.query(Product).delete()
        db.query(Category).delete()
        db.query(Brand).delete()
        db.commit()

        # ── Tạo danh mục ─────────────────────────────────────────────────────
        print("[3/6] Tạo danh mục...")
        cat_map = {}
        for slug, (name, icon, order) in CATEGORIES_VN.items():
            cat = Category(name=name, slug=slug, icon=icon, display_order=order)
            db.add(cat); db.flush()
            cat_map[slug] = cat
        db.commit()
        print(f"      → {len(cat_map)} danh mục")

        # ── Lọc & phân loại ──────────────────────────────────────────────────
        print("[4/6] Lọc sản phẩm phù hợp...")
        valid = []
        seen_slugs = set()

        for p in raw:
            price_usd = float(p.get("price") or 0)
            if price_usd <= 0 or not p.get("image"):
                continue
            cat_slug = classify(p.get("category", []))
            if not cat_slug:
                continue
            raw_slug = slugify(p.get("name",""))[:70] + "-" + str(p.get("sku",""))
            if raw_slug in seen_slugs:
                continue
            seen_slugs.add(raw_slug)
            valid.append((p, cat_slug, raw_slug))
            if MAX_PRODUCTS and len(valid) >= MAX_PRODUCTS:
                break

        print(f"      → {len(valid):,} sản phẩm hợp lệ")

        from collections import Counter
        by_cat = Counter(s for _, s, _ in valid)
        for slug, cnt in sorted(by_cat.items(), key=lambda x: -x[1]):
            print(f"         {CATEGORIES_VN[slug][0]:30s}: {cnt:,}")

        # ── Import ────────────────────────────────────────────────────────────
        print("[5/6] Import vào database...")
        brand_map = {}

        def get_brand(name):
            name = (name or "Unknown").strip()
            if name not in brand_map:
                slug = slugify(name)[:50]
                final, i = slug, 2
                while any(b.slug == final for b in brand_map.values()):
                    final = f"{slug}-{i}"; i += 1
                b = Brand(name=name, slug=final)
                db.add(b); db.flush()
                brand_map[name] = b
            return brand_map[name]

        count = 0
        for p, cat_slug, slug in valid:
            price_usd = float(p.get("price", 0))
            product = Product(
                name           = clean(p.get("name",""))[:200],
                slug           = slug,
                description    = clean(p.get("description","")),
                price          = usd_vnd(price_usd),
                original_price = usd_vnd(price_usd * 1.15) if price_usd > 20 else None,
                image_url      = p.get("image",""),
                stock          = 15,
                rating         = 4.0,
                review_count   = 0,
                is_featured    = price_usd > 150,
                category_id    = cat_map[cat_slug].id,
                brand_id       = get_brand(p.get("manufacturer","")).id,
            )
            db.add(product); db.flush()

            for sname, sval in [("Model", p.get("model")), ("UPC", p.get("upc"))]:
                if sval:
                    db.add(ProductSpec(product_id=product.id,
                                       spec_name=sname, spec_value=str(sval)[:200]))
            count += 1
            if count % 500 == 0:
                db.commit()
                print(f"         {count:,}/{len(valid):,}...")

        db.commit()
        print(f"      → {count:,} sản phẩm | {len(brand_map)} thương hiệu")

        # ── Tài khoản ─────────────────────────────────────────────────────────
        print("[6/6] Tạo tài khoản admin/demo...")
        from config import DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_NAME
        if not db.query(User).filter(User.email == DEFAULT_ADMIN_EMAIL).first():
            admin = User(full_name=DEFAULT_ADMIN_NAME, email=DEFAULT_ADMIN_EMAIL, is_admin=True)
            admin.set_password(DEFAULT_ADMIN_PASSWORD); db.add(admin)
        if not db.query(User).filter(User.email == "user@techworld.vn").first():
            demo = User(full_name="Nguyễn Văn A", email="user@techworld.vn",
                        phone="0901234567", is_admin=False)
            demo.set_password("user123"); db.add(demo)
        db.commit()

        print()
        print("✓ Import hoàn tất!")
        print(f"  Sản phẩm   : {count:,}")
        print(f"  Thương hiệu: {len(brand_map)}")
        print()
        print("  Chạy app: python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000")

    finally:
        db.close()


if __name__ == "__main__":
    run_import()
