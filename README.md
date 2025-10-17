# InvoiceAI (In - Progress)

AI-powered invoice processing application built with FastAPI.

## Features

- Upload and process invoice images/PDFs
- Extract data using OCR and AI
- Export to Excel
- User authentication with Google OAuth
- Real-time processing with Celery
- Payment processing with Stripe

## Tech Stack

- **Backend**: FastAPI, PostgreSQL, Redis, Celery
- **AI/ML**: OpenAI API, Tesseract OCR
- **Authentication**: Google OAuth 2.0
- **Payment**: Stripe
- **Email**: SendGrid
- **Deployment**: Nginx, systemd, Let's Encrypt

## Installation

See deployment documentation for production setup.

## Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run development server
uvicorn main:app --reload
