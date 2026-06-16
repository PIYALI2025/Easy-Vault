from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Get DB URL from .env, default to local sqlite if not set
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./cloud_vault.db"

# When deploying to Vercel, the default root SQLite file is read-only.
# Move it to /tmp where writes are permitted.
if "VERCEL" in os.environ and SQLALCHEMY_DATABASE_URL.startswith("sqlite:///."):
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