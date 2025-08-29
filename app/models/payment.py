
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stripe_charge_id = Column(String, unique=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    type = Column(String, nullable=False)  # subscription, credit_pack
    status = Column(String, nullable=False)  # pending, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="payments")