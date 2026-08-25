#!/usr/bin/env bash
# Run on the DigitalOcean droplet AFTER code deploy + prisma generate.
# Archives existing strategies (flag only) and publishes all temp-lab strategies.
set -euo pipefail
cd /opt/quant-buffet
export DATABASE_URL="${DATABASE_URL:-file:/var/lib/quant-buffet/dev.db}"
npx prisma db push --skip-generate
npx prisma generate
npx tsx scripts/promote-lab-to-production.ts
pm2 restart quant-buffet || true
echo "Promote complete."
