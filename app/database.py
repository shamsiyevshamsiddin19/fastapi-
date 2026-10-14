from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

# PostgreSQL ulanishi uchun URL
db_url = settings.database_url
if db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

# Engine - PostgreSQL ga ulanish
engine = create_engine(db_url)

# SessionLocal - har bir so'rov uchun alohida DB session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base - barcha SQLAlchemy modellar shu classdan meros oladi
Base = declarative_base()


# Dependency - har bir endpoint uchun DB session yaratish va yopish
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
