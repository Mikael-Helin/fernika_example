#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

apt-get update
apt-get install -y python3 python3-pip

mkdir -p /opt/fernika/bin
mkdir -p /opt/fernika/config

cp server.py /opt/fernika/bin/server.py
chmod +x /opt/fernika/bin/server.py
cp shared.py /opt/fernika/bin/shared.py
chmod +x /opt/fernika/bin/shared.py

python3 -m venv /opt/fernika/bin/venv
source /opt/fernika/bin/venv/bin/activate
pip3 install -r requirements_server.txt
deactivate

cp server.env /opt/fernika/config/.env
cp user.keys /opt/fernika/config/user.keys

cp start_fernika /usr/bin/start_fernika
chmod +x /usr/bin/start_fernika

echo ""
echo "Fernika server installation is complete."
echo "Please edit the configuration files /opt/fernika/config/.env and /opt/fernika/config/user.keys before starting the server."
echo "To start the server, run 'start_fernika' as root."
echo "To stop the server, press Ctrl+C in the terminal where the server is running."
echo "To uninstall the server, run 'debian_server_uninstaller.sh' as root."
