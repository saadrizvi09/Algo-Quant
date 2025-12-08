# database.py (No changes needed, just keeping it for context)
from sqlmodel import SQLModel, create_engine
from dotenv import load_dotenv 
import os

load_dotenv() 

database_url = os.environ.get("DATABASE_URL")
# Example: "postgresql://user:password@localhost:5432/algoquant_db"

engine = create_engine(database_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)