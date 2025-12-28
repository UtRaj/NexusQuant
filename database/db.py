# database/db.py

from sqlmodel import create_engine, SQLModel
from config import config

# PostgreSQL connection string from config (Production Grade)
# Note: Ensure DATABASE_URL is set in .env
engine_params = {}
if "sqlite" not in config.DATABASE_URL:
    engine_params = {
        "pool_size": 10,
        "max_overflow": 20
    }

engine = create_engine(
    config.DATABASE_URL,
    echo=False,
    **engine_params
)

def init_db():
    from . import models # Ensure models are loaded
    SQLModel.metadata.create_all(engine)
