# ============================================================================
# main.py - FastAPI Application Entry Point
# ============================================================================

import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import redis.asyncio as redis
from celery import Celery

from app.core.config import settings
from app.core.database import get_db, init_db
from app.models.user import User
from app.models.invoice import Invoice, InvoiceStatus
from app.services.auth import AuthService
from app.services.storage import StorageService
from app.services.email import EmailService
from app.services.payment import PaymentService
from app.tasks.invoice_processor import process_invoice_task
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.invoice import InvoiceResponse, InvoiceUploadResponse
from app.schemas.user import UserResponse

# Initialize Redis and Celery
redis_client = redis.from_url(settings.REDIS_URL)
celery_app = Celery('invoice_processor', broker=settings.REDIS_URL, backend=settings.REDIS_URL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await redis_client.close()

app = FastAPI(
    title="InvoiceAI API",
    description="AI-powered invoice processing API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    auth_service = AuthService()
    user = await auth_service.get_current_user(credentials.credentials, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user

# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService()
    
    if request.provider == "google":
        return await auth_service.google_login(request.token, db)
    elif request.provider == "magic_link":
        return await auth_service.send_magic_link(request.email, db)
    
    raise HTTPException(status_code=400, detail="Invalid login provider")

@app.post("/api/auth/verify-magic-link")
async def verify_magic_link(token: str, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService()
    return await auth_service.verify_magic_link(token, db)

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse.from_orm(current_user)

# ============================================================================
# Invoice Processing Endpoints
# ============================================================================

@app.post("/api/invoices/upload", response_model=List[InvoiceUploadResponse])
async def upload_invoices(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if len(files) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 files allowed")
    
    # Check user credits
    if current_user.credits_balance < len(files) and current_user.plan == "credit_pack":
        raise HTTPException(status_code=402, detail="Insufficient credits")
    
    storage_service = StorageService()
    responses = []
    
    for file in files:
        # Validate file type
        if not file.content_type in ["application/pdf", "image/jpeg", "image/png"]:
            continue
            
        # Save file
        file_path = await storage_service.save_upload(file, current_user.id)
        
        # Create invoice record
        invoice = Invoice(
            user_id=current_user.id,
            filename=file.filename,
            original_path=file_path,
            status=InvoiceStatus.PENDING
        )
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        
        # Queue processing task
        process_invoice_task.delay(invoice.id)
        
        responses.append(InvoiceUploadResponse(
            invoice_id=invoice.id,
            filename=file.filename,
            status="queued"
        ))
    
    return responses

@app.get("/api/invoices/status/{invoice_id}")
async def get_invoice_status(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    invoice = await db.get(Invoice, invoice_id)
    if not invoice or invoice.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return InvoiceResponse.from_orm(invoice)

@app.get("/api/invoices/download/{invoice_id}")
async def download_excel(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    invoice = await db.get(Invoice, invoice_id)
    if not invoice or invoice.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.status != InvoiceStatus.COMPLETED or not invoice.excel_path:
        raise HTTPException(status_code=400, detail="Excel file not ready")
    
    return FileResponse(
        invoice.excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"{invoice.filename.rsplit('.', 1)[0]}.xlsx"
    )

@app.get("/api/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    result = await db.execute(
        select(Invoice)
        .where(Invoice.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(Invoice.created_at.desc())
    )
    invoices = result.scalars().all()
    return [InvoiceResponse.from_orm(invoice) for invoice in invoices]

# ============================================================================
# Payment Endpoints (Stripe)
# ============================================================================

@app.post("/api/payments/create-checkout-session")
async def create_checkout_session(
    plan_type: str,
    current_user: User = Depends(get_current_user)
):
    payment_service = PaymentService()
    return await payment_service.create_checkout_session(current_user, plan_type)

@app.post("/api/payments/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payment_service = PaymentService()
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    await payment_service.handle_webhook(payload, sig_header, db)
    return {"status": "success"}

# ============================================================================
# Admin Endpoints
# ============================================================================

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@app.get("/api/admin/users")
async def list_users(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserResponse.from_orm(user) for user in users]

@app.get("/api/admin/usage")
async def get_usage_stats(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select, func
    
    # Total users
    user_count = await db.scalar(select(func.count(User.id)))
    
    # Total invoices processed
    invoice_count = await db.scalar(select(func.count(Invoice.id)))
    
    # This month's invoices
    from datetime import datetime, timedelta
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_invoices = await db.scalar(
        select(func.count(Invoice.id)).where(Invoice.created_at >= start_of_month)
    )
    
    return {
        "total_users": user_count,
        "total_invoices": invoice_count,
        "monthly_invoices": monthly_invoices,
        "success_rate": 99.2  # Calculate from actual data
    }
