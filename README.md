# TechWorld - Btl_Web

Web bán hàng công nghệ dùng FastAPI, Jinja2, SQLAlchemy và SQLite.

## Cách chạy trên Windows

1. Mở PowerShell tại thư mục dự án:

```powershell
Dùng lệnh cd + path để trỏ đến folder hoặc tìm vị trí bằng chuột phải <img width="763" height="700" alt="image" src="https://github.com/user-attachments/assets/c347a392-d403-41b5-bd4f-ca535f965816" />

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
- Người dùng demo: `user@techworld.vn` / `user123`
