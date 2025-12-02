from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import config

# Create database if not exists (hack for dev)
import pymysql
try:
    conn = pymysql.connect(
        host=config.DB_HOST, 
        user=config.DB_USER, 
        password=config.DB_PASSWORD,
        port=int(config.DB_PORT)
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.close()
except Exception as e:
    print(f"Warning: Could not check/create database: {e}")

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
