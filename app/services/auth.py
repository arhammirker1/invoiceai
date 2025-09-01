# services/auth.py - Fixed Authentication Service
# ============================================================================

from datetime import datetime, timedelta
from typing import Optional
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.config import settings
from app.services.email import EmailService
from google.oauth2 import id_token
from google.auth.transport import requests
import httpx
import json


class AuthService:
    def __init__(self):
        self.email_service = EmailService()
    
    async def google_login(self, token: str, db: AsyncSession) -> dict:
        """Handle Google OAuth login with proper error handling"""
        try:
            # Method 1: Verify using Google's library (recommended)
            try:
                idinfo = id_token.verify_oauth2_token(
                    token,
                    requests.Request(),
                    settings.GOOGLE_CLIENT_ID
                )
                
                # Check if token is for your app
                if idinfo['aud'] != settings.GOOGLE_CLIENT_ID:
                    raise ValueError('Wrong audience')
                    
            except Exception as e:
                print(f"Google library verification failed: {e}")
                # Method 2: Fallback to Google's tokeninfo endpoint
                idinfo = await self._verify_token_with_google_api(token)
        
            # Extract user info
            user_info = {
                "id": idinfo["sub"],
                "email": idinfo["email"],
                "name": idinfo.get("name", ""),
                "picture": idinfo.get("picture")
            }
            
            print(f"Google user info: {user_info}")

            # Find existing user by Google ID first
            result = await db.execute(select(User).where(User.google_id == user_info['id']))
            user = result.scalar_one_or_none()
            
            # If no user found by Google ID, try by email
            if not user:
                result = await db.execute(select(User).where(User.email == user_info['email']))
                user = result.scalar_one_or_none()
                
                # Update existing user with Google ID if found
                if user:
                    user.google_id = user_info['id']
                    if not user.name:
                        user.name = user_info.get('name')

            # Create new user if none exists
            if not user:
                user = User(
                    email=user_info['email'],
                    google_id=user_info['id'],
                    name=user_info.get('name', ''),
                    trial_start=datetime.utcnow(),
                    trial_end=datetime.utcnow() + timedelta(days=14),
                    credits_balance=50,  # Free trial credits
                    plan="trial"
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                print(f"Created new user: {user.id}")
            else:
                await db.commit()
                print(f"Found existing user: {user.id}")
            
            # Generate JWT for your app
            access_token = self._create_access_token({"sub": str(user.id)})
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "plan": user.plan,
                    "credits": user.credits_balance,
                    "trial_end": user.trial_end.isoformat() if user.trial_end else None
                }
            }
            
        except Exception as e:
            print(f"Google login error: {e}")
            raise Exception(f"Authentication failed: {str(e)}")
    
    async def _verify_token_with_google_api(self, token: str) -> dict:
        """Verify token using Google's tokeninfo API as fallback"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
            )
            
            if response.status_code != 200:
                raise Exception("Invalid token from Google API")
                
            data = response.json()
            
            # Verify audience
            if data.get('aud') != settings.GOOGLE_CLIENT_ID:
                raise Exception("Token audience mismatch")
                
            return data
    
    async def send_magic_link(self, email: str, db: AsyncSession) -> dict:
        """Send magic link for email authentication"""
        try:
            # Find or create user
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(
                    email=email,
                    trial_start=datetime.utcnow(),
                    trial_end=datetime.utcnow() + timedelta(days=14),
                    credits_balance=50,
                    plan="trial"
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            
            # Generate magic link token (shorter expiry for security)
            token = self._create_access_token(
                {"sub": str(user.id), "magic": True}, 
                expires_delta=timedelta(minutes=15)
            )
            magic_link = f"{settings.FRONTEND_URL}/auth/verify?token={token}"
            
            # Send email
            await self.email_service.send_magic_link(email, magic_link)
            
            return {"message": "Magic link sent to your email"}
            
        except Exception as e:
            print(f"Magic link error: {e}")
            raise Exception(f"Failed to send magic link: {str(e)}")
    
    async def verify_magic_link(self, token: str, db: AsyncSession) -> dict:
        """Verify magic link token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            
            # Check if it's a magic link token
            if not payload.get("magic"):
                raise Exception("Invalid magic link token")
                
            user_id = int(payload.get("sub"))
            
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                raise Exception("User not found")
            
            # Generate new regular access token
            access_token = self._create_access_token({"sub": str(user.id)})
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "plan": user.plan,
                    "credits": user.credits_balance,
                    "trial_end": user.trial_end.isoformat() if user.trial_end else None
                }
            }
            
        except jwt.ExpiredSignatureError:
            raise Exception("Magic link has expired")
        except jwt.PyJWTError as e:
            raise Exception("Invalid magic link token")
    
    def _create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    
    async def get_current_user(self, token: str, db: AsyncSession) -> Optional[User]:
        """Get current user from JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = int(payload.get("sub"))
            
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except jwt.PyJWTError:
            return None


# API Routes - Add these to your FastAPI router
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.auth import AuthService
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()
auth_service = AuthService()

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Handle login requests (Google OAuth or Magic Link)"""
    try:
        if request.provider == "google":
            if not request.token:
                raise HTTPException(
                    status_code=400, 
                    detail="Google token is required"
                )
            
            result = await auth_service.google_login(request.token, db)
            return result
            
        elif request.provider == "magic_link":
            if not request.email:
                raise HTTPException(
                    status_code=400, 
                    detail="Email is required for magic link"
                )
            
            result = await auth_service.send_magic_link(request.email, db)
            return result
            
        else:
            raise HTTPException(
                status_code=400, 
                detail="Invalid provider"
            )
            
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=400, 
            detail=str(e)
        )

@router.get("/verify")
async def verify_magic_link(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify magic link token"""
    try:
        result = await auth_service.verify_magic_link(token, db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    token: str = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current user information"""
    user = await auth_service.get_current_user(token.credentials, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    return UserResponse.from_orm(user)
