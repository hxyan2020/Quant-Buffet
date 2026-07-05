# Quant Buffet — Admin CMS

## URLs (separate from the public site)

| Page | URL |
|------|-----|
| **Admin login** | http://localhost:3088/admin/login |
| **Strategy list** | http://localhost:3088/admin/strategies |
| **Create strategy** | http://localhost:3088/admin/strategies/new |
| **Edit strategy** | http://localhost:3088/admin/strategies/{id} |

Use the port from `.\scripts\run-dev.ps1` if not 3088.

Old URLs like `/en/admin/strategies` redirect to `/admin/strategies`.

## Credentials

| Field | Value |
|-------|--------|
| **Email** | `admin@local.dev` |
| **Password** | `admin123` |

Change in `.env` (`ADMIN_EMAIL`, `ADMIN_PASSWORD`), then run `npm run db:seed`.

## CMS features

- Full strategy CRUD (EN / ZH)
- **SEO:** meta title & meta description
- List filters: search, locale, paywall, published, region, market, asset class, created/updated date ranges
- **Paywall** toggle (Yes / No) inline in the list
- **Python code** column (scanned from HTML body)
- Creation & update timestamps

## Maintenance scripts

```powershell
npx prisma db push
npm run admin:scan-python    # refresh hasPythonCode column
npm run admin:set-half-free  # ~50% EN + 50% ZH strategies free
```
