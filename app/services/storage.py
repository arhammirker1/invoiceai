# services/storage.py - File Storage Service
# ============================================================================

import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings

class StorageService:
    def __init__(self):
        # Ensure directories exist
        Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        Path(settings.EXCEL_DIR).mkdir(parents=True, exist_ok=True)
    
    async def save_upload(self, file: UploadFile, user_id: int) -> str:
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = Path(settings.UPLOAD_DIR) / str(user_id) / unique_filename
        
        # Create user directory
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return str(file_path)
    
    def get_excel_path(self, invoice_id: int, filename: str) -> str:
        excel_filename = f"{Path(filename).stem}_{invoice_id}.xlsx"
        return str(Path(settings.EXCEL_DIR) / excel_filename)