from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import shutil
from dotenv import load_dotenv

load_dotenv()

# Get DB URL from .env, check for database_url or postgres_url
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./cloud_vault.db"

# Handle deployments on Vercel
if "VERCEL" in os.environ:
    # Fix standard postgres:// scheme to postgresql:// as required by SQLAlchemy
    if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # If using SQLite, copy the pre-seeded local database to /tmp so data is preserved on cold start
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite:///."):
        src_db = "./cloud_vault.db"
        dest_db = "/tmp/cloud_vault.db"
        if not os.path.exists(dest_db) and os.path.exists(src_db):
            try:
                shutil.copy2(src_db, dest_db)
            except Exception as e:
                print(f"Error copying database to /tmp: {e}")
        SQLALCHEMY_DATABASE_URL = "sqlite:////tmp/cloud_vault.db"

# Only pass connect_args for SQLite database connections
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()

# Dependency to get DB session in routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()