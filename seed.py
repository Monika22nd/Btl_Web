"""
seed.py — Khởi tạo dữ liệu mẫu cho TechWorld
Chạy tự động khi app khởi động lần đầu (DB trống).
Hoặc chạy thủ công: python seed.py
"""

from database import SessionLocal, create_tables
from models import Category, Brand, Product, ProductSpec, User


# ═══════════════════════════════════════════════════════════════════════════════
# DATA
# ═══════════════════════════════════════════════════════════════════════════════

CATEGORIES = [
    {"name": "Điện thoại",   "slug": "dien-thoai",  "icon": "📱", "display_order": 1},
    {"name": "Laptop",        "slug": "laptop",       "icon": "💻", "display_order": 2},
    {"name": "Máy tính bảng","slug": "may-tinh-bang","icon": "📲", "display_order": 3},
    {"name": "Tai nghe",      "slug": "tai-nghe",     "icon": "🎧", "display_order": 4},
    {"name": "Đồng hồ",      "slug": "dong-ho",      "icon": "⌚", "display_order": 5},
    {"name": "Phụ kiện",     "slug": "phu-kien",     "icon": "🔌", "display_order": 6},
]

BRANDS = [
    {"name": "Apple",   "slug": "apple"},
    {"name": "Samsung", "slug": "samsung"},
    {"name": "Xiaomi",  "slug": "xiaomi"},
    {"name": "ASUS",    "slug": "asus"},
    {"name": "Dell",    "slug": "dell"},
    {"name": "Sony",    "slug": "sony"},
    {"name": "Oppo",    "slug": "oppo"},
    {"name": "Lenovo",  "slug": "lenovo"},
]

