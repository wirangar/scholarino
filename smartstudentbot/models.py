from pydantic import BaseModel, EmailStr, constr, Field
from typing import Optional, List

class RoommatePreferences(BaseModel):
    """Pydantic model for roommate preferences."""
    looking_for_roommate: bool = False
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    smoker: Optional[bool] = None
    notes: Optional[str] = None

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
    points: int = 0
    badges: List[str] = []
    roommate_prefs: RoommatePreferences = Field(default_factory=RoommatePreferences)
