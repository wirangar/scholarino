from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import declarative_base

# A single Base for all database models
Base = declarative_base()

class UserDB(Base):
    """SQLAlchemy model for storing user profile information."""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=True)
    age = Column(Integer, nullable=True)
    country = Column(String(100), nullable=True)
    field_of_study = Column(String(100), nullable=True)
    email = Column(String, nullable=True)
    language = Column(String(10), default="en", nullable=False)
    preferences = Column(Text, default="{}", nullable=False) # Stored as a JSON string

class News(Base):
    """SQLAlchemy model for news articles."""
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    file = Column(String, nullable=True)
    timestamp = Column(String, nullable=False)
