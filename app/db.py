import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_DB_URL environment variable not set. Please add your Supabase Postgres connection string to .env.")

engine = create_engine(
    SUPABASE_URL,
    poolclass=NullPool,  # serverless-friendly
    connect_args={"sslmode": "require"}  # Supabase requires SSL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
