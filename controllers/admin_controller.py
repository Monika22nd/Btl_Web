from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import APP_NAME
from database import get_db
from models import User, Product, Category, Brand, Order, OrderItem, ProductSpec, CartItem

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="views")


# ── Guards ────────────────────────────────────────────────────────────────────
def _require_admin(request: Request):
    """Trả về user_id nếu là admin, ngược lại trả None."""
    if not request.session.get("user_id") or not request.session.get("is_admin"):
        return None
    return request.session.get("user_id")


def _admin_ctx(request: Request, db: Session) -> dict:
    user_id = request.session.get("user_id")
    cart_count = 0
    if user_id:
        cart_count = db.query(CartItem).filter(CartItem.user_id == user_id).count()
    return {
        "APP_NAME": APP_NAME,
        "user_id": user_id,
        "user_name": request.session.get("user_name"),
        "is_admin": request.session.get("is_admin", False),
        "cart_count": cart_count,
        "flash": request.session.pop("flash", None),
    }


def _redirect_login():
    return RedirectResponse(url="/dang-nhap?next=/admin/", status_code=303)


def _redirect_forbidden(request: Request, db: Session):
    return templates.TemplateResponse(
        "admin/403.html", {"request": request, **_admin_ctx(request, db)}, status_code=403
    )


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    """Trang tổng quan: thống kê nhanh + đơn hàng gần đây."""
    if not _require_admin(request):
        return _redirect_login()

    total_products = db.query(Product).count()
    total_users    = db.query(User).filter(User.is_admin == False).count()
    total_orders   = db.query(Order).count()

    # Doanh thu từ đơn đã giao
    from sqlalchemy import func
    revenue = (
        db.query(func.sum(Order.total))
        .filter(Order.status == "delivered")
        .scalar()
    ) or 0

    recent_orders = (
        db.query(Order)
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )

    low_stock_products = (
        db.query(Product)
        .filter(Product.stock <= 5)
        .order_by(Product.stock.asc())
        .limit(10)
        .all()
    )

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            **_admin_ctx(request, db),
            "total_products": total_products,
            "total_users": total_users,
            "total_orders": total_orders,
            "revenue": revenue,
            "recent_orders": recent_orders,
            "low_stock_products": low_stock_products,
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/products", response_class=HTMLResponse)
def admin_products(
    request: Request,
    page: int = 1,
    q: str = "",
    db: Session = Depends(get_db),
):
    """Danh sách sản phẩm — có tìm kiếm và phân trang."""
    if not _require_admin(request):
        return _redirect_login()

    PER_PAGE = 20
    query = db.query(Product)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    query = query.order_by(Product.created_at.desc())

    total = query.count()
    total_pages = max(1, -(-total // PER_PAGE))
    page = max(1, min(page, total_pages))
    products = query.offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()

    return templates.TemplateResponse(
        "admin/products.html",
        {
            "request": request,
            **_admin_ctx(request, db),
            "products": products,
            "q": q,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        },
    )


@router.get("/products/new", response_class=HTMLResponse)
def admin_product_new(request: Request, db: Session = Depends(get_db)):
    """Form thêm sản phẩm mới."""
    if not _require_admin(request):
        return _redirect_login()

    categories = db.query(Category).order_by(Category.display_order).all()
    brands     = db.query(Brand).all()

    return templates.TemplateResponse(
        "admin/product_form.html",
        {
            "request": request,
            **_admin_ctx(request, db),
            "product": None,
            "categories": categories,
            "brands": brands,
            "specs": [],
            "error": None,
        },
    )


@router.post("/products/new")
def admin_product_create(
    request: Request,
    name: str           = Form(...),
    slug: str           = Form(...),
    description: str    = Form(default=""),
    price: int          = Form(...),
    original_price: int = Form(default=None),
    image_url: str      = Form(default=""),
    stock: int          = Form(default=0),
    category_id: int    = Form(...),
    brand_id: int       = Form(...),
    is_featured: bool   = Form(default=False),
    spec_names: list[str]  = Form(default=[]),
    spec_values: list[str] = Form(default=[]),
    db: Session = Depends(get_db),
):
    """Tạo sản phẩm mới kèm thông số kỹ thuật."""
    if not _require_admin(request):
        return _redirect_login()

    # Kiểm tra slug trùng
    if db.query(Product).filter(Product.slug == slug).first():
        categories = db.query(Category).all()
        brands     = db.query(Brand).all()
        return templates.TemplateResponse(
            "admin/product_form.html",
            {
                "request": request,
                **_admin_ctx(request, db),
                "product": None,
                "categories": categories,
                "brands": brands,
                "specs": list(zip(spec_names, spec_values)),
                "error": f"Slug '{slug}' đã tồn tại. Vui lòng chọn slug khác.",
            },
            status_code=400,
        )

    product = Product(
        name=name.strip(),
        slug=slug.strip(),
        description=description.strip(),
        price=price,
        original_price=original_price or None,
        image_url=image_url.strip() or None,
        stock=stock,
        category_id=category_id,
        brand_id=brand_id,
        is_featured=is_featured,
    )
    db.add(product)
    db.flush()  # Lấy product.id trước khi commit

    # Lưu thông số kỹ thuật
    for sname, svalue in zip(spec_names, spec_values):
        if sname.strip() and svalue.strip():
            db.add(ProductSpec(product_id=product.id, spec_name=sname.strip(), spec_value=svalue.strip()))

    db.commit()
    request.session["flash"] = f"Đã thêm sản phẩm '{product.name}'."
    return RedirectResponse(url="/admin/products", status_code=303)


@router.get("/products/{product_id}/edit", response_class=HTMLResponse)
def admin_product_edit(product_id: int, request: Request, db: Session = Depends(get_db)):
    """Form chỉnh sửa sản phẩm."""
    if not _require_admin(request):
        return _redirect_login()

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/admin/products", status_code=303)

    categories = db.query(Category).order_by(Category.display_order).all()
    brands     = db.query(Brand).all()
    specs      = db.query(ProductSpec).filter(ProductSpec.product_id == product_id).all()

    return templates.TemplateResponse(
        "admin/product_form.html",
        {
            "request": request,
            **_admin_ctx(request, db),
            "product": product,
            "categories": categories,
            "brands": brands,
            "specs": specs,
            "error": None,
        },
    )


@router.post("/products/{product_id}/edit")
def admin_product_update(
    product_id: int,
    request: Request,
    name: str           = Form(...),
    slug: str           = Form(...),
    description: str    = Form(default=""),
    price: int          = Form(...),
    original_price: int = Form(default=None),
    image_url: str      = Form(default=""),
    stock: int          = Form(default=0),
    category_id: int    = Form(...),
    brand_id: int       = Form(...),
    is_featured: bool   = Form(default=False),
    spec_names: list[str]  = Form(default=[]),
    spec_values: list[str] = Form(default=[]),
    db: Session = Depends(get_db),
):
    """Cập nhật thông tin sản phẩm và thông số kỹ thuật."""
    if not _require_admin(request):
        return _redirect_login()

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/admin/products", status_code=303)

    # Kiểm tra slug trùng với sản phẩm khác
    slug_conflict = (
        db.query(Product)
        .filter(Product.slug == slug, Product.id != product_id)
        .first()
    )
    if slug_conflict:
        categories = db.query(Category).all()
        brands     = db.query(Brand).all()
        specs      = db.query(ProductSpec).filter(ProductSpec.product_id == product_id).all()
        return templates.TemplateResponse(
            "admin/product_form.html",
            {
                "request": request,
                **_admin_ctx(request, db),
                "product": product,
                "categories": categories,
                "brands": brands,
                "specs": specs,
                "error": f"Slug '{slug}' đã tồn tại.",
            },
            status_code=400,
        )

    product.name           = name.strip()
    product.slug           = slug.strip()
    product.description    = description.strip()
    product.price          = price
    product.original_price = original_price or None
    product.image_url      = image_url.strip() or None
    product.stock          = stock
    product.category_id    = category_id
    product.brand_id       = brand_id
    product.is_featured    = is_featured

    # Xoá specs cũ → thêm mới
    db.query(ProductSpec).filter(ProductSpec.product_id == product_id).delete()
    for sname, svalue in zip(spec_names, spec_values):
        if sname.strip() and svalue.strip():
            db.add(ProductSpec(product_id=product_id, spec_name=sname.strip(), spec_value=svalue.strip()))

    db.commit()
    request.session["flash"] = f"Đã cập nhật sản phẩm '{product.name}'."
    return RedirectResponse(url="/admin/products", status_code=303)


@router.post("/products/{product_id}/delete")
def admin_product_delete(product_id: int, request: Request, db: Session = Depends(get_db)):
    """Xoá sản phẩm (cascade xoá specs, cart_items, order_items)."""
    if not _require_admin(request):
        return _redirect_login()

    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.query(CartItem).filter(CartItem.product_id == product_id).delete()
        db.delete(product)
        db.commit()
        request.session["flash"] = f"Đã xoá sản phẩm '{product.name}'."

    return RedirectResponse(url="/admin/products", status_code=303)


# ═══════════════════════════════════════════════════════════════════════════════
# ORDERS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/orders", response_class=HTMLResponse)
def admin_orders(
    request: Request,
    status: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
):
    """Danh sách tất cả đơn hàng — lọc theo trạng thái, phân trang."""
    if not _require_admin(request):
        return _redirect_login()

    PER_PAGE = 20
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    query = query.order_by(Order.created_at.desc())

    total = query.count()
    total_pages = max(1, -(-total // PER_PAGE))
    page = max(1, min(page, total_pages))
    orders = query.offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()

    from models.order import ORDER_STATUS, ADMIN_ALLOWED_STATUS
    return templates.TemplateResponse(
        "admin/orders.html",
        {
            "request": request,
            **_admin_ctx(request, db),
            "orders": orders,
            "status_filter": status,
            "ORDER_STATUS": ORDER_STATUS,
            "ADMIN_ALLOWED_STATUS": ADMIN_ALLOWED_STATUS,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        },
    )


@router.get("/orders/{order_id}", response_class=HTMLResponse)
def admin_order_detail(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Chi tiết đơn hàng + danh sách sản phẩm."""
    if not _require_admin(request):
        return _redirect_login()

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return RedirectResponse(url="/admin/orders", status_code=303)

    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    user  = db.query(User).filter(User.id == order.user_id).first()

    from models.order import ORDER_STATUS, ADMIN_ALLOWED_STATUS
    return templates.TemplateResponse(
        "admin/order_detail.html",
        {
            "request": request,
            **_admin_ctx(request, db),
            "order": order,
            "items": items,
            "user": user,
            "ORDER_STATUS": ORDER_STATUS,
            "ADMIN_ALLOWED_STATUS": ADMIN_ALLOWED_STATUS,
        },
    )


@router.post("/orders/{order_id}/status")
def admin_order_update_status(
    order_id: int,
    request: Request,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    """Cập nhật trạng thái đơn hàng."""
    if not _require_admin(request):
        return _redirect_login()

    from models.order import ORDER_STATUS, ADMIN_ALLOWED_STATUS
    order = db.query(Order).filter(Order.id == order_id).first()
    if order and status in ADMIN_ALLOWED_STATUS:
        order.status = status
        db.commit()
        request.session["flash"] = f"Đã cập nhật trạng thái đơn #{order_id} → {ORDER_STATUS[status]}."

    return RedirectResponse(url=f"/admin/orders/{order_id}", status_code=303)


# ═══════════════════════════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/users", response_class=HTMLResponse)
def admin_users(
    request: Request,
    page: int = 1,
    q: str = "",
    db: Session = Depends(get_db),
):
    """Danh sách người dùng — tìm kiếm theo tên/email, phân trang."""
    if not _require_admin(request):
        return _redirect_login()

    PER_PAGE = 20
    query = db.query(User)
    if q:
        query = query.filter(
            (User.full_name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
        )
    query = query.order_by(User.created_at.desc())

    total = query.count()
    total_pages = max(1, -(-total // PER_PAGE))
    page = max(1, min(page, total_pages))
    users = query.offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()

    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            **_admin_ctx(request, db),
            "users": users,
            "q": q,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        },
    )


@router.post("/users/{user_id}/toggle-admin")
def admin_toggle_admin(user_id: int, request: Request, db: Session = Depends(get_db)):
    """Cấp / thu hồi quyền admin của một user."""
    if not _require_admin(request):
        return _redirect_login()

    # Không cho tự thu hồi quyền của chính mình
    current_user_id = request.session.get("user_id")
    if user_id == current_user_id:
        request.session["flash"] = "Không thể thay đổi quyền của chính mình."
        return RedirectResponse(url="/admin/users", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_admin = not user.is_admin
        db.commit()
        action = "Cấp" if user.is_admin else "Thu hồi"
        request.session["flash"] = f"{action} quyền admin cho '{user.full_name}'."

    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/users/{user_id}/delete")
def admin_user_delete(user_id: int, request: Request, db: Session = Depends(get_db)):
    """Xoá tài khoản người dùng (không được xoá chính mình)."""
    if not _require_admin(request):
        return _redirect_login()

    if user_id == request.session.get("user_id"):
        request.session["flash"] = "Không thể xoá tài khoản đang đăng nhập."
        return RedirectResponse(url="/admin/users", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.query(CartItem).filter(CartItem.user_id == user_id).delete()
        db.delete(user)
        db.commit()
        request.session["flash"] = f"Đã xoá tài khoản '{user.full_name}'."

    return RedirectResponse(url="/admin/users", status_code=303)


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/categories", response_class=HTMLResponse)
def admin_categories(request: Request, db: Session = Depends(get_db)):
    """Danh sách + form thêm danh mục."""
    if not _require_admin(request):
        return _redirect_login()

    categories = db.query(Category).order_by(Category.display_order).all()
    return templates.TemplateResponse(
        "admin/categories.html",
        {"request": request, **_admin_ctx(request, db), "categories": categories, "error": None},
    )


@router.post("/categories/new")
def admin_category_create(
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    icon: str = Form(default=""),
    display_order: int = Form(default=0),
    db: Session = Depends(get_db),
):
    if not _require_admin(request):
        return _redirect_login()

    if db.query(Category).filter(Category.slug == slug).first():
        categories = db.query(Category).order_by(Category.display_order).all()
        return templates.TemplateResponse(
            "admin/categories.html",
            {
                "request": request,
                **_admin_ctx(request, db),
                "categories": categories,
                "error": f"Slug '{slug}' đã tồn tại.",
            },
            status_code=400,
        )

    db.add(Category(name=name.strip(), slug=slug.strip(), icon=icon.strip() or None, display_order=display_order))
    db.commit()
    request.session["flash"] = f"Đã thêm danh mục '{name}'."
    return RedirectResponse(url="/admin/categories", status_code=303)


@router.post("/categories/{category_id}/delete")
def admin_category_delete(category_id: int, request: Request, db: Session = Depends(get_db)):
    """Xoá danh mục — từ chối nếu còn sản phẩm."""
    if not _require_admin(request):
        return _redirect_login()

    category = db.query(Category).filter(Category.id == category_id).first()
    if category:
        if db.query(Product).filter(Product.category_id == category_id).count() > 0:
            request.session["flash"] = f"Không thể xoá '{category.name}' vì vẫn còn sản phẩm."
        else:
            db.delete(category)
            db.commit()
            request.session["flash"] = f"Đã xoá danh mục '{category.name}'."

    return RedirectResponse(url="/admin/categories", status_code=303)


# ═══════════════════════════════════════════════════════════════════════════════
# BRANDS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/brands", response_class=HTMLResponse)
def admin_brands(request: Request, db: Session = Depends(get_db)):
    """Danh sách + form thêm thương hiệu."""
    if not _require_admin(request):
        return _redirect_login()

    brands = db.query(Brand).order_by(Brand.name).all()
    return templates.TemplateResponse(
        "admin/brands.html",
        {"request": request, **_admin_ctx(request, db), "brands": brands, "error": None},
    )


@router.post("/brands/new")
def admin_brand_create(
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    db: Session = Depends(get_db),
):
    if not _require_admin(request):
        return _redirect_login()

    if db.query(Brand).filter(Brand.slug == slug).first():
        brands = db.query(Brand).order_by(Brand.name).all()
        return templates.TemplateResponse(
            "admin/brands.html",
            {
                "request": request,
                **_admin_ctx(request, db),
                "brands": brands,
                "error": f"Slug '{slug}' đã tồn tại.",
            },
            status_code=400,
        )

    db.add(Brand(name=name.strip(), slug=slug.strip()))
    db.commit()
    request.session["flash"] = f"Đã thêm thương hiệu '{name}'."
    return RedirectResponse(url="/admin/brands", status_code=303)


@router.post("/brands/{brand_id}/delete")
def admin_brand_delete(brand_id: int, request: Request, db: Session = Depends(get_db)):
    """Xoá thương hiệu — từ chối nếu còn sản phẩm."""
    if not _require_admin(request):
        return _redirect_login()

    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if brand:
        if db.query(Product).filter(Product.brand_id == brand_id).count() > 0:
            request.session["flash"] = f"Không thể xoá '{brand.name}' vì vẫn còn sản phẩm."
        else:
            db.delete(brand)
            db.commit()
            request.session["flash"] = f"Đã xoá thương hiệu '{brand.name}'."

    return RedirectResponse(url="/admin/brands", status_code=303)
