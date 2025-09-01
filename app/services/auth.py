# services/auth.py - Fixed Authentication Service
# ============================================================================

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import httpx
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.config import settings
from app.services.email import EmailService

class AuthService:
    def __init__(self):
        self.email_service = EmailService()
    
    async def google_login(self, token: str, db: AsyncSession) -> dict:
        """Handle Google OAuth login with proper error handling"""
        try:
            print(f"Received Google token: {token[:50]}...")
            
            # Verify token using Google's tokeninfo endpoint
            user_info = await self._verify_google_token(token)
            print(f"Google user info: {user_info}")

            # Find existing user by Google ID first
            result = await db.execute(select(User).where(User.google_id == user_info['sub']))
            user = result.scalar_one_or_none()
            
            # If no user found by Google ID, try by email
            if not user:
                result = await db.execute(select(User).where(User.email == user_info['email']))
                user = result.scalar_one_or_none()
                
                # Update existing user with Google ID if found
                if user:
                    user.google_id = user_info['sub']
                    if not user.name and user_info.get('name'):
                        user.name = user_info['name']

            # Create new user if none exists
            if not user:
                trial_end = datetime.utcnow() + timedelta(days=14)
                user = User(
                    email=user_info['email'],
                    google_id=user_info['sub'],
                    name=user_info.get('name', ''),
                    trial_start=datetime.utcnow(),
                    trial_end=trial_end,
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
    
    async def _verify_google_token(self, token: str) -> Dict[str, Any]:
        """Verify Google ID token using Google's tokeninfo API"""
        async with httpx.AsyncClient() as client:
            try:
                # Use Google's tokeninfo endpoint to verify the token
                response = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={token}",
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    error_detail = response.text
                    print(f"Google API error response: {error_detail}")
                    raise Exception(f"Google token verification failed: {error_detail}")
                
                user_info = response.json()
                
                # Verify the token is for your app
                if user_info.get('aud') != settings.GOOGLE_CLIENT_ID:
                    raise Exception(f"Token audience mismatch. Expected: {settings.GOOGLE_CLIENT_ID}, Got: {user_info.get('aud')}")
                
                # Check if token is expired
                exp = int(user_info.get('exp', 0))
                if exp < datetime.utcnow().timestamp():
                    raise Exception("Token has expired")
                
                # Return verified user info
                return {
                    'sub': user_info['sub'],
                    'email': user_info['email'],
                    'name': user_info.get('name', ''),
                    'picture': user_info.get('picture')
                }
                
            except httpx.TimeoutException:
                raise Exception("Google API timeout - please try again")
            except httpx.RequestError as e:
                raise Exception(f"Network error contacting Google: {str(e)}")
            except json.JSONDecodeError:
                raise Exception("Invalid response from Google API")
    
    async def send_magic_link(self, email: str, db: AsyncSession) -> dict:
        """Send magic link for email authentication"""
        try:
            # Find or create user
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if not user:
                trial_end = datetime.utcnow() + timedelta(days=14)
                user = User(
                    email=email,
                    trial_start=datetime.utcnow(),
                    trial_end=trial_end,
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
