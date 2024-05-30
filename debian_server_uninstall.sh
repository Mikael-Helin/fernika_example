#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

rm -rf /opt/fernika
rm /usr/bin/start_fernika

echo "Fernika server uninstallation is complete."
