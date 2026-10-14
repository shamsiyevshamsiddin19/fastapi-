# 🚀 FastAPI Blog API (PostgreSQL + JWT + Alembic)

FastAPI asosida yaratilgan zamonaviy va xavfsiz RESTful Blog API backend loyihasi.

## 📌 Xususiyatlari
- **FastAPI**: Yuqori tezlikdagi asinxron REST API.
- **SQLAlchemy & PostgreSQL**: Ma'lumotlar bazasi bilan ORM orqali ishlash.
- **Alembic**: Database migratsiyalar tizimi.
- **JWT Autentifikatsiya**: OAuth2 Password Flow orqali xavfsiz access tokenlar.
- **Rollar va Himoya**: Postlarni faqat egasi tahrirlashi/o'chirishi mumkin (`403 Forbidden`).
- **Pydantic v2**: Kuchli ma'lumotlar validatsiyasi va serializatsiya.
- **AWS EC2 Deploy**: Gunicorn + Uvicorn + Nginx + Systemd production konfiguratsiyasi.

---

## 🛠 O'rnatish va Ishga tushirish (Lokal)

### 1. Repozitoriyani klonlash:
```bash
git clone https://github.com/shamsiyevshamsiddin19/fastapi-.git
cd fastapi-
```

### 2. Virtual muhit yaratish va faollashtirish:
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Bog'liqliklarni o'rnatish:
```bash
pip install -r requirements.txt
```

### 4. Muhit o'zgaruvchilari (.env):
`.env.example` dan `.env` fayl yarating va PostgreSQL ma'lumotlarini kiriting:
```bash
cp .env.example .env
```

### 5. Migratsiyalarni qo'llash:
```bash
alembic upgrade head
```

### 6. Serverni ishga tushirish:
```bash
uvicorn app.main:app --reload
```

Brauzerda:
- API Root: `http://127.0.0.1:8000/`
- Swagger UI (Hujjatlar): `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
