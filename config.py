import secrets

# ── App info ────────────────────────────────────────────────────────────────
APP_NAME = "TechWorld"
APP_DESCRIPTION = "Cửa hàng công nghệ trực tuyến - Chính hãng, Giá tốt"
APP_VERSION = "1.0.0"

# ── Security ─────────────────────────────────────────────────────────────────
# In production, set this via environment variable; never commit a real secret.
SECRET_KEY = secrets.token_hex(32)

# ── Database ─────────────────────────────────────────────────────────────────
DATABASE_URL = "sqlite:///./techworld.db"

# ── Pagination ───────────────────────────────────────────────────────────────
ITEMS_PER_PAGE = 12

# ── Currency ─────────────────────────────────────────────────────────────────
CURRENCY_SYMBOL = "₫"


def format_vnd(amount: int) -> str:
    """Return amount formatted as Vietnamese Đồng, e.g. 1.299.000₫"""
    return f"{amount:,}".replace(",", ".") + CURRENCY_SYMBOL


# ── Session cookie ────────────────────────────────────────────────────────────
SESSION_COOKIE_NAME = "techworld_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days in seconds

# ── Static / template paths ───────────────────────────────────────────────────
STATIC_DIR = "static"
TEMPLATES_DIR = "views"

# ── Admin defaults ────────────────────────────────────────────────────────────
DEFAULT_ADMIN_EMAIL = "admin@techworld.vn"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ADMIN_NAME = "Quản trị viên"
