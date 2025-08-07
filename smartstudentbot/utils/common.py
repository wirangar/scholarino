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

def check_json_version(file_path: str, expected_version: str = JSON_VERSION):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("version") != expected_version:
                logger.error(f"Unsupported JSON version in {file_path}. Expected {expected_version}, found {data.get('version')}")
                raise ValueError(f"Unsupported JSON version in {file_path}")
            return data
    except FileNotFoundError:
        logger.error(f"JSON file not found at {file_path}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Could not decode JSON from {file_path}")
        return None
