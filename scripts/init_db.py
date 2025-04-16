"""
Initialize Supabase/Postgres DB: create all tables from SQLAlchemy models.
Run: python scripts/init_db.py
"""
from app.db import engine
from app.models import Base

def main():
    print("Creating all tables in Supabase/Postgres DB...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    main()
