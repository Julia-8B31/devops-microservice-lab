from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings
import time
import logging

logger = logging.getLogger("uvicorn.error")

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def wait_for_db(max_retries=10, delay=3):
    """Ожидание доступности базы данных при старте сервиса"""
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                logger.info("Successfully connected to the database.")
                return True
        except Exception as e:
            logger.warning(f"Database unavailable on attempt {attempt}/{max_retries}: {e}")
            time.sleep(delay)
    raise RuntimeError("Failed to connect to the database after several attempts.")
