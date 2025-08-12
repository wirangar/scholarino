from fastapi import HTTPException
import re
import json
from .logger import logger
# Import config with a try-except block to handle running from different directories
try:
    from config import JSON_VERSION
except ImportError:
    from smartstudentbot.config import JSON_VERSION


def sanitize_markdown(text: str) -> str:
    return re.sub(r'[<>`]', '', text)

def validate_file(file_size: int, file_type: str) -> bool:
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB")
    if file_type not in ["pdf", "jpg", "png", "mp3", "mp4"]:
        raise HTTPException(status_code=400, detail="Invalid file format")
    return True
