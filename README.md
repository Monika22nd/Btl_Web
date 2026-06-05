# TechWorld - Btl_Web

TechWorld là website thương mại điện tử bán sản phẩm công nghệ, được xây dựng bằng FastAPI, Jinja2, SQLAlchemy và SQLite. Website mô phỏng quy trình mua hàng cơ bản gồm xem sản phẩm, tìm kiếm/lọc sản phẩm, đăng ký/đăng nhập, quản lý giỏ hàng, đặt hàng, gợi ý sản phẩm và quản trị dữ liệu.

## Thông tin chung

- Tên dự án: `TechWorld`
- Chủ đề: website bán hàng công nghệ
- Mô hình tổ chức code: MVC
- Backend: FastAPI
- Template engine: Jinja2
- ORM: SQLAlchemy
- Database: SQLite
- Frontend: HTML, CSS, JavaScript
- Nguồn dữ liệu sản phẩm: file `products.json` từ Best Buy, import bằng `import_bestbuy.py`
- Vị trí repo trên máy hiện tại: `C:\Users\ASUS\Documents\New project\Btl_Web`
- URL chạy local mặc định: `http://127.0.0.1:8000`

## Dữ liệu Best Buy

Dự án sử dụng dữ liệu sản phẩm công nghệ từ Best Buy thông qua file `products.json`. Script `import_bestbuy.py` đọc dữ liệu Best Buy, lọc các nhóm sản phẩm công nghệ phù hợp, chuẩn hóa danh mục/thương hiệu/thông số, rồi lưu vào database SQLite.

File `products.json` gốc có rất nhiều sản phẩm thuộc nhiều nhóm khác nhau, không chỉ đồ công nghệ. Dự án không import toàn bộ file này; `import_bestbuy.py` dùng các rule phân loại để chỉ lấy các nhóm phù hợp với website TechWorld như điện thoại, laptop, tablet, màn hình, tai nghe, phụ kiện và TV.

Luồng import dữ liệu:

```text
products.json -> import_bestbuy.py -> SQLite techworld.db -> Website TechWorld
```

Khi chạy web lần đầu, nếu database chưa có dữ liệu Best Buy hoặc chỉ có dữ liệu mẫu, ứng dụng sẽ tự động chạy `import_bestbuy.py` để tạo `techworld.db`. Các lần chạy sau sẽ dùng lại database đã import, không import lại nếu số lượng sản phẩm đã đủ.

Các nhóm dữ liệu chính sau khi import:

- `categories`: danh mục sản phẩm như điện thoại, laptop, tablet, TV, tai nghe, phụ kiện.
- `brands`: thương hiệu sản phẩm.
- `products`: thông tin sản phẩm, giá, tồn kho, hình ảnh, đánh giá.
- `product_specs`: thông số kỹ thuật chi tiết của sản phẩm.

## Giới thiệu mô hình MVC

Dự án được tổ chức theo mô hình MVC để tách rõ dữ liệu, xử lý nghiệp vụ và giao diện:

- Model: thư mục `models/`, định nghĩa các bảng dữ liệu như user, product, category, brand, cart và order.
- View: thư mục `views/`, chứa template Jinja2 hiển thị giao diện người dùng và trang quản trị.
- Controller: thư mục `controllers/`, chứa router FastAPI và logic xử lý request/response cho từng nhóm chức năng.
- DAO: thư mục `dao/`, chứa các hàm truy cập dữ liệu cho sản phẩm, người dùng, giỏ hàng và đơn hàng.

Luồng xử lý request:

```text
User request -> Controller -> DAO -> Model/Database -> View -> HTML response
```

## Chức năng chính

- Hiển thị trang chủ, danh sách sản phẩm và chi tiết sản phẩm.
- Tìm kiếm, lọc và phân loại sản phẩm theo danh mục/thương hiệu.
- Import dữ liệu sản phẩm Best Buy từ `products.json`.
- Đăng ký, đăng nhập, đăng xuất và xem thông tin tài khoản.
- Thêm sản phẩm vào giỏ hàng và thanh toán đơn hàng.
- Xem lịch sử đơn hàng và chi tiết đơn hàng.
- Trang quản trị để quản lý sản phẩm, danh mục, thương hiệu, người dùng và đơn hàng.
- Gợi ý sản phẩm và chatbot tư vấn sản phẩm.

