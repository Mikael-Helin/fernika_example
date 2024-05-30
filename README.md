# Fernika API

An API service written in Python. Fernika allows remote clients to run commands on the server where Fernika is installed.

WARNING: This code is not safe for a production server!

## Server Installation

Run the following command:

```bash
bash debian_server_installer.sh
```

Then, edit the configuration file at `/opt/fernika/config/.env` to set the timeout:

```env
TIMEOUT=30
PORT=422
```

The current timestamp must be less than the timestamp in the request plus the TIMEOUT (in seconds) for a successful request.

PORT is the port number for the server, if you run Fernika in rootless mode, then pick a number larger than 1024, for example 1422.

Also, edit the user keys file at `/opt/fernika/config/user.keys`:

```plaintext
username1=checksumkey1
username2=checksumkey2
```

## Client Installation

Run the following command:

```bash
bash debian_client_installer.sh
```

Then, edit the client environment file at `~/fernika.env`:

```env
username1=checksumkey1
```

This username and corresponding checksum key must match one of the entries in the server configuration.

## Uninstallation

To uninstall the server, run:

```bash
bash debian_server_uninstaller.sh
```

To uninstall the client, run:

```bash
bash debian_client_uninstaller.sh
```

## API Format

### Upload a File

To upload a file, POST to `servername:422/<checksum>` with the following JSON body:

```json
{
    "username": "your username",
    "timestamp": "utc in unixtimestamp",
    "command": "upload /remote/path/filename",
    "data": "base64 encoded string that is uploaded"
}
```

### Download a File

To download a file, POST to `servername:422/<checksum>` with the following JSON body:

```json
{
    "username": "your username",
    "timestamp": "utc in unixtimestamp",
    "command": "download /remote/path/filename"
}
```

### Run a Remote Command

To run a remote command, POST to `servername:422/<checksum>` with the following JSON body:

```json
{
    "username": "your username",
    "timestamp": "utc in unixtimestamp",
    "command": "run ls -al"
}
```

### Response Format

The response to your request will be in the following format:

```json
{
    "checksum": "same checksum as in the POST request",
    "status": "one of OK, FAIL, TIMEOUT, or REPEAT",
    "message": "some message if there is any",
    "data": "if there is any data, it is base64 encoded"
}
```

## Client CLI Format

### Upload a File

To upload a file, run:

```bash
fctl upload /local/path/filename /remote/path/filename
```

### Download a File

To download a file, run:

```bash
fctl download /remote/path/filename
```

### Run a Remote Command

To run a remote command, for example, list directory contents, run:

```bash
fctl run ls -al
```
