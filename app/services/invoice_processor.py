# services/invoice_processor.py - Core Invoice Processing Logic
# ============================================================================

import io
import fitz  # PyMuPDF
from typing import Dict, List, Any, Optional
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

class InvoiceProcessor:
    def __init__(self):
        self.pytesseract_config = '--oem 3 --psm 6'
    
    async def process(self, file_path: str) -> Dict[str, Any]:
        """Main processing pipeline for invoices"""
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            return await self._process_pdf(file_path)
        elif file_ext in ['.jpg', '.jpeg', '.png']:
            return await self._process_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    async def _process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process PDF invoice using multiple extraction methods"""
        
        # Method 1: Try pdfplumber for text extraction
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract text from all pages
                full_text = ""
                tables = []
                
                for page in pdf.pages:
                    full_text += page.extract_text() or ""
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
                
                # If we got good text extraction, parse it
                if full_text.strip():
                    result = self._extract_data_from_text(full_text)
                    if tables:
                        result['line_items'] = self._parse_tables(tables)
                    return result
        except Exception as e:
            print(f"pdfplumber failed: {e}")
        
        # Method 2: Try Camelot for table extraction
        try:
            tables = camelot.read_pdf(pdf_path, pages='all')
            if tables:
                combined_data = self._process_camelot_tables(tables)
                return combined_data
        except Exception as e:
            print(f"Camelot failed: {e}")
        
        # Method 3: Convert to images and use OCR
        return await self._pdf_to_ocr(pdf_path)
    
    async def _process_image(self, image_path: str) -> Dict[str, Any]:
        """Process image invoice using OCR"""
        
        # Preprocess image
        processed_image = self._preprocess_image(image_path)
        
        # Extract text using Tesseract
        text = pytesseract.image_to_string(processed_image, config=self.pytesseract_config)
        
        return self._extract_data_from_text(text)
    
    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """Preprocess image for better OCR results"""
        
        # Load image
        img = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Deskew
        gray = self._deskew_image(gray)
        
        # Binarize (adaptive threshold)
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Denoise
        denoised = cv2.medianBlur(binary, 3)
        
        return denoised
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Correct skewed scanned documents"""
        
        # Find edges
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None:
            # Calculate average angle
            angles = []
            for rho, theta in lines[:10]:  # Use first 10 lines
                angle = theta * 180 / np.pi - 90
                angles.append(angle)
            
            if angles:
                median_angle = np.median(angles)
                
                # Rotate image if skew is significant
                if abs(median_angle) > 0.5:
                    center = (image.shape[1] // 2, image.shape[0] // 2)
                    rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                    image = cv2.warpAffine(image, rotation_matrix, (image.shape[1], image.shape[0]))
        
        return image
    
    async def _pdf_to_ocr(self, pdf_path: str) -> Dict[str, Any]:
        """Convert PDF to images and run OCR"""
        
        doc = fitz.open(pdf_path)
        full_text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            
            # Convert to OpenCV format
            img_array = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            # Preprocess
            processed = self._preprocess_image_array(img)
            
            # OCR
            text = pytesseract.image_to_string(processed, config=self.pytesseract_config)
            full_text += text + "\n"
        
        doc.close()
        return self._extract_data_from_text(full_text)
    
    def _extract_data_from_text(self, text: str) -> Dict[str, Any]:
        """Extract structured data from raw text using regex patterns"""
        
        result = {
            'invoice_number': None,
            'vendor_name': None,
            'invoice_date': None,
            'total_amount': None,
            'line_items': []
        }
        
        # Extract invoice number
        invoice_patterns = [
            r'invoice\s*#?\s*:?\s*([A-Z0-9\-]+)',
            r'inv\s*#?\s*:?\s*([A-Z0-9\-]+)',
            r'#\s*([A-Z0-9\-]+)',
        ]
        
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['invoice_number'] = match.group(1)
                break
        
        # Extract dates
        date_patterns = [
            r'date:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}-\d{2}-\d{2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1)
                    # Try different date formats
                    for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%m-%d-%Y']:
                        try:
                            result['invoice_date'] = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    if result['invoice_date']:
                        break
                except Exception:
                    continue
        
        # Extract vendor/company name (first line usually)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            # Look for company name in first few lines
            for line in lines[:5]:
                if not re.search(r'invoice|bill|receipt', line, re.IGNORECASE):
                    if len(line) > 3 and not re.match(r'^\d+', line):
                        result['vendor_name'] = line
                        break
        
        # Extract total amount
        amount_patterns = [
            r'total\s*:?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'amount\s*:?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                try:
                    # Take the largest amount found
                    amounts = [float(amt.replace(',', '')) for amt in matches]
                    result['total_amount'] = Decimal(str(max(amounts)))
                    break
                except (ValueError, InvalidOperation):
                    continue
        
        return result
    
    def _parse_tables(self, tables: List[List[List[str]]]) -> List[Dict[str, Any]]:
        """Parse extracted tables into line items"""
        
        line_items = []
        
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            # Try to identify header row
            headers = [str(cell).lower().strip() for cell in table[0]]
            
            # Look for common column patterns
            desc_col = self._find_column_index(headers, ['description', 'item', 'product', 'service'])
            qty_col = self._find_column_index(headers, ['qty', 'quantity', 'amount'])
            price_col = self._find_column_index(headers, ['price', 'rate', 'cost'])
            total_col = self._find_column_index(headers, ['total', 'amount', 'subtotal'])
            
            # Process data rows
            for row in table[1:]:
                if len(row) <= max(filter(None, [desc_col, qty_col, price_col, total_col])):
                    continue
                
                try:
                    item = {
                        'description': str(row[desc_col]) if desc_col is not None else '',
                        'quantity': self._parse_number(row[qty_col]) if qty_col is not None else None,
                        'unit_price': self._parse_number(row[price_col]) if price_col is not None else None,
                        'total_amount': self._parse_number(row[total_col]) if total_col is not None else None
                    }
                    
                    if item['description'].strip():
                        line_items.append(item)
                        
                except (IndexError, ValueError):
                    continue
        
        return line_items
    
    def _find_column_index(self, headers: List[str], keywords: List[str]) -> Optional[int]:
        """Find column index by matching keywords"""
        for i, header in enumerate(headers):
            for keyword in keywords:
                if keyword in header:
                    return i
        return None
    
    def _parse_number(self, value: str) -> Optional[Decimal]:
        """Parse string to decimal number"""
        if not value:
            return None
        
        # Clean the string
        cleaned = re.sub(r'[^\d.-]', '', str(value))
        
        try:
            return Decimal(cleaned) if cleaned else None
        except InvalidOperation:
            return None
