# ============================================================================
# core/config.py - Configuration Settings
# ============================================================================

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://invoice_user:N12345123-nn@localhost/invoiceai"
    
    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Authentication
    SECRET_KEY: str = "your-secret-key-change-this"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    GOOGLE_CLIENT_ID: str = "782809189336-vufvfm95cumltebfifgnnlkp31529l6s.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET: str = "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"
    
    # Email
    SENDGRID_API_KEY: str = "your-sendgrid-api-key"
    FROM_EMAIL: str = "noreply@invoiceai.com"
    
    # Stripe
    STRIPE_SECRET_KEY: str = "sk_test_your_stripe_secret_key"
    STRIPE_WEBHOOK_SECRET: str = "whsec_your_webhook_secret"
    
    # Storage
    UPLOAD_DIR: str = "/var/www/invoice-app/storage/uploads"
    EXCEL_DIR: str = "/var/www/invoice-app/storage/excels"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://yourdomain.com"]
    
    class Config:
        env_file = ".env"

settings = Settings()
