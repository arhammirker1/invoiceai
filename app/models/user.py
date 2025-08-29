# models/user.py - User Database Model
# ============================================================================

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    google_id = Column(String, unique=True, nullable=True)
    name = Column(String, nullable=True)
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    plan = Column(String, default="trial")  # trial, monthly, credit_pack
    credits_balance = Column(Integer, default=0)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    invoices = relationship("Invoice", back_populates="user")
    payments = relationship("Payment", back_populates="user")
