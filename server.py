#!/usr/bin/env python3

import os
import time
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import base64
import hashlib
import json
import shared
import subprocess

def get_server_dir() -> str:
    """Return the path to the Fernika directory."""
    return os.path.join("/opt", "fernika")

def get_config_dir() -> str:
    """Return the path to the Fernika config directory."""
    return os.path.join(get_server_dir(), "config")

def get_env_path() -> str:
    """Return the path to the environment file."""
    env_path = os.path.join(get_config_dir(), ".env")
    return env_path

def get_checksum_keys_path() -> str:
    """Return the path to the checksum key file."""
    env_path = os.path.join(get_config_dir(), "user.keys")
    return env_path

def get_checksum_key(username: str) -> str:
    """Return the checksum key."""
    checksum_keys_path = get_checksum_keys_path()
    with open(checksum_keys_path, "r") as f:
        lines = f.readlines()
    checksum_key = None
    for line in lines:
        parts = line.strip().split("=")
        if len(parts) == 2 and parts[0] == username:
            checksum_key = parts[1]
            break
    return checksum_key

expiry_times = {}

app = Flask(__name__)

def update_cache(checksum: str) -> bool:
    """Update the cache."""
    now = int(time.time())
    expiry_times_list = list(expiry_times.keys())
    for expiry_time in expiry_times_list:
        if expiry_time < now:
            del expiry_times[expiry_time]
    for expiry_time in expiry_times.keys():
        if checksum in expiry_times[expiry_time]:
            return False
    expiry_time = now + TIMEOUT
    expiry_times[expiry_time] = checksum
    return True

@app.route("/<checksum>", methods=["POST"])
def handle_request(checksum):
    json_data = request.get_json()
    isOK, decoded_data = shared.validate_some_json(json_data)
    if not isOK:
        return jsonify({"checksum": checksum, "status": "FAIL", "message": decoded_data}), 400
    checksum_key = get_checksum_key(json_data.get("username"))
    if checksum_key is None:
        return jsonify({"checksum": checksum, "status": "FAIL", "message": "Invalid username"}), 400
    computed_checksum = shared.compute_checksum(checksum_key, json_data)
    if computed_checksum != checksum:
        return jsonify({"checksum": checksum, "status": "FAIL", "message": "Checksum mismatch"}), 400
    
    if not update_cache(checksum):
        return jsonify({"checksum": checksum, "status": "FAIL", "message": "Checksum already used"}), 400

    command = json_data.get("command")
    if command.startswith("upload "):
        if decoded_data is None:
            return jsonify({"checksum": checksum, "status": "FAIL", "message": "No data provided"}), 400
        remote_path = command[7:]
        if not shared.test_path(remote_path):
            return jsonify({"checksum": checksum, "status": "FAIL", "message": "Path contains invalid characters"}), 400
        with open(remote_path, "wb") as f:
            f.write(decoded_data)
        return jsonify({"checksum": checksum, "status": "OK", "message": "File uploaded"})

    elif command.startswith("download "):
        remote_path = command[9:]
        if not shared.test_path(remote_path):
            return jsonify({"checksum": checksum, "status": "FAIL", "message": "Path contains invalid characters"}), 400
        if not os.path.isfile(remote_path):
            return jsonify({"checksum": checksum, "status": "FAIL", "message": "File not found"}), 400
        with open(remote_path, "rb") as f:
            data = f.read()
        return jsonify({"checksum": checksum, "status": "OK", "data": base64.b64encode(data).decode("utf-8")})

    elif command.startswith("run "):
        cmd = command[4:]
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                return jsonify({"checksum": checksum, "status": "FAIL", "message": result.stderr}), 400
            return jsonify({"checksum": checksum, "status": "OK", "output": result.stdout}), 200
        except Exception as e:
            return jsonify({"checksum": checksum, "status": "FAIL", "message": str(e)}), 400
    else:
        return jsonify({"checksum": checksum, "status": "FAIL", "message": "Invalid command"}), 400
    
@app.route("/health")
def health_check():
    return jsonify({"status": "OK"})

@app.route("/")
def default():
    return f"Fernika Server version {shared.VERSION} (<i>date: {shared.DATE}</i>) running on port {PORT}"

if __name__ == "__main__":
    config_dir= get_config_dir()
    if not os.path.isdir(config_dir):
        os.makedirs(config_dir)
    env_path = get_env_path()
    if not os.path.isfile(env_path):
        raise FileNotFoundError(f"Environment file not found: {env_path}")
    load_dotenv(env_path)
    if "TIMEOUT" not in os.environ:
        raise ValueError("TIMEOUT not found in environment file")
    try:
        if int(os.environ["TIMEOUT"]) < 1:
            raise ValueError("Invalid TIMEOUT value")
    except ValueError:
        raise ValueError("Invalid TIMEOUT value")
    TIMEOUT = int(os.environ["TIMEOUT"])
    if "PORT" not in os.environ:
        raise ValueError("PORT not found in environment file")
    try:
        PORT = int(os.environ["PORT"])
        if PORT < 1 or PORT > 65535:
            raise ValueError("Invalid PORT value")
    except ValueError:
        raise ValueError("Invalid PORT value")
    checksum_keys_path = get_checksum_keys_path()
    if not os.path.isfile(checksum_keys_path):
        raise FileNotFoundError(f"Checksum key file not found: {checksum_keys_path}")
    app.run(host="0.0.0.0", port=PORT)
