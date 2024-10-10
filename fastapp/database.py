from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from fastapp.core import config

SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{config.POSTGRESQL_USER}:{config.POSTGRESQL_PASSWORD}@{config.POSTGRESQL_HOST}:{config.POSTGRESQL_PORT}/{config.POSTGRESQL_DATABASE}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_non_gen() -> Session:
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()