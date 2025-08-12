from pydantic import BaseModel, EmailStr, constr, Field
from typing import Optional, List
from datetime import datetime

from enum import Enum

class GenderPreference(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    ANY = "Any"

class RoommatePreferences(BaseModel):
    """Pydantic model for roommate preferences."""
    looking_for_roommate: bool = False
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    smoker: Optional[bool] = None
    gender_preference: GenderPreference = GenderPreference.ANY
    notes: Optional[str] = None

class User(BaseModel):
    """
    Pydantic model for validating user data.
    """
    user_id: int
    first_name: constr(min_length=1, max_length=50)
    last_name: Optional[constr(min_length=1, max_length=50)] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    country: Optional[constr(min_length=2, max_length=100)] = None
    field_of_study: Optional[constr(min_length=2, max_length=100)] = None
    email: Optional[EmailStr] = None
    language: str = "en"  # Default language
    preferences: Optional[dict] = {}  # For user-specific settings
    points: int = 0
    badges: List[str] = []
    roommate_prefs: RoommatePreferences = Field(default_factory=RoommatePreferences)

class SuccessStory(BaseModel):
    """Pydantic model for a success story."""
    id: Optional[int] = None
    user_id: int
    story_text: str
    timestamp: datetime = Field(default_factory=datetime.now)
    is_approved: bool = False
