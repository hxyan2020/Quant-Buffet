# Quant Buffet — local WordPress replacement

Next.js 16 scaffold that matches the Quant Buffet visual language (matte black canvas + cyan `#55E0FF`), bilingual routing, gated strategy CMS, Stripe unlock flows, GPT research assistants scoped to individual posts, JWT auth atop SQLite via Prisma, and an authenticated admin toolkit for authoring HTML strategies offline.

---

## Production deploy (DigitalOcean → www.quantbuffet.com)

See **[deploy/digitalocean/DEPLOY.md](deploy/digitalocean/DEPLOY.md)** for DNS, SSL, and the one-command deploy script.

Quick start (after DNS points to your droplet):

```powershell
$env:DO_HOST = "188.166.214.47"
$env:DO_USER = "root"
$env:DO_PASSWORD = "YOUR-ROOT-PASSWORD"
python scripts\deploy_do.py
```

---

## Prerequisites

| Tool | Why |
| --- | --- |
| Node 18 + npm | Next.js toolchain |
| SQLite (`file:./dev.db`) | Default Prisma datasource |
| Stripe account + CLI *(optional locally)* | `stripe listen …/api/stripe/webhook` |
| Google OAuth client | Social login toggle |
| OpenAI API key | Strategy bot completions |

Duplicate `.env.example` → `.env` and populate at minimum:

```
AUTH_SECRET="$(openssl rand -hex 32)"
AUTH_URL=http://localhost:3088
DATABASE_URL="file:./dev.db"

AUTH_GOOGLE_ID / AUTH_GOOGLE_SECRET    # optional
STRIPE_SECRET_KEY / STRIPE_WEBHOOK_SECRET

OPENAI_API_KEY / OPENAI_MODEL          # bot
ADMIN_EMAIL / ADMIN_PASSWORD           # seed overrides
AUTH_WECHAT_*                          # documentation-only until wired
NEXT_PUBLIC_*                          # Stripe publishable (future Elements)
```

---

## Getting started

```powershell
npm install
npx prisma migrate dev
npx prisma db seed
```

### Windows helper scripts (port **3088** — keeps **3000** free)

| Script | What it does |
| --- | --- |
| `.\scripts\import-wordpress.ps1` | Dry-run, then import `data/quantbuffet.WordPress.xml` into SQLite |
| `.\scripts\run-dev.ps1` | Start Next.js at **http://localhost:3088** |

Or via npm:

```bash
npm run import:wxr:dry    # preview counts only
npm run import:wxr        # replace DB strategies from WXR
npm run dev               # same as run-dev.ps1 (port 3088)
```

Place your WordPress export at `data/quantbuffet.WordPress.xml` (already copied from your Downloads export).

Visit `/` → middleware guesses default locale (`LOCALE_PREF`, geo-ish headers on edge, `accept-language`). All UI strings live under `messages/{en,zh}.json`.

### Seed users

Defaults from `ADMIN_EMAIL`, `ADMIN_PASSWORD` (see `.env`). Current repository seeds:

```
admin@local.dev / admin123   (ADMIN, library flagged unlocked for demos)
dual-language strategy slug: enhanced-reverse-beta-equities
```

Reset whenever `prisma/seed.ts` changes:

```bash
npx prisma migrate reset --force
```

---

## Requirement coverage

| # | Requirement | Implementation |
|---|--------------|----------------|
|1| Hero parity + Browse CTA|`src/app/[locale]/page.tsx`|
|2| Strategy Library table|`strategy-library/page.tsx` + locale filter|
|3| KPI columns|`Strategy` prisma model + translations|
|4| Auth (Google, email/pass, stub WeChat)|`InteractiveLogin.tsx`, `/api/register`, Auth.js Providers|
|5| EN/zh + inferred language|`middleware.ts`, `LocaleSwitcher.tsx`, dictionaries|
|6| Manageable paywall|`isPaywalled` boolean + helpers|
|7| Pricing page|$99 SKU via Stripe Checkout|`src/app/[locale]/pricing/page.tsx`
|8| Stripe payments|`/api/stripe/checkout` + webhook|
|9| Page-scoped GPT bot|`StrategyAssistant.tsx` → `/api/strategy-bot`
|10| Admin CMS|`/admin/strategies/*` + REST routes|
|11| Sample post|seeded bilingual article under `/strategies/enhanced-reverse-beta-equities`

---

## Monetization playbook

1. Put **test** Stripe keys into `.env`.
2. Forward webhooks locally:  
   `stripe listen --forward-to localhost:3000/api/stripe/webhook`
3. Paste signing secret → `STRIPE_WEBHOOK_SECRET`.
4. Log in locally, `/pricing`, run Checkout (`4242424242424242` test PAN).
5. Webhook confirms `checkout.session.completed`, sets `libraryUnlocked=true` and audits `subscriptions`.

Adjust amount by editing `unit_amount` in `/api/stripe/checkout`.

---

## WeChat SSO

Needs WeChat Open Platform **Website App** approvals + HTTPS callback. Outline:

1. Create app → retrieve `AUTH_WECHAT_APP_ID`, `AUTH_WECHAT_APP_SECRET`.
2. Set redirect (`AUTH_WECHAT_REDIRECT_URI`) to `{AUTH_URL}/api/auth/callback/wechat` once your custom provider lands.
3. Until then the UI disables the chip but surfaces copy from translations (`auth.wechat*` keys).

Popular integration patterns:

- Extend Auth.js with a custom OAuth provider proxying Tencent’s handshake.
- Or delegate to Passport.js route that mints a NextAuth-compatible JWT.

---

## Importing WordPress exports

Suggested pipeline:

1. Pull posts via REST (`/wp-json/wp/v2/posts?per_page=100&page=n`) respecting rate limits/licensing.
2. Normalize fields `(slug, locale, KPI metadata, excerpt, content_html)` → Prisma inserts.
3. Batch upload binaries to object storage rather than stuffing blobs in SQLite.

The admin textarea stores raw HTML; **sanitize** before trusting user-supplied markup (WordPress exporters may include iframe/script baggage).

---

## Hardening checklist

| Topic | Recommendation |
|---|----------------|
| XSS from HTML strategies | CSP + sanitizers (isomorphic-dompurify) server-side|
| GPT abuse/misuse | per-user quotas, abuse monitoring, disclaimers|
| Credential stuffing | MFA, rate-limit `/api/register` + `/api/auth`
| Stripe replay | webhook signature verification (already enforced)

---

Reach out internally if you need automated ingestion scripts layered on `/api/admin/strategies`.
