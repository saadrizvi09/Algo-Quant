# models.py
from typing import Optional
from sqlmodel import Field, SQLModel

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True) 
    name: Optional[str] = None
    hashed_password: str  # <--- CRITICAL ADDITION