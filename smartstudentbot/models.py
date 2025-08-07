from pydantic import BaseModel, EmailStr, constr
from typing import Optional

class User(BaseModel):
    """
    Pydantic model for validating user data.
    """
    user_id: int
    first_name: constr(min_length=1, max_length=50)
    last_name: Optional[constr(min_length=1, max_length=50)] = None
    age: Optional[int] = None
    country: Optional[constr(min_length=2, max_length=100)] = None
    field_of_study: Optional[constr(min_length=2, max_length=100)] = None
    email: Optional[EmailStr] = None
    language: str = "en"  # Default language
    preferences: Optional[dict] = {}  # For user-specific settings
