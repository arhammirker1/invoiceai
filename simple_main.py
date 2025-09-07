# simple_main.py - Simplified FastAPI Application for Quick Testing
# ============================================================================

import os
import asyncio
import logging
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="InvoiceAI API - Simplified",
    description="AI-powered invoice processing API (Simplified Version)",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# ============================================================================
# Health Check
# ============================================================================
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Server is running!"}

# ============================================================================
# Test Endpoints
# ============================================================================
@app.get("/")
async def read_root():
    """Root endpoint"""
    return {
        "message": "InvoiceAI API is running (Simplified Version)", 
        "version": "1.0.0",
        "status": "ready"
    }

@app.get("/api/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {
        "message": "API is working!",
        "timestamp": str(asyncio.get_event_loop().time()),
        "features": [
            "Basic server running",
            "CORS enabled",
            "Ready for development"
        ]
    }

@app.post("/api/test-login")
async def test_login():
    """Test login endpoint for debugging"""
    return {
        "access_token": "test_token_123",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "email": "test@example.com",
            "name": "Test User",
            "plan": "trial",
            "credits": 50
        }
    }

@app.get("/api/debug")
async def debug_endpoint():
    """Debug endpoint to check server status"""
    return {
        "status": "Server is running",
        "message": "Backend is working correctly",
        "timestamp": str(asyncio.get_event_loop().time())
    }

# ============================================================================
# Mock Authentication Endpoints (No Database Required)
# ============================================================================
from pydantic import BaseModel

class LoginRequest(BaseModel):
    provider: str
    token: str = None
    email: str = None

# Google OAuth Configuration
GOOGLE_CLIENT_ID = "782809189336-vufvfm95cumltebfifgnnlkp31529l6s.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"  # From your config.py

@app.post("/api/auth/login")
async def login(request: dict):
    """Handle login requests (Google OAuth or Magic Link)"""
    try:
        logger.info(f"🔐 Login attempt with provider: {request.get('provider')}")
        logger.info(f"Request data: {request}")
        
        provider = request.get('provider')
        if provider == "google":
            token = request.get('token')
            if not token:
                raise HTTPException(
                    status_code=400, 
                    detail="Google token is required"
                )
            
            # Decode the Google JWT token to get real user information
            try:
                import base64
                import json
                
                # Decode the JWT token (without verification for now)
                # JWT format: header.payload.signature
                parts = token.split('.')
                if len(parts) != 3:
                    raise ValueError("Invalid JWT token format")
                
                # Decode the payload (middle part)
                payload = parts[1]
                # Add padding if needed
                payload += '=' * (4 - len(payload) % 4)
                decoded_payload = base64.urlsafe_b64decode(payload)
                user_data = json.loads(decoded_payload)
                
                # Extract user information from the token
                user_email = user_data.get('email', 'unknown@gmail.com')
                user_name = user_data.get('name', 'Google User')
                user_id = user_data.get('sub', 'unknown')
                
                # Create a simple user ID from email
                import hashlib
                user_id = int(hashlib.md5(user_email.encode()).hexdigest()[:8], 16)
                
                logger.info(f"✅ Google login successful for: {user_email}")
                
                return {
                    "access_token": f"google_token_{user_id}",
                    "token_type": "bearer",
                    "user": {
                        "id": user_id,
                        "email": user_email,
                        "name": user_name,
                        "plan": "trial",
                        "credits": 50
                    }
                }
                    
            except Exception as e:
                logger.error(f"Google token processing failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to process Google token: {str(e)}"
                )
            
        elif provider == "magic_link":
            email = request.get('email')
            if not email:
                raise HTTPException(
                    status_code=400, 
                    detail="Email is required for magic link"
                )
            
            # Generate a simple magic link token
            import secrets
            import hashlib
            magic_token = secrets.token_urlsafe(32)
            
            # Store the magic token (in production, store in database)
            # For now, we'll just log it
            logger.info(f"🔗 Magic link generated for {email}: http://localhost:3000/auth/verify?token={magic_token}")
            
            # In a real app, you would send an email here
            # For development, we'll just return the link in the response
            return {
                "message": "Magic link sent! Check your email.",
                "email": email,
                "debug_link": f"http://localhost:3000/auth/verify?token={magic_token}",  # For development only
                "note": "In production, this link would be sent via email"
            }
            
        else:
            raise HTTPException(
                status_code=400, 
                detail="Invalid provider"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Authentication failed: {str(e)}"
        )

@app.get("/api/auth/verify")
async def verify_magic_link(token: str = None):
    """Verify magic link token"""
    if not token:
        raise HTTPException(
            status_code=400,
            detail="Token is required"
        )
    
    # In production, you would verify the token against the database
    # For now, we'll just accept any token and create a user
    try:
        import hashlib
        
        # Create a simple user ID from the token
        user_id = int(hashlib.md5(token.encode()).hexdigest()[:8], 16)
        
        logger.info(f"✅ Magic link verified for token: {token[:10]}...")
        
        return {
            "access_token": f"magic_token_{user_id}",
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": f"user{user_id}@example.com",
                "name": f"Magic Link User {user_id}",
                "plan": "trial",
                "credits": 50
            }
        }
        
    except Exception as e:
        logger.error(f"Magic link verification failed: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired token"
        )

# ============================================================================
# Mock Invoice Endpoints (No Database Required)
# ============================================================================
@app.post("/api/invoices/upload")
async def mock_upload_invoices(files: List[UploadFile] = File(...)):
    """Mock invoice upload endpoint"""
    responses = []
    for file in files:
        responses.append({
            "invoice_id": f"mock_{file.filename}",
            "filename": file.filename,
            "status": "queued",
            "message": "File received (mock processing)"
        })
    return responses

@app.get("/api/invoices")
async def mock_list_invoices():
    """Mock invoice list endpoint"""
    return [
        {
            "id": 1,
            "filename": "sample_invoice.pdf",
            "status": "completed",
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]

@app.get("/api/invoices/status/{invoice_id}")
async def mock_get_invoice_status(invoice_id: str):
    """Mock invoice status endpoint"""
    return {
        "id": invoice_id,
        "filename": "sample_invoice.pdf",
        "status": "completed",
        "message": "Mock status - invoice processed"
    }

# ============================================================================
# Error Handling
# ============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Error on {request.method} {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

if __name__ == "__main__":
    print("🚀 Starting InvoiceAI Simplified Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("❤️  Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
