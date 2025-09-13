from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from settings import settings


username = settings.DB_USERNAME
password = settings.DB_PASSWORD
host = settings.DB_HOST
port = settings.DB_PORT
dbname = settings.DB_NAME

DATABASE_URL = f"postgresql://{username}:{password}@{host}:{port}/{dbname}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_psql():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()