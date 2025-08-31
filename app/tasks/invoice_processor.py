# tasks/invoice_processor.py - Celery Task for Invoice Processing
# ============================================================================

import os
import asyncio

from pathlib import Path
import pdfplumber
import camelot
import pytesseract
import cv2
import numpy as np
from PIL import Image
import openpyxl
from openpyxl.drawing import image
import re
from datetime import datetime
from decimal import Decimal
from app.core.config import settings   
from celery import Celery

celery_app = Celery('invoice_processor', broker=settings.REDIS_URL, backend=settings.REDIS_URL)

@celery_app.task(bind=True)
def process_invoice_task(self, invoice_id: int):
    """
    Process uploaded invoice through the AI pipeline:
    1. Convert PDF to images if needed
    2. Preprocess images (deskew, binarize)
    3. Try table extraction with pdfplumber/Camelot
    4. Fallback to Tesseract OCR
    5. Extract structured data
    6. Generate Excel file
    7. Send email notification
    """
    
    # This would run the processing pipeline
    asyncio.run(process_invoice_async(invoice_id))

async def process_invoice_async(invoice_id: int):
    from app.core.database import async_session_maker
    from app.models.invoice import Invoice, InvoiceStatus
    from app.services.email import EmailService
    from app.services.storage import StorageService
    
    async with async_session_maker() as db:
        invoice = await db.get(Invoice, invoice_id)
        if not invoice:
            return
        
        try:
            # Update status to processing
            invoice.status = InvoiceStatus.PROCESSING
            await db.commit()
            
            processor = InvoiceProcessor()
            result = await processor.process(invoice.original_path)
            
            # Update invoice with extracted data
            invoice.invoice_number = result.get('invoice_number')
            invoice.vendor_name = result.get('vendor_name')
            invoice.invoice_date = result.get('invoice_date')
            invoice.total_amount = result.get('total_amount')
            
            # Generate Excel file
            storage_service = StorageService()
            excel_path = storage_service.get_excel_path(invoice.id, invoice.filename)
            
            excel_generator = ExcelGenerator()
            await excel_generator.create_excel(result, excel_path, invoice.original_path)
            
            invoice.excel_path = excel_path
            invoice.status = InvoiceStatus.COMPLETED
            await db.commit()
            
            # Send email notification
            email_service = EmailService()
            await email_service.send_excel_file(
                invoice.user.email,
                excel_path,
                invoice.filename
            )
            
        except Exception as e:
            invoice.status = InvoiceStatus.FAILED
            invoice.error_message = str(e)
            await db.commit()
            print(f"Error processing invoice {invoice_id}: {e}")
