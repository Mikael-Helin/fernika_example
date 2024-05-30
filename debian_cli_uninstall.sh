#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

rm /usr/bin/fctl
rm -rf /opt/fernika
rm -rf ~/.fernika

echo ""
echo "Fernika CLI has been uninstalled."
