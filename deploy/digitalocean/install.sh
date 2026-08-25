#!/usr/bin/env bash
# Run on the droplet after code is in /opt/quant-buffet
set -euo pipefail

APP_DIR="/opt/quant-buffet"
DATA_DIR="/var/lib/quant-buffet"
DOMAIN="${QB_DOMAIN:-www.quantbuffet.com}"
APEX_DOMAIN="${QB_APEX_DOMAIN:-quantbuffet.com}"

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

mkdir -p "$DATA_DIR"
if [[ ! -f "$DATA_DIR/dev.db" && -f "$APP_DIR/prisma/dev.db" ]]; then
  cp "$APP_DIR/prisma/dev.db" "$DATA_DIR/dev.db"
fi

cd "$APP_DIR"

if [[ ! -f .env ]]; then
  echo "Missing $APP_DIR/.env — copy .env.production.example and fill secrets first." >&2
  exit 1
fi

if ! npm ci; then
  echo "npm ci failed — syncing lock file with npm install…" >&2
  npm install
fi
npx prisma generate
export DATABASE_URL="file:${DATA_DIR}/dev.db"
npx prisma db push

npm run build

mkdir -p .next/standalone/.next
cp -r .next/static .next/standalone/.next/static
cp -r public .next/standalone/public
cp .env .next/standalone/.env

# Ensure production DB path in runtime env
if grep -q '^DATABASE_URL=' .env; then
  sed -i "s|^DATABASE_URL=.*|DATABASE_URL=\"file:${DATA_DIR}/dev.db\"|" .env
  cp .env .next/standalone/.env
fi
if grep -q '^AUTH_URL=' .env; then
  sed -i 's|^AUTH_URL=.*|AUTH_URL="https://www.quantbuffet.com"|' .env
  cp .env .next/standalone/.env
fi

cat > ecosystem.config.cjs <<EOF
module.exports = {
  apps: [
    {
      name: "quant-buffet",
      cwd: "${APP_DIR}/.next/standalone",
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

echo "Quant Buffet running on http://127.0.0.1:3088 (proxied by nginx)."
echo "Set DNS A @ and www to this server's public IP, then open https://${DOMAIN}"
