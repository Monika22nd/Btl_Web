# TechWorld - Btl_Web

Web bán hàng công nghệ dùng FastAPI, Jinja2, SQLAlchemy và SQLite.

## Cách chạy trên Windows

1. Mở PowerShell tại thư mục dự án:

```powershell
cd "C:\Users\ASUS\Documents\New project\Btl_Web"
```

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

6. Mở trình duyệt:

```text
http://127.0.0.1:8000
```

## Tài khoản mẫu

- Admin: `admin@techworld.vn` / `admin123`
- Người dùng demo: `demo@techworld.vn` / `demo123`

## Ghi chú

Database SQLite `techworld.db` sẽ được tạo và seed dữ liệu mẫu tự động khi chạy lần đầu nếu chưa có danh mục nào.
