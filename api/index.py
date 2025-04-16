"""
Vercel Python Serverless Entrypoint for Flask app.
All routes will be available under /api/ (e.g., /api/, /api/test-candles)
"""
from app import create_app

app = create_app()
