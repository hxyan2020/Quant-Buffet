# Deploy Quant Buffet to DigitalOcean → www.quantbuffet.com

**Droplet IP:** `188.166.214.47` (SSH and HTTP are reachable from your PC.)

---

## Step 1 — DNS (WordPress / domain registrar)

Your domain currently points at **WordPress.com**. Change only the **website** records; **keep email (Zoho) records**.

| Action | Type | Name | Value |
|--------|------|------|--------|
| **Change** | **A** | `@` | `188.166.214.47` |
| **Change** | **CNAME** or **A** | `www` | `188.166.214.47` (or CNAME `www` → `@`) |
| **Keep** | MX | `@` | `mx.zoho.com` (10), `mx2.zoho.com` (20), `mx3.zoho.com` (30) |
| **Keep** | TXT | `@` | SPF + Zoho verification |
| **Keep** | TXT | `_dmarc` | DMARC record |
| **Optional remove** | CNAME | `wpcloud1._domainkey` / `wpcloud2._domainkey` | WordPress email signing (only if you leave WP email) |
| **Optional remove** | TXT | `_domainconnect` | WordPress domain connect |

DNS can take **15 minutes – 48 hours** to propagate.

---

## Step 2 — Production `.env` on your PC

Before deploy, edit local `.env`:

```env
AUTH_URL="https://www.quantbuffet.com"
DATABASE_URL="file:/var/lib/quant-buffet/dev.db"
```

Use production Stripe keys and a strong `AUTH_SECRET`. The deploy script uploads your local `.env` to the server (it is **not** stored in git).

See `.env.production.example` for the full list.

**Also update:**

- Google OAuth → authorized redirect: `https://www.quantbuffet.com/api/auth/callback/google`
- Stripe webhook URL: `https://www.quantbuffet.com/api/stripe/webhook`

---

## Step 3 — Deploy from Windows

```powershell
cd C:\Users\hxyan\.cursor\projects\empty-window\quant-buffet-local

# Use your DigitalOcean root password (rotate if it was ever shared in chat)
$env:DO_HOST = "188.166.214.47"
$env:DO_USER = "root"
$env:DO_PASSWORD = "YOUR-ROOT-PASSWORD"

python scripts\deploy_do.py
```

This **builds on your PC** (avoids out-of-memory errors on a small droplet), uploads the standalone bundle, installs Node 20, nginx, PM2, SSL, and starts the app on port **3088** behind nginx.

---

## Step 4 — Verify

```powershell
curl.exe -I https://www.quantbuffet.com/en
```

On the server:

```bash
pm2 status
pm2 logs quant-buffet --lines 50
curl -I http://127.0.0.1:3088/en
```

---

## Manual deploy (no SSH from PC)

1. DigitalOcean → Droplet → **Launch console**
2. Upload `quant-buffet.tar.gz` to `/tmp/` (WinSCP / FileZilla, port 22)
3. Run:

```bash
bash /opt/quant-buffet/deploy/digitalocean/bootstrap.sh
```

---

## Firewall (DigitalOcean)

Allow inbound: **22**, **80**, **443**.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Site still shows WordPress | DNS not updated or still cached — wait or flush DNS |
| SSL error | Run `certbot --nginx -d quantbuffet.com -d www.quantbuffet.com` on server |
| 502 Bad Gateway | `pm2 restart quant-buffet` and check `pm2 logs` |
| Auth redirect wrong | `AUTH_URL` must be `https://www.quantbuffet.com` in server `.env` |
