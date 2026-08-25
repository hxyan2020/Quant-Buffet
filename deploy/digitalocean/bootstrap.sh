#!/usr/bin/env bash
# First-time server bootstrap (run in droplet console if deploy script cannot SSH)
set -euo pipefail

APP_DIR="/opt/quant-buffet"
TAR="/tmp/quant-buffet.tar.gz"

mkdir -p "$APP_DIR"
if [[ -f "$TAR" ]]; then
  tar -xzf "$TAR" -C "$APP_DIR"
fi

bash "$APP_DIR/deploy/digitalocean/install.sh"
