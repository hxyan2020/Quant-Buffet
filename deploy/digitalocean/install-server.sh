#!/usr/bin/env bash
# Lightweight server setup — expects pre-built Next.js standalone (built on your PC).
set -euo pipefail

APP_DIR="/opt/quant-buffet"
DATA_DIR="/var/lib/quant-buffet"
DOMAIN="${QB_DOMAIN:-www.quantbuffet.com}"
APEX_DOMAIN="${QB_APEX_DOMAIN:-quantbuffet.com}"
STANDALONE="${APP_DIR}/.next/standalone"

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq curl ca-certificates gnupg nginx certbot python3-certbot-nginx

if ! command -v node >/dev/null 2>&1 || [[ "$(node -v | sed 's/v//' | cut -d. -f1)" -lt 20 ]]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y -qq nodejs
fi

if ! command -v pm2 >/dev/null 2>&1; then
  npm install -g pm2
fi

# Extra memory for small droplets (optional, safe if already exists)
if [[ ! -f /swapfile ]] && [[ "$(swapon --show | wc -l)" -eq 0 ]]; then
  fallocate -l 2G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=2048 status=none
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

mkdir -p "$DATA_DIR" "${APP_DIR}/.next"
cd "$APP_DIR"

if [[ ! -d "${APP_DIR}/release/standalone" ]]; then
  echo "Missing ${APP_DIR}/release/standalone — upload a pre-built bundle." >&2
  exit 1
fi

rm -rf "$STANDALONE"
mkdir -p "$STANDALONE"
cp -a "${APP_DIR}/release/standalone/." "$STANDALONE/"

if [[ ! -f "$STANDALONE/server.js" ]]; then
  echo "Invalid standalone bundle (no server.js)." >&2
  exit 1
fi

if [[ -f "${APP_DIR}/release/prisma/dev.db" ]]; then
  cp "${APP_DIR}/release/prisma/dev.db" "$DATA_DIR/dev.db"
elif [[ ! -f "$DATA_DIR/dev.db" && -f "${APP_DIR}/prisma/dev.db" ]]; then
  cp "${APP_DIR}/prisma/dev.db" "$DATA_DIR/dev.db"
fi

if [[ ! -f "$DATA_DIR/dev.db" ]]; then
  echo "ERROR: SQLite database missing at $DATA_DIR/dev.db — re-deploy from PC with prisma/dev.db present." >&2
  exit 1
fi

chmod 664 "$DATA_DIR/dev.db"
chown root:root "$DATA_DIR/dev.db"

if [[ ! -f .env ]]; then
  echo "Missing $APP_DIR/.env" >&2
  exit 1
fi

DB_URL="file:${DATA_DIR}/dev.db"
sed -i "s|^DATABASE_URL=.*|DATABASE_URL=\"${DB_URL}\"|" .env
sed -i 's|^AUTH_URL=.*|AUTH_URL="https://www.quantbuffet.com"|' .env
cp .env "$STANDALONE/.env"

apt-get install -y -qq sqlite3 2>/dev/null || true
COUNT="$(sqlite3 "$DATA_DIR/dev.db" "SELECT COUNT(*) FROM Strategy;" 2>/dev/null || echo 0)"
echo "Database OK — ${COUNT} strategies in SQLite."

cat > "${APP_DIR}/ecosystem.config.cjs" <<EOF
module.exports = {
  apps: [
    {
      name: "quant-buffet",
      cwd: "${STANDALONE}",
      script: "server.js",
      env: {
        NODE_ENV: "production",
        PORT: "3088",
        HOSTNAME: "0.0.0.0",
        DATABASE_URL: "file:${DATA_DIR}/dev.db",
      },
    },
  ],
};
EOF

pm2 delete quant-buffet 2>/dev/null || true
cd "$APP_DIR"
pm2 start ecosystem.config.cjs
pm2 save
pm2 startup systemd -u root --hp /root 2>/dev/null | tail -1 | bash || true

cp "$APP_DIR/deploy/digitalocean/nginx-quantbuffet.conf" /etc/nginx/sites-available/quantbuffet
ln -sf /etc/nginx/sites-available/quantbuffet /etc/nginx/sites-enabled/quantbuffet
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

if [[ "${QB_SKIP_SSL:-0}" != "1" ]]; then
  certbot --nginx -d "$APEX_DOMAIN" -d "$DOMAIN" --non-interactive --agree-tos -m "${QB_SSL_EMAIL:-hola@quantbuffet.com}" --redirect || true
fi

echo "OK — Quant Buffet is running at http://127.0.0.1:3088"
echo "Public URL: https://${DOMAIN}"
