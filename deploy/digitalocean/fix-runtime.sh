#!/usr/bin/env bash
# Quick fix on server: ensure DB exists and PM2 has correct DATABASE_URL
set -euo pipefail

APP_DIR="/opt/quant-buffet"
DATA_DIR="/var/lib/quant-buffet"
STANDALONE="${APP_DIR}/.next/standalone"
DB_URL="file:${DATA_DIR}/dev.db"

mkdir -p "$DATA_DIR"
cd "$APP_DIR"

if [[ -f release/prisma/dev.db ]]; then
  cp release/prisma/dev.db "$DATA_DIR/dev.db"
elif [[ -f prisma/dev.db ]]; then
  cp prisma/dev.db "$DATA_DIR/dev.db"
fi

if [[ ! -f "$DATA_DIR/dev.db" ]]; then
  echo "No database file found. Re-run deploy from your PC." >&2
  exit 1
fi

chmod 664 "$DATA_DIR/dev.db"
if [[ -f .env ]]; then
  sed -i "s|^DATABASE_URL=.*|DATABASE_URL=\"${DB_URL}\"|" .env
  cp .env "$STANDALONE/.env"
fi

pm2 delete quant-buffet 2>/dev/null || true
pm2 start "${APP_DIR}/ecosystem.config.cjs" --update-env
pm2 save

echo "Restarted. Test: curl -sI http://127.0.0.1:3088/en | head -1"
