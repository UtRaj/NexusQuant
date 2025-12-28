# database/db.py

from sqlmodel import create_engine, SQLModel
from config import config

# PostgreSQL connection string from config (Production Grade)
# Note: Ensure DATABASE_URL is set in .env
engine = create_engine(
    config.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20
)

def init_db():
    from . import models # Ensure models are loaded
    SQLModel.metadata.create_all(engine)
