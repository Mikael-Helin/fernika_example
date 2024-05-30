#!/usr/bin/env python3

import os
from dotenv import load_dotenv
import hashlib
import json
import base64
import time

VERSION = "0.0.1"
DATE = "2024-05-24"

def compute_checksum(checksum_key: str, json_data: dict) -> str:
    """Compute the checksum of a JSON object. Return the checksum if successful, None otherwise."""
    if not checksum_key:
        raise ValueError("Invalid checksum key")
    json_string = json.dumps(json_data, sort_keys=True)
    json_string = checksum_key + " " + json_string
    return hashlib.sha256(json_string.encode("utf-8")).hexdigest()

def validate_username(username: str) -> bool:
    """Validate a username. Return True if valid, False otherwise."""
    return username.isalnum() and len(username) <= 40 and len(username) > 0

def validate_timestamp(timestamp: int, timeout: int=30) -> bool:
    """Validate a timestamp. Return True if valid, False otherwise."""
    try:
        if int(timeout) < 1:
            raise ValueError("Invalid timeout")
    except Exception as e:
        raise ValueError("Invalid timeout")
    try:
        current_time = int(time.time())
        return 0 <= current_time - int(timestamp) <= int(timeout)
    except Exception as e:
        raise ValueError("Invalid timestamp")

def test_path(path: str) -> bool:
    """Test if a path contains any invalid characters. Return True if valid, False otherwise."""
    test = path.replace("/", "").replace(".", "").replace("_", "").replace("-", "")
    return test.isalnum()

def validate_some_json(json_data: dict, timeout: int=30) -> tuple[bool, str]:
    """Validate a JSON object against a list of required fields. Return True if valid, False otherwise. Also return the decoded data if present."""
    allowed_keys = ["username", "timestamp", "command", "data"]
    b64_decoded_data = None
    for key in allowed_keys:
        if key == "data":
            continue
        if key not in json_data.keys():
            return False, f"Missing key {key} in JSON data"
    for key in json_data.keys():
        if key not in allowed_keys:
            return False, f"Invalid key in JSON data"
        value = json_data[key]
        if key == "username" and not validate_username(value):
            return False, "Invalid username in JSON"
        if key == "timestamp" and not validate_timestamp(value, timeout):
            return False, "Invalid timestamp in JSON"
        if key == "command" and not (value.startswith("upload ") or value.startswith("download ") or value.startswith("run ")):
            return False, "Invalid command in JSON"
        if key == "data":
            try:
                if value is not None:
                    b64_decoded_data = base64.b64decode(value)
            except Exception as e:
                return False, "Invalid data in JSON"
    return True, b64_decoded_data

