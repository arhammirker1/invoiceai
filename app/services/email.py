# services/email.py - Email Service (SendGrid)
# ============================================================================

import sendgrid
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from app.core.config import settings
import base64

class EmailService:
    def __init__(self):
        self.sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
    
    async def send_magic_link(self, email: str, magic_link: str):
        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=email,
            subject="Your InvoiceAI Login Link",
            html_content=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #a4c3a2;">Welcome to InvoiceAI!</h2>
                <p>Click the link below to sign in to your account:</p>
                <a href="{magic_link}" style="display: inline-block; padding: 12px 24px; 
                   background-color: #a4c3a2; color: white; text-decoration: none; 
                   border-radius: 8px; margin: 20px 0;">Sign In to InvoiceAI</a>
                <p><small>This link expires in 15 minutes.</small></p>
            </div>
            """
        )
        
        try:
            await self.sg.send(message)
        except Exception as e:
            print(f"Error sending email: {e}")
    
    async def send_excel_file(self, email: str, excel_path: str, original_filename: str):
        # Read Excel file
        with open(excel_path, 'rb') as f:
            excel_data = f.read()
        
        # Create attachment
        encoded_file = base64.b64encode(excel_data).decode()
        attachment = Attachment(
            FileContent(encoded_file),
            FileName(f"{Path(original_filename).stem}.xlsx"),
            FileType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            Disposition("attachment")
        )
        
        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=email,
            subject="Your Processed Invoice - Excel Ready!",
            html_content=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #a4c3a2;">Your Invoice is Ready!</h2>
                <p>Great news! We've successfully processed your invoice: <strong>{original_filename}</strong></p>
                <p>Your structured Excel file is attached to this email.</p>
                <p>You can also download it from your dashboard at any time.</p>
            </div>
            """
        )
        message.attachment = attachment
        
        try:
            await self.sg.send(message)
        except Exception as e:
            print(f"Error sending Excel file: {e}")