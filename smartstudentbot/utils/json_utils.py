import json
from typing import Any, Dict, List, Optional
from .logger import logger
from ..config import JSON_VERSION

def read_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Reads a JSON file, checks its version, and returns its content.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("version") != JSON_VERSION:
                logger.error(f"Unsupported JSON version in {file_path}. Expected {JSON_VERSION}, found {data.get('version')}")
                raise ValueError(f"Unsupported JSON version in {file_path}")
            return data
    except FileNotFoundError:
        logger.error(f"JSON file not found at {file_path}")
        # Create an empty file with the correct structure
        template = {"version": JSON_VERSION, "data": []}
        write_json_file(file_path, template)
        return template
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error processing JSON file {file_path}: {e}")
        return None

def write_json_file(file_path: str, content: Dict[str, Any]) -> bool:
    """
    Writes content to a JSON file.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to write to JSON file {file_path}: {e}")
        return False

def get_next_id(file_path: str) -> int:
    """Finds the highest ID in a JSON file's data list and returns the next ID."""
    data = read_json_file(file_path)
    if not data or not data.get("data"):
        return 1
    ids = [item.get("id", 0) for item in data["data"]]
    return max(ids) + 1 if ids else 1

def add_item_to_json(file_path: str, new_item: Dict[str, Any]) -> bool:
    """Adds a new item with a unique ID to a JSON file."""
    data = read_json_file(file_path)
    if data is None:
        return False

    new_item["id"] = get_next_id(file_path)
    data["data"].append(new_item)
    return write_json_file(file_path, data)

def get_item_by_id(file_path: str, item_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves an item from a JSON file by its ID."""
    data = read_json_file(file_path)
    if not data or not data.get("data"):
        return None
    for item in data["data"]:
        if item.get("id") == item_id:
            return item
    return None

def update_item_in_json(file_path: str, item_id: int, updated_data: Dict[str, Any]) -> bool:
    """Updates an item in a JSON file by its ID."""
    data = read_json_file(file_path)
    if data is None:
        return False

    item_found = False
    for i, item in enumerate(data["data"]):
        if item.get("id") == item_id:
            # Preserve the original ID
            updated_data["id"] = item_id
            data["data"][i] = updated_data
            item_found = True
            break

    if not item_found:
        logger.error(f"Item with id {item_id} not found in {file_path}")
        return False

    return write_json_file(file_path, data)

def delete_item_from_json(file_path: str, item_id: int) -> bool:
    """Deletes an item from a JSON file by its ID."""
    data = read_json_file(file_path)
    if data is None:
        return False

    original_count = len(data["data"])
    data["data"] = [item for item in data["data"] if item.get("id") != item_id]

    if len(data["data"]) == original_count:
        logger.error(f"Item with id {item_id} not found for deletion in {file_path}")
        return False

    return write_json_file(file_path, data)
