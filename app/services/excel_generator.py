# services/excel_generator.py - Excel File Generation
# ============================================================================

class ExcelGenerator:
    
    async def create_excel(self, data: Dict[str, Any], excel_path: str, original_image_path: str):
        """Generate Excel file with structured data and embedded image"""
        
        workbook = openpyxl.Workbook()
        
        # Sheet 1: Structured Data
        ws1 = workbook.active
        ws1.title = "Invoice Data"
        
        # Header information
        ws1['A1'] = "Invoice Information"
        ws1['A1'].font = openpyxl.styles.Font(bold=True, size=14)
        
        row = 3
        if data.get('invoice_number'):
            ws1[f'A{row}'] = "Invoice Number:"
            ws1[f'B{row}'] = data['invoice_number']
            row += 1
        
        if data.get('vendor_name'):
            ws1[f'A{row}'] = "Vendor:"
            ws1[f'B{row}'] = data['vendor_name']
            row += 1
        
        if data.get('invoice_date'):
            ws1[f'A{row}'] = "Date:"
            ws1[f'B{row}'] = data['invoice_date'].strftime('%Y-%m-%d') if isinstance(data['invoice_date'], datetime) else str(data['invoice_date'])
            row += 1
        
        if data.get('total_amount'):
            ws1[f'A{row}'] = "Total Amount:"
            ws1[f'B{row}'] = f"${data['total_amount']}"
            row += 2
        
        # Line items table
        if data.get('line_items'):
            ws1[f'A{row}'] = "Line Items"
            ws1[f'A{row}'].font = openpyxl.styles.Font(bold=True, size=12)
            row += 1
            
            # Headers
            headers = ['Description', 'Quantity', 'Unit Price', 'Total']
            for col, header in enumerate(headers, 1):
                cell = ws1.cell(row=row, column=col, value=header)
                cell.font = openpyxl.styles.Font(bold=True)
                cell.fill = openpyxl.styles.PatternFill(start_color="E8F5E8", end_color="E8F5E8", fill_type="solid")
            row += 1
            
            # Data rows
            for item in data['line_items']:
                ws1.cell(row=row, column=1, value=item.get('description', ''))
                ws1.cell(row=row, column=2, value=float(item['quantity']) if item.get('quantity') else '')
                ws1.cell(row=row, column=3, value=f"${item['unit_price']}" if item.get('unit_price') else '')
                ws1.cell(row=row, column=4, value=f"${item['total_amount']}" if item.get('total_amount') else '')
                row += 1
        
        # Auto-adjust column widths
        for column in ws1.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws1.column_dimensions[column_letter].width = adjusted_width
        
        # Sheet 2: Original Invoice Image
        ws2 = workbook.create_sheet("Original Invoice")
        
        try:
            # Convert PDF first page to image or load image directly
            if original_image_path.lower().endswith('.pdf'):
                img_path = await self._pdf_to_image(original_image_path)
            else:
                img_path = original_image_path
            
            # Embed image
            img = openpyxl.drawing.image.Image(img_path)
            img.width = 600  # Resize for better fit
            img.height = 800
            ws2.add_image(img, 'A1')
            
        except Exception as e:
            ws2['A1'] = f"Could not embed original invoice: {e}"
        
        # Save workbook
        workbook.save(excel_path)
        workbook.close()
    
    async def _pdf_to_image(self, pdf_path: str) -> str:
        """Convert first page of PDF to image for embedding"""
        
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap()
        
        # Save as temporary image
        img_path = pdf_path.replace('.pdf', '_temp.png')
        pix.save(img_path)
        doc.close()
        
        return img_path