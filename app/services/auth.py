# services/auth.py - Authentication Service
# ============================================================================

from datetime import datetime, timedelta
from typing import Optional
import jwt
from authlib.integrations.httpx_client import AsyncOAuth2Client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.config import settings
from app.services.email import EmailService
from google.oauth2 import id_token
from google.auth.transport import requests


class AuthService:
    def __init__(self):
        self.email_service = EmailService()
    
   async def google_login(self, token: str, db: AsyncSession) -> dict:
    try:
        # Verify the ID token from frontend
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
    except Exception as e:
        raise Exception(f"Invalid Google token: {e}")

    # Extract the user info
    user_info = {
        "id": idinfo["sub"],
        "email": idinfo["email"],
        "name": idinfo.get("name")
    }

    # Find or create user in DB
    result = await db.execute(select(User).where(User.google_id == user_info['id']))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=user_info['email'],
            google_id=user_info['id'],
            name=user_info.get('name'),
            trial_start=datetime.utcnow(),
            trial_end=datetime.utcnow() + timedelta(days=14),
            credits_balance=0
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

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
            "credits": user.credits_balance
        }
    }
    
    async def send_magic_link(self, email: str, db: AsyncSession) -> dict:
        # Find or create user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                email=email,
                trial_start=datetime.utcnow(),
                trial_end=datetime.utcnow() + timedelta(days=14),
                credits_balance=0
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        # Generate magic link token
        token = self._create_access_token({"sub": str(user.id), "magic": True}, expires_delta=timedelta(minutes=15))
        magic_link = f"{settings.FRONTEND_URL}/auth/verify?token={token}"
        
        # Send email
        await self.email_service.send_magic_link(email, magic_link)
        
        return {"message": "Magic link sent to your email"}
    
    def _create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    
    async def get_current_user(self, token: str, db: AsyncSession) -> Optional[User]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = int(payload.get("sub"))
            
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except jwt.PyJWTError:
            return None
