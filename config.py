import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "fallback-secret-key-12345"

    # Render कडून मिळणारा postgres:// हा URL SQLAlchemy साठी postgresql:// मध्ये कन्व्हर्ट करणे आवश्यक असते
    database_url = os.environ.get("DATABASE_URL")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url or "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
