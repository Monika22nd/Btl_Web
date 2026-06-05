from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from controllers.recommend_controller import router as recommend_router

from config import (
    APP_NAME, APP_DESCRIPTION, APP_VERSION,
    SECRET_KEY, SESSION_MAX_AGE,
    STATIC_DIR, TEMPLATES_DIR,
    format_vnd,
)
from database import create_tables, migrate_schema

BESTBUY_IMPORT_MIN_PRODUCTS = 1000


def bootstrap_data():
    create_tables()
    migrate_schema()

    from database import SessionLocal
    from models import Category, Product

    db = SessionLocal()
    try:
        product_count = db.query(Product).count()
        category_count = db.query(Category).count()
    finally:
        db.close()

    if product_count >= BESTBUY_IMPORT_MIN_PRODUCTS:
        return

    from import_bestbuy import PRODUCTS_JSON, run_import

    if Path(PRODUCTS_JSON).exists():
        print("[startup] Best Buy data is missing or incomplete. Importing products.json...")
        run_import()
        return

    if category_count == 0:
        print("[startup] products.json not found. Seeding sample data instead...")
        db = SessionLocal()
        try:
            from seed import run_seed
            run_seed(db)
        finally:
            db.close()


# ── Lifespan: runs once on startup ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import filtered Best Buy tech products on first run
    bootstrap_data()

    yield  # App runs here


# ── App instance ─────────────────────────────────────────────────────────────
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=SESSION_MAX_AGE,
    session_cookie="techworld_session",
    https_only=False,   # Set True in production with HTTPS
)

# ── Static files ──────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ── Jinja2 templates ──────────────────────────────────────────────────────────
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Inject helpers into every template context
templates.env.globals["APP_NAME"] = APP_NAME
templates.env.globals["format_vnd"] = format_vnd


# ── Routers ───────────────────────────────────────────────────────────────────
from controllers.home_controller import router as home_router
from controllers.product_controller import router as product_router
from controllers.cart_controller import router as cart_router
from controllers.order_controller import router as order_router
from controllers.auth_controller import router as auth_router
from controllers.admin_controller import router as admin_router

app.include_router(home_router)
app.include_router(product_router)
app.include_router(cart_router)
app.include_router(order_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(recommend_router)

# ── Custom 404 handler ────────────────────────────────────────────────────────
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        "404.html",
        {"request": request, "APP_NAME": APP_NAME},
        status_code=404,
    )


# ── Dev entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
