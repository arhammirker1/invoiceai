# main.py - Fixed FastAPI Application Entry Point
# ============================================================================

import os
import asyncio
import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Redis and Celery
redis_client = redis.from_url(settings.REDIS_URL)
celery_app = Celery('invoice_processor', broker=settings.REDIS_URL, backend=settings.REDIS_URL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)


@app.middleware("http")
async def add_coop_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    return response

# Security
security = HTTPBearer()

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for better error logging"""
    logger.error(f"Unhandled exception on {request.method} {request.url}: {str(exc)}")
    logger.error(f"Full traceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

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
# Health Check
# ============================================================================
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": str(asyncio.get_event_loop().time())}

# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.options("/api/auth/login")
async def options_login():
    """Handle CORS preflight for login"""
    return JSONResponse(content={"message": "OK"})

@app.post("/api/auth/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Handle login requests (Google OAuth or Magic Link)"""
    try:
        logger.info(f"🔐 Login attempt with provider: {request.provider}")
        logger.info(f"Request data: provider={request.provider}, has_token={bool(request.token)}, email={request.email}")
        
        auth_service = AuthService()
        
        if request.provider == "google":
            if not request.token:
                logger.error("❌ No Google token provided")
                raise HTTPException(
                    status_code=400, 
                    detail="Google token is required"
                )
            
            logger.info("🔄 Processing Google login...")
            result = await auth_service.google_login(request.token, db)
            logger.info(f"✅ Google login successful for user: {result['user']['email']}")
            
            return result
            
        elif request.provider == "magic_link":
            if not request.email:
                logger.error("❌ No email provided for magic link")
                raise HTTPException(
                    status_code=400, 
                    detail="Email is required for magic link"
                )
            
            logger.info(f"📧 Sending magic link to: {request.email}")
            result = await auth_service.send_magic_link(request.email, db)
            
            return JSONResponse(content=result)
            
        else:
            logger.error(f"❌ Invalid provider: {request.provider}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid provider. Must be 'google' or 'magic_link'"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"Authentication failed: {str(e)}"
        )

@app.get("/api/auth/verify")
async def verify_magic_link(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify magic link token"""
    try:
        logger.info(f"🔗 Verifying magic link token...")
        auth_service = AuthService()
        result = await auth_service.verify_magic_link(token, db)
        logger.info("✅ Magic link verification successful")
        return result
    except Exception as e:
        logger.error(f"❌ Magic link verification error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# Invoice Processing Endpoints
# ============================================================================

@app.post("/api/invoices/upload", response_model=List[InvoiceUploadResponse])
async def upload_invoices(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload and queue invoices for processing"""
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

@app.get("/api/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's invoices"""
    result = await db.execute(
        select(Invoice)
        .where(Invoice.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(Invoice.created_at.desc())
    )
    invoices = result.scalars().all()
    return [InvoiceResponse.model_validate(invoice) for invoice in invoices]

@app.get("/api/invoices/download/{invoice_id}")
async def download_excel(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download processed Excel file"""
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

# ============================================================================
# Payment Endpoints
# ============================================================================

@app.post("/api/payments/create-checkout-session")
async def create_checkout_session(
    plan_type: str,
    current_user: User = Depends(get_current_user)
):
    """Create Stripe checkout session"""
    payment_service = PaymentService()
    return await payment_service.create_checkout_session(current_user, plan_type)

@app.post("/api/payments/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Stripe webhooks"""
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
    """List all users (admin only)"""
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserResponse.model_validate(user) for user in users]

@app.get("/api/admin/usage")
async def get_usage_stats(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get usage statistics (admin only)"""
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

@app.get("/api/invoices/status/{invoice_id}")
async def get_invoice_status(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get invoice processing status"""
    invoice = await db.get(Invoice, invoice_id)
    if not invoice or invoice.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return InvoiceResponse.model_validate(invoice)

# ============================================================================
# Test Endpoint for Debugging
# ============================================================================

@app.get("/api/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {
        "message": "API is working!",
        "timestamp": str(asyncio.get_event_loop().time()),
        "settings": {
            "database_url": settings.DATABASE_URL[:50] + "...",
            "frontend_url": settings.FRONTEND_URL,
            "google_client_id": settings.GOOGLE_CLIENT_ID[:20] + "..."
        }
    }

# Root endpoint for testing
@app.get("/")
async def read_root():
    """Root endpoint"""
    return {"message": "InvoiceAI API is running", "version": "1.0.0"}
