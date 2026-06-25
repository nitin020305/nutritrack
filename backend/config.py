import os
from datetime import timedelta
from dotenv import load_dotenv

# Load from infra/.env (one level up from backend/)
_env_path = os.path.join(os.path.dirname(__file__), "..", "infra", ".env")
load_dotenv(_env_path)

class Config:
    # Core
    SECRET_KEY      = os.getenv("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY  = os.getenv("JWT_SECRET_KEY", "dev-jwt")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///nutritrack.db")

    # JWT
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(days=int(os.getenv("ACCESS_TOKEN_EXPIRY_DAYS", 7)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Mail
    MAIL_SERVER         = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT           = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS        = os.getenv("MAIL_USE_TLS", "1") == "1"
    MAIL_USERNAME       = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD       = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "NutriTrack <noreply@nutritrack.com>")

    # USDA
    USDA_API_KEY  = os.getenv("USDA_API_KEY", "DEMO_KEY")
    USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

    # Admin
    ADMIN_EMAIL      = os.getenv("ADMIN_EMAIL", "admin@nutritrack.com")
    ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "admin-secret")

    # App
    FRONTEND_URL               = os.getenv("FRONTEND_URL", "http://127.0.0.1:5000")
    EMAIL_TOKEN_EXPIRY_HOURS   = int(os.getenv("EMAIL_TOKEN_EXPIRY_HOURS", 24))
    RESET_TOKEN_EXPIRY_HOURS   = int(os.getenv("RESET_TOKEN_EXPIRY_HOURS", 1))

class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SUPPRESS_SEND = False   # Don't actually send emails in dev

class ProductionConfig(Config):
    DEBUG = False
    MAIL_SUPPRESS_SEND = False

config = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}
