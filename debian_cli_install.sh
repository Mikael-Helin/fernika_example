#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

#apt-get update
#apt-get install -y python3 python3-pip

mkdir -p /opt/fernika/bin
mkdir -p /opt/fernika/config

cp fctl /usr/bin/fctl
chmod 755 /usr/bin/fctl
cp fctl.py /opt/fernika/bin/fctl.py
chmod 755 /opt/fernika/bin/fctl.py
cp shared.py /opt/fernika/bin/shared.py
chmod 755 /opt/fernika/bin/shared.py

python3 -m venv /opt/fernika/bin/venv
source /opt/fernika/bin/venv/bin/activate
pip3 install -r requirements_client.txt
deactivate

echo ""
echo "Fernika CLI installation is complete."
echo "Run 'fctl help' to get started."