# (name, slug, description, price, original_price, stock, rating, review_count,
#  is_featured, category_slug, brand_slug, image_url, specs: list[tuple])
PRODUCTS = [
    # ── Điện thoại ─────────────────────────────────────────────────────────────
    (
        "iPhone 16 Pro Max 256GB", "iphone-16-pro-max-256gb",
        "iPhone 16 Pro Max với chip A18 Pro mạnh mẽ, camera 48MP thế hệ mới và màn hình ProMotion 6.9 inch.",
        34_990_000, 36_990_000, 50, 4.9, 128, True,
        "dien-thoai", "apple",
        "https://placehold.co/400x400?text=iPhone+16+Pro+Max",
        [("Màn hình", "6.9 inch Super Retina XDR OLED"), ("Chip", "Apple A18 Pro"),
         ("RAM", "8GB"), ("Bộ nhớ", "256GB"), ("Camera sau", "48MP + 48MP + 12MP"),
         ("Pin", "4685mAh"), ("Hệ điều hành", "iOS 18")],
    ),
    (
        "iPhone 15 128GB", "iphone-15-128gb",
        "iPhone 15 với Dynamic Island, camera 48MP và sạc USB-C tiện lợi.",
        22_990_000, 24_990_000, 80, 4.7, 95, True,
        "dien-thoai", "apple",
        "https://placehold.co/400x400?text=iPhone+15",
        [("Màn hình", "6.1 inch Super Retina XDR"), ("Chip", "Apple A16 Bionic"),
         ("RAM", "6GB"), ("Bộ nhớ", "128GB"), ("Camera sau", "48MP + 12MP"),
         ("Pin", "3877mAh"), ("Hệ điều hành", "iOS 17")],
    ),
    (
        "Samsung Galaxy S25 Ultra 512GB", "samsung-s25-ultra-512gb",
        "Galaxy S25 Ultra với bút S Pen tích hợp, camera 200MP và AI Galaxy tiên tiến.",
        33_990_000, 35_990_000, 45, 4.8, 76, True,
        "dien-thoai", "samsung",
        "https://placehold.co/400x400?text=S25+Ultra",
        [("Màn hình", "6.9 inch Dynamic AMOLED 2X"), ("Chip", "Snapdragon 8 Elite"),
         ("RAM", "12GB"), ("Bộ nhớ", "512GB"), ("Camera sau", "200MP + 50MP + 10MP + 12MP"),
         ("Pin", "5000mAh"), ("Hệ điều hành", "Android 15 / One UI 7")],
    ),
    (
        "Samsung Galaxy A55 5G 256GB", "samsung-a55-5g-256gb",
        "Galaxy A55 5G thiết kế sang trọng, màn hình Super AMOLED 120Hz và pin lớn.",
        10_490_000, 11_490_000, 120, 4.5, 54, False,
        "dien-thoai", "samsung",
        "https://placehold.co/400x400?text=Galaxy+A55",
        [("Màn hình", "6.6 inch Super AMOLED 120Hz"), ("Chip", "Exynos 1480"),
         ("RAM", "8GB"), ("Bộ nhớ", "256GB"), ("Camera sau", "50MP + 12MP + 5MP"),
         ("Pin", "5000mAh"), ("Hệ điều hành", "Android 14")],
    ),
    (
        "Xiaomi 14 Ultra 512GB", "xiaomi-14-ultra-512gb",
        "Xiaomi 14 Ultra hợp tác Leica, camera 1 inch đỉnh cao và sạc nhanh 90W.",
        28_990_000, 30_490_000, 30, 4.7, 42, True,
        "dien-thoai", "xiaomi",
        "https://placehold.co/400x400?text=Xiaomi+14+Ultra",
        [("Màn hình", "6.73 inch AMOLED 120Hz"), ("Chip", "Snapdragon 8 Gen 3"),
         ("RAM", "16GB"), ("Bộ nhớ", "512GB"), ("Camera sau", "50MP Leica x4"),
         ("Pin", "5300mAh"), ("Hệ điều hành", "Android 14 / MIUI 14")],
    ),
    (
        "Oppo Find X8 Pro 256GB", "oppo-find-x8-pro-256gb",
        "Oppo Find X8 Pro camera Hasselblad, sạc SUPERVOOC 80W siêu nhanh.",
        26_990_000, 28_490_000, 35, 4.6, 31, False,
        "dien-thoai", "oppo",
        "https://placehold.co/400x400?text=Find+X8+Pro",
        [("Màn hình", "6.78 inch AMOLED 120Hz"), ("Chip", "MediaTek Dimensity 9400"),
         ("RAM", "16GB"), ("Bộ nhớ", "256GB"), ("Camera sau", "50MP Hasselblad x3"),
         ("Pin", "5910mAh"), ("Hệ điều hành", "Android 15 / ColorOS 15")],
    ),

    # ── Laptop ─────────────────────────────────────────────────────────────────
    (
        "MacBook Air M3 13 inch 256GB", "macbook-air-m3-13-256gb",
        "MacBook Air M3 siêu mỏng nhẹ, hiệu năng vượt trội và pin lên đến 18 giờ.",
        28_990_000, 30_990_000, 40, 4.9, 87, True,
        "laptop", "apple",
        "https://placehold.co/400x400?text=MacBook+Air+M3",
        [("CPU", "Apple M3 8-core"), ("RAM", "8GB Unified Memory"),
         ("Ổ cứng", "256GB SSD"), ("Màn hình", "13.6 inch Liquid Retina"),
         ("Pin", "52.6Wh, ~18 giờ"), ("Hệ điều hành", "macOS Sequoia")],
    ),
    (
        "MacBook Pro M4 14 inch 512GB", "macbook-pro-m4-14-512gb",
        "MacBook Pro M4 chip Pro, màn hình Liquid Retina XDR ProMotion 120Hz.",
        52_990_000, 55_990_000, 20, 4.9, 63, True,
        "laptop", "apple",
        "https://placehold.co/400x400?text=MacBook+Pro+M4",
        [("CPU", "Apple M4 Pro 12-core"), ("RAM", "24GB Unified Memory"),
         ("Ổ cứng", "512GB SSD"), ("Màn hình", "14.2 inch Liquid Retina XDR 120Hz"),
         ("Pin", "72.4Wh, ~22 giờ"), ("Hệ điều hành", "macOS Sequoia")],
    ),
    (
        "ASUS ROG Zephyrus G16 RTX 4070", "asus-rog-zephyrus-g16-rtx4070",
        "Laptop gaming mỏng nhẹ ROG Zephyrus G16, màn hình OLED 240Hz, RTX 4070.",
        42_990_000, 45_990_000, 15, 4.8, 38, True,
        "laptop", "asus",
        "https://placehold.co/400x400?text=ROG+Zephyrus+G16",
        [("CPU", "Intel Core Ultra 7 155H"), ("RAM", "16GB DDR5"),
         ("Ổ cứng", "1TB NVMe SSD"), ("GPU", "NVIDIA RTX 4070 8GB"),
         ("Màn hình", "16 inch OLED 240Hz"), ("Pin", "90Wh")],
    ),
    (
        "Dell XPS 15 Core i7 RTX 4060", "dell-xps-15-i7-rtx4060",
        "Dell XPS 15 thiết kế premium, màn hình OLED 4K cảm ứng, hiệu năng mạnh mẽ.",
        45_990_000, 48_490_000, 12, 4.7, 29, False,
        "laptop", "dell",
        "https://placehold.co/400x400?text=Dell+XPS+15",
        [("CPU", "Intel Core i7-13700H"), ("RAM", "32GB DDR5"),
         ("Ổ cứng", "1TB NVMe SSD"), ("GPU", "NVIDIA RTX 4060 8GB"),
         ("Màn hình", "15.6 inch OLED 4K cảm ứng"), ("Pin", "86Wh")],
    ),
    (
        "Lenovo ThinkPad X1 Carbon Gen 12", "lenovo-thinkpad-x1-carbon-gen12",
        "ThinkPad X1 Carbon siêu nhẹ 1.12kg, bảo mật doanh nghiệp và bàn phím huyền thoại.",
        38_990_000, 41_990_000, 18, 4.6, 22, False,
        "laptop", "lenovo",
        "https://placehold.co/400x400?text=ThinkPad+X1",
        [("CPU", "Intel Core Ultra 7 165U"), ("RAM", "16GB LPDDR5"),
         ("Ổ cứng", "512GB NVMe SSD"), ("Màn hình", "14 inch IPS 2.8K"),
         ("Trọng lượng", "1.12kg"), ("Pin", "57Wh, ~15 giờ")],
    ),

    # ── Máy tính bảng ──────────────────────────────────────────────────────────
    (
        "iPad Pro M4 11 inch 256GB", "ipad-pro-m4-11-256gb",
        "iPad Pro M4 mỏng nhất từ trước tới nay, màn hình Ultra Retina XDR OLED tuyệt đẹp.",
        23_990_000, 25_490_000, 30, 4.9, 51, True,
        "may-tinh-bang", "apple",
        "https://placehold.co/400x400?text=iPad+Pro+M4",
        [("Chip", "Apple M4"), ("Màn hình", "11 inch Ultra Retina XDR OLED"),
         ("Bộ nhớ", "256GB"), ("Camera", "12MP + 10MP LiDAR"),
         ("Pin", "~10 giờ"), ("Hệ điều hành", "iPadOS 17")],
    ),
    (
        "Samsung Galaxy Tab S10 Ultra 256GB", "samsung-tab-s10-ultra-256gb",
        "Galaxy Tab S10 Ultra màn hình 14.6 inch AMOLED khổng lồ, bút S Pen kèm theo.",
        25_990_000, 27_490_000, 22, 4.7, 34, True,
        "may-tinh-bang", "samsung",
        "https://placehold.co/400x400?text=Tab+S10+Ultra",
        [("Chip", "Snapdragon 8 Gen 3"), ("Màn hình", "14.6 inch Dynamic AMOLED 120Hz"),
         ("RAM", "12GB"), ("Bộ nhớ", "256GB"), ("Pin", "11200mAh"),
         ("Hệ điều hành", "Android 14 / One UI 6.1")],
    ),

    # ── Tai nghe ───────────────────────────────────────────────────────────────
    (
        "AirPods Pro 2nd Gen USB-C", "airpods-pro-2-usbc",
        "AirPods Pro thế hệ 2 chống ồn ANC vượt trội, âm thanh Adaptive Audio thông minh.",
        6_490_000, 6_990_000, 100, 4.8, 142, True,
        "tai-nghe", "apple",
        "https://placehold.co/400x400?text=AirPods+Pro+2",
        [("Loại", "In-ear True Wireless"), ("Chống ồn", "ANC chủ động"),
         ("Thời lượng pin", "6h (30h với hộp sạc)"), ("Kết nối", "Bluetooth 5.3"),
         ("Sạc", "USB-C / MagSafe"), ("Kháng nước", "IP54")],
    ),
    (
        "Sony WH-1000XM6", "sony-wh-1000xm6",
        "Tai nghe over-ear Sony flagship, chống ồn số 1 thế giới và chất âm Hi-Res.",
        9_990_000, 10_990_000, 60, 4.9, 89, True,
        "tai-nghe", "sony",
        "https://placehold.co/400x400?text=WH-1000XM6",
        [("Loại", "Over-ear Wireless"), ("Chống ồn", "ANC thế hệ mới"),
         ("Thời lượng pin", "40 giờ"), ("Kết nối", "Bluetooth 5.3 / Multipoint"),
         ("Driver", "30mm"), ("Codec", "LDAC / AAC / SBC")],
    ),
    (
        "Samsung Galaxy Buds3 Pro", "samsung-galaxy-buds3-pro",
        "Galaxy Buds3 Pro thiết kế mới lạ, âm thanh Hi-Fi và chống ồn thông minh.",
        4_990_000, 5_490_000, 75, 4.6, 47, False,
        "tai-nghe", "samsung",
        "https://placehold.co/400x400?text=Buds3+Pro",
        [("Loại", "In-ear True Wireless"), ("Chống ồn", "ANC thích ứng"),
         ("Thời lượng pin", "6h (26h với hộp sạc)"), ("Kết nối", "Bluetooth 5.4"),
         ("Kháng nước", "IP57")],
    ),

    # ── Đồng hồ ───────────────────────────────────────────────────────────────
    (
        "Apple Watch Series 10 45mm", "apple-watch-series-10-45mm",
        "Apple Watch Series 10 mỏng nhất từ trước tới nay, màn hình lớn hơn và sạc nhanh hơn.",
        11_990_000, 12_990_000, 55, 4.8, 76, True,
        "dong-ho", "apple",
        "https://placehold.co/400x400?text=Watch+Series+10",
        [("Màn hình", "45mm Always-On Retina LTPO OLED"), ("Chip", "Apple S10"),
         ("Kết nối", "GPS + Cellular"), ("Pin", "~18 giờ"),
         ("Kháng nước", "50m"), ("Cảm biến", "Tim mạch, SpO2, Nhiệt độ")],
    ),
    (
        "Samsung Galaxy Watch 7 44mm", "samsung-galaxy-watch-7-44mm",
        "Galaxy Watch 7 với chip 3nm mới nhất, theo dõi sức khoẻ toàn diện và pin bền.",
        7_490_000, 7_990_000, 48, 4.6, 38, False,
        "dong-ho", "samsung",
        "https://placehold.co/400x400?text=Galaxy+Watch+7",
        [("Màn hình", "44mm Super AMOLED 60Hz"), ("Chip", "Exynos W1000 3nm"),
         ("Kết nối", "GPS + Bluetooth + Wi-Fi"), ("Pin", "~40 giờ"),
         ("Kháng nước", "5ATM + IP68")],
    ),

    # ── Phụ kiện ──────────────────────────────────────────────────────────────
    (
        "Sạc MagSafe 15W Apple", "sac-magsafe-15w-apple",
        "Sạc không dây MagSafe chính hãng Apple, sạc nhanh 15W cho iPhone 12 trở lên.",
        1_190_000, 1_290_000, 200, 4.7, 210, False,
        "phu-kien", "apple",
        "https://placehold.co/400x400?text=MagSafe+15W",
        [("Công suất", "15W (cho iPhone)"), ("Chuẩn sạc", "MagSafe / Qi"),
         ("Tương thích", "iPhone 12 trở lên"), ("Cáp", "Không kèm theo")],
    ),
    (
        "Ốp lưng Samsung S25 Ultra Silicone", "op-lung-s25-ultra-silicone",
        "Ốp lưng silicone chính hãng Samsung Galaxy S25 Ultra, bảo vệ toàn diện.",
        590_000, 690_000, 300, 4.4, 88, False,
        "phu-kien", "samsung",
        "https://placehold.co/400x400?text=Ốp+S25+Ultra",
        [("Chất liệu", "Silicone cao cấp"), ("Tương thích", "Samsung Galaxy S25 Ultra"),
         ("Màu sắc", "Đen / Trắng / Xanh"), ("Bảo vệ", "Chống va đập 4 góc")],
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# SEED FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def run_seed(db):
    print("🌱 Bắt đầu seed dữ liệu mẫu...")

    # 1. Categories
    cat_map = {}
    for data in CATEGORIES:
        cat = Category(**data)
        db.add(cat)
        db.flush()
        cat_map[cat.slug] = cat.id
    print(f"  ✅ {len(CATEGORIES)} danh mục")

    # 2. Brands
    brand_map = {}
    for data in BRANDS:
        brand = Brand(**data)
        db.add(brand)
        db.flush()
        brand_map[brand.slug] = brand.id
    print(f"  ✅ {len(BRANDS)} thương hiệu")

    # 3. Products + Specs
    for (name, slug, desc, price, orig_price, stock, rating, review_count,
         is_featured, cat_slug, brand_slug, image_url, specs) in PRODUCTS:

        product = Product(
            name=name,
            slug=slug,
            description=desc,
            price=price,
            original_price=orig_price,
            stock=stock,
            rating=rating,
            review_count=review_count,
            is_featured=is_featured,
            category_id=cat_map[cat_slug],
            brand_id=brand_map[brand_slug],
            image_url=image_url,
        )
        db.add(product)
        db.flush()

        for spec_name, spec_value in specs:
            db.add(ProductSpec(
                product_id=product.id,
                spec_name=spec_name,
                spec_value=spec_value,
            ))

    print(f"  ✅ {len(PRODUCTS)} sản phẩm + thông số kỹ thuật")

    # 4. Admin account
    from config import DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_NAME
    admin = User(
        full_name=DEFAULT_ADMIN_NAME,
        email=DEFAULT_ADMIN_EMAIL,
        is_admin=True,
    )
    admin.set_password(DEFAULT_ADMIN_PASSWORD)
    db.add(admin)

    # 5. Demo user
    demo = User(
        full_name="Nguyễn Văn A",
        email="user@techworld.vn",
        phone="0901234567",
        address="123 Nguyễn Huệ, Quận 1, TP.HCM",
        is_admin=False,
    )
    demo.set_password("user123")
    db.add(demo)

    db.commit()
    print("  ✅ Tài khoản admin + demo user")
    print("🎉 Seed hoàn tất!")


# ═══════════════════════════════════════════════════════════════════════════════
# CHẠY THỦ CÔNG
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    create_tables()
    db = SessionLocal()
    try:
        from models import Category as _C
        if db.query(_C).count() > 0:
            print("⚠️  DB đã có dữ liệu. Bỏ qua seed.")
        else:
            run_seed(db)
    finally:
        db.close()