## Cấu trúc repo

```text
Btl_Web/
├── main.py                         # Điểm khởi chạy ứng dụng FastAPI
├── config.py                       # Cấu hình ứng dụng, database, session, helper format
├── database.py                     # Kết nối SQLite và cấu hình SQLAlchemy
├── seed.py                         # Seed dữ liệu mẫu ban đầu
├── import_bestbuy.py               # Import dữ liệu sản phẩm từ Best Buy/products.json
├── products.json                   # Dữ liệu sản phẩm Best Buy
├── recommender.py                  # Logic gợi ý/tư vấn sản phẩm
├── requirements.txt                # Danh sách thư viện Python cần cài
├── dao/                            # DAO: truy vấn dữ liệu sản phẩm, user, giỏ hàng, đơn hàng
├── controllers/                    # Controller: router và xử lý nghiệp vụ
│   ├── admin_controller.py         # Quản trị sản phẩm, danh mục, thương hiệu, đơn hàng, user
│   ├── auth_controller.py          # Đăng ký, đăng nhập, đăng xuất, profile
│   ├── cart_controller.py          # Giỏ hàng
│   ├── order_controller.py         # Đặt hàng và lịch sử đơn hàng
│   ├── product_controller.py       # Danh sách và chi tiết sản phẩm
│   ├── home_controller.py          # Trang chủ
│   ├── recommend_controller.py     # API gợi ý sản phẩm/chatbot
│   └── catalog_helpers.py          # Helper lọc/sắp xếp catalog
├── models/                         # Model: ánh xạ bảng dữ liệu
│   ├── user.py
│   ├── product.py
│   ├── category.py
│   ├── brand.py
│   ├── cart.py
│   └── order.py
├── views/                          # View: template Jinja2
│   ├── admin/                      # Giao diện quản trị
│   ├── partials/                   # Template dùng lại
│   ├── base.html
│   ├── home.html
│   ├── products.html
│   ├── product_detail.html
│   ├── cart.html
│   ├── checkout.html
│   ├── login.html
│   └── register.html
├── static/                         # CSS, JavaScript, hình ảnh
│   ├── css/
│   ├── js/
│   └── images/
└── README.md                       # Tài liệu mô tả và hướng dẫn chạy dự án
```

## Cách chạy trên Windows

1. Mở PowerShell tại thư mục dự án:

```powershell
cd "C:\Users\ASUS\Documents\New project\Btl_Web"
```

Hoặc tìm thư mục dự án rồi chọn `Open in Terminal`.

Minh họa: https://github.com/user-attachments/assets/c347a392-d403-41b5-bd4f-ca535f965816

2. Tạo môi trường ảo:

```powershell
python -m venv .venv
```

3. Kích hoạt môi trường ảo:

```powershell
.\.venv\Scripts\Activate.ps1
```

Nếu PowerShell chặn script, chạy lệnh này một lần rồi kích hoạt lại:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

4. Cài thư viện:

```powershell
pip install -r requirements.txt
```

5. Chạy web:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Ở lần chạy đầu tiên, ứng dụng sẽ tự đọc `products.json`, lọc các sản phẩm công nghệ bằng `import_bestbuy.py`, rồi tạo database SQLite `techworld.db`. Vì vậy không cần chạy `python import_bestbuy.py` thủ công trước khi mở web.

6. Mở trình duyệt:

```text
http://127.0.0.1:8000
```

## Tài khoản mẫu

- Admin: `admin@techworld.vn` / `admin123`
- Người dùng demo: `user@techworld.vn` / `user123`

## Ghi chú

Database SQLite `techworld.db` được tạo khi chạy ứng dụng/import dữ liệu. File database local chỉ phục vụ phát triển và demo, không nên dùng trực tiếp cho môi trường production.
