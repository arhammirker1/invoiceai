# schemas/auth.py - Updated Authentication Schemas
# ============================================================================
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any

class LoginRequest(BaseModel):
    provider: str  # "google" or "magic_link"
    token: Optional[str] = None  # Google token
    email: Optional[EmailStr] = None  # Email for magic link

class UserData(BaseModel):
    id: int
    email: str
    name: Optional[str]
    plan: str
    credits: int
    trial_end: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserData

class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    plan: str
    credits_balance: int
    trial_end: Optional[datetime]
    
    class Config:
        from_attributes = True
