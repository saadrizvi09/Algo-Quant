# database.py
from sqlmodel import SQLModel, create_engine
from dotenv import load_dotenv 
import os

load_dotenv() 

database_url = os.environ.get("DATABASE_URL")

engine = create_engine(
    database_url, 
    echo=True,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)