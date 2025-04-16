import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# Configure logging (works both locally and on Vercel)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")

if not SUPABASE_URL:
    logger.error("SUPABASE_DB_URL environment variable not set. Please add your Supabase Postgres connection string to .env.")
    raise RuntimeError("SUPABASE_DB_URL environment variable not set. Please add your Supabase Postgres connection string to .env.")

# Mask the URL for logs (show protocol and host only)
def mask_url(url):
    if not url:
        return "(none)"
    try:
        from urllib.parse import urlparse
        parts = urlparse(url)
        return f"{parts.scheme}://{parts.hostname}/..."
    except Exception:
        return url[:15] + "..."

logger.info(f"SUPABASE_DB_URL detected: {mask_url(SUPABASE_URL)}")

try:
    engine = create_engine(
        SUPABASE_URL,
        poolclass=NullPool,  # serverless-friendly
        connect_args={"sslmode": "require"}  # Supabase requires SSL
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("SQLAlchemy engine created successfully for Supabase/Postgres.")
except Exception as e:
    logger.error(f"Failed to create SQLAlchemy engine: {e}")
    raise
