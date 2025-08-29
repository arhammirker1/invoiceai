# schemas/invoice.py - Invoice Schemas
# ============================================================================

from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from app.models.invoice import InvoiceStatus

class InvoiceUploadResponse(BaseModel):
    invoice_id: int
    filename: str
    status: str

class InvoiceResponse(BaseModel):
    id: int
    filename: str
    status: InvoiceStatus
    invoice_number: Optional[str]
    vendor_name: Optional[str]
    invoice_date: Optional[datetime]
    total_amount: Optional[Decimal]
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class LineItemResponse(BaseModel):
    description: str
    quantity: Optional[Decimal]
    unit_price: Optional[Decimal]
    total_amount: Decimal