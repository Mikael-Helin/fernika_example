#!/usr/bin/env python3

import os
import sys
import time
import requests
import json
import base64
from dotenv import load_dotenv
import shared

def help() -> None:
    """Print help message"""
    help = """
Usage:  fctl help                           # Print help message
        fctl version                        # Print version
        fctl upload <file> <remote_path>    # Upload a file    
        fctl download <file>                # Download a file and print its content
        fctl run <command> <args>           # Run a command
"""
    print(help)

def version() -> None:
    """Print version"""
    print(f"fctl version {shared.VERSION} ({shared.DATE})")

def get_config_dir() -> str:
    """Get the config directory"""
    return os.path.join(os.path.expanduser("~"), ".fernika")

def get_env_path() -> str:
    """Get the environment file path"""
    return os.path.join(get_config_dir(), ".env")

def get_checksum_key() -> str:
    """Get the checksum key"""
    return os.environ.get("CHECKSUM_KEY")

def get_server_url() -> str:
    """Get the server URL"""
    return os.environ.get("SERVER_URL")

def get_port() -> str:
    """Get the port"""
    return os.environ.get("PORT")

def get_timeout() -> int:
    """Get the timeout"""
    return os.environ.get("TIMEOUT")

def get_enviroment_file() -> None:
    """Validate the environment file"""
    env_path = get_env_path()
    if not os.path.isfile(env_path):
        print(f"Error: Environment file not found: {env_path}")
        sys.exit(1)
    load_dotenv(env_path)
    required_env_vars = ["USERNAME", "CHECKSUM_KEY", "SERVER_URL", "PORT"]
    for required_env_var in required_env_vars:
        if not os.environ.get(required_env_var):
            print(f"Error: Missing environment variable {required_env_var}")
            sys.exit(1)
    return os.environ

def post_request(json_data: dict) -> tuple[bool, str]:
    """Send a POST request"""
    timeout = os.environ.get("TIMEOUT")
    isOK, message = shared.validate_some_json(json_data, timeout)
    if not isOK:
        return False, message
    try:
        checksum_key = get_checksum_key()
        computed_checksum = shared.compute_checksum(checksum_key, json_data)
        headers = {"Content-Type": "application/json"}
        url = f"{get_server_url()}:{get_port()}/{computed_checksum}"
        if not url.startswith("http"):
            url = f"http://{url}"
    except Exception as e:
        return False, f"Error: {e}"
    try:
        response = requests.post(url, headers=headers, json=json_data)
    except Exception as e:
        return False, f"Error: {e}"

    if response.status_code != 200:
        return False, f"Status code error {response.status_code}: {response.text}"
    if not response.content:
        return False, "Error: Empty response"
    response_type = response.headers.get("Content-Type")
    if response_type != "application/json":
        return False, f"Error: Unexpected response content type: {response_type}"

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        return False, "Error: Response is not in JSON format"

    if response_json.get("status") != "OK":
        return False, f"Error: {response_json.get('message')}"

    return True, response_json

def main() -> None:
    """Main function"""
    if len(sys.argv) == 1:
        help()
        sys.exit(1)
    if sys.argv[1] == "help":
        help()
        sys.exit(0)
    if sys.argv[1] == "version":
        version()
        sys.exit(0)
    if len(sys.argv) < 3:
        print("Error: Missing arguments")
        sys.exit(1)
    command = sys.argv[1]
    if command not in ["upload", "download", "run"]:
        print("Error: Invalid command")
        sys.exit(1)
    
    fernika_dir = get_config_dir()
    if not os.path.isdir(fernika_dir):
        os.makedirs(fernika_dir)
        print(f"Directory created: {fernika_dir}")
    env_path = get_env_path()
    if not os.path.isfile(env_path):
        env_string="""USERNAME=username1
CHECKSUM_KEY=checksumkey1
SERVER_URL=localhost
PORT=422
TIMEOUT=30
"""
        with open(env_path, "w") as f:
            f.write(env_string)
        print(f"Environment file created: {env_path}")
        print("Please edit the file and set the correct values")
        sys.exit(1)
    
    load_dotenv(get_env_path())
    required_env_vars = ["USERNAME", "CHECKSUM_KEY", "SERVER_URL", "PORT", "TIMEOUT"]
    for required_env_var in required_env_vars:
        if not os.environ.get(required_env_var):
            print(f"Error: Missing environment variable {required_env_var}")
            sys.exit(1)
    json_data = {}
    json_data["username"] = os.environ.get("USERNAME")
    json_data["timestamp"] = int(time.time())

    if command == "upload":
        if len(sys.argv) != 4:
            print("Error: Need to specify a local file path and a remote file path")
            sys.exit(1)
        local_path = sys.argv[2]
        if not shared.test_path(local_path):
            print("Error: Invalid local file path")
            sys.exit(1)
        remote_path = sys.argv[3]
        if not shared.test_path(remote_path):
            print("Error: Invalid remote file path")
            sys.exit(1)
        json_data["command"] = f"upload {remote_path}"
        if not os.path.isfile(local_path):
            print(f"Error: File not found: {local_path}")
            sys.exit(1)
        with open(local_path, "rb") as f:
            data = f.read()
        b64_data = base64.b64encode(data).decode("utf-8")
        json_data["data"] = b64_data
        isOK, response = post_request(json_data)
        if not isOK or response.get("status") != "OK":
            print(json.dumps(response, indent=4))
            sys.exit(1)
        print(json.dumps(response, indent=4))

    if command == "download":
        if len(sys.argv) < 3:
            print("Error: Need to specify a remote file path")
            sys.exit(1)
        if len(sys.argv) > 3:
            print("Error: Too many arguments")
            sys.exit(1)
        remote_path = sys.argv[2]
        if not shared.test_path(remote_path):
            print("Error: Invalid remote file path")
            sys.exit(1)
        json_data["command"] = f"download {remote_path}"
        isOK, response = post_request(json_data)
        if not isOK or response.get("status") != "OK":
            print(response)
            sys.exit(1)
        b64_decoded_data = response.get("data")
        if b64_decoded_data:
            decoded_data = base64.b64decode(b64_decoded_data)
            print(decoded_data.decode("utf-8"), end="")
        else:
            print(response.get("message"))

    if command == "run":
        if len(sys.argv) < 3:
            print("Error: Need to specify a command")
            sys.exit(1)
        cmd = " ".join(sys.argv[2:])
        json_data["command"] = f"run {cmd}"
        isOK, response = post_request(json_data)
        print(json.dumps(response, indent=4))
        if not isOK or response.get("status") != "OK":
            sys.exit(1)

if __name__ == "__main__":
    is_development = True
    if is_development:
        main()
    else:
        try:
            main()
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    sys.exit(0)