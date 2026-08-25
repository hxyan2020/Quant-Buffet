"""Build unified lab index: full library (1764) + new_100 drafts."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "backtest" / "catalog" / "strategies_full.json"
BATCH = ROOT / "backtest" / "results" / "batch_full_summary.json"
DRAFT_POSTS = ROOT / "backtest" / "drafts" / "new_100" / "posts"
OUT = ROOT / "backtest" / "drafts" / "lab_index.json"
LIST_MD = ROOT / "backtest" / "drafts" / "FULL_STRATEGY_LIST.md"
LIST_JSON = ROOT / "backtest" / "drafts" / "full_strategy_list.json"


def fmt_pct(x):
    if x is None:
        return None
    try:
        return f"{float(x) * 100:.2f}%"
    except (TypeError, ValueError):
        return None


def fmt_num(x):
    if x is None:
        return None
    try:
        return f"{float(x):.2f}"
    except (TypeError, ValueError):
        return None


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    batch = json.loads(BATCH.read_text(encoding="utf-8")) if BATCH.exists() else {}
    by_key = {r["file_key"]: r for r in batch.get("results") or [] if r.get("file_key")}
    by_slug_locale = {
        (r.get("slug"), r.get("locale")): r for r in batch.get("results") or [] if r.get("slug")
    }

    entries = []
    for s in catalog["strategies"]:
        fk = s["file_key"]
        locale = s.get("locale") or "en"
        slug = s["slug"]
        br = by_key.get(fk) or by_slug_locale.get((slug, locale)) or {}
        m = br.get("metrics") if br.get("status") == "ok" else None
        code_path = f"backtest/strategies/generated/{fk}.py"
        entries.append(
            {
                "id": f"library:{locale}:{slug}",
                "source": "library",
                "slug": slug,
                "locale": locale,
                "title": s.get("title") or slug,
                "file_key": fk,
                "template": s.get("template"),
                "assets": s.get("assets") or [],
                "fidelity": s.get("fidelity"),
                "has_qc_source": s.get("has_qc_source"),
                "assetClass": s.get("assetClass"),
                "region": s.get("region"),
                "isPaywalled": s.get("isPaywalled"),
                "code_path": code_path if (ROOT / code_path).exists() else None,
                "annualisedReturn": fmt_pct(m.get("cagr")) if m else s.get("site_annualisedReturn"),
                "sharpeRatio": fmt_num(m.get("sharpe")) if m else s.get("site_sharpeRatio"),
                "maxDrawdown": fmt_pct(m.get("max_drawdown")) if m else s.get("site_maxDrawdown"),
                "volatility": fmt_pct(m.get("volatility")) if m else None,
                "beta": fmt_num(m.get("beta")) if m else None,
                "sortinoRatio": fmt_num(m.get("sortino")) if m else None,
                "trades": (m.get("trades") if m else None) or br.get("trades"),
                "siteCagr": s.get("site_annualisedReturn"),
                "params": s.get("params") or {},
                "backtest_status": br.get("status"),
                "href": f"/{locale}/draft-preview/{slug}",
            }
        )

    draft_count = 0
    if DRAFT_POSTS.exists():
        for p in sorted(DRAFT_POSTS.glob("*.json")):
            d = json.loads(p.read_text(encoding="utf-8"))
            slug = d["slug"]
            locale = d.get("locale") or "en"
            draft_count += 1
            entries.append(
                {
                    "id": f"new100:{locale}:{slug}",
                    "source": "new100",
                    "slug": slug,
                    "locale": locale,
                    "title": d.get("title") or slug,
                    "file_key": None,
                    "template": d.get("template"),
                    "assets": d.get("assets") or [],
                    "fidelity": d.get("fidelity"),
                    "has_qc_source": False,
                    "assetClass": d.get("assetClass"),
                    "region": d.get("region"),
                    "isPaywalled": d.get("isPaywalled", True),
                    "code_path": f"backtest/drafts/new_100/code/{slug}.py",
                    "annualisedReturn": d.get("annualisedReturn"),
                    "sharpeRatio": d.get("sharpeRatio"),
                    "maxDrawdown": d.get("maxDrawdown"),
                    "volatility": d.get("volatility"),
                    "beta": d.get("beta"),
                    "sortinoRatio": d.get("sortinoRatio"),
                    "trades": (d.get("backtest") or {}).get("trades"),
                    "params": d.get("params") or {},
                    "backtest_status": (d.get("backtest") or {}).get("status"),
                    "href": f"/{locale}/draft-preview/{slug}",
                    "paperTitle": d.get("paperTitle"),
                }
            )

    # Sort: new100 first by sharpe, then library by title
    def sort_key(e):
        src = 0 if e["source"] == "new100" else 1
        sh = float(e["sharpeRatio"] or -99) if e.get("sharpeRatio") else -99
        try:
            sh = float(str(e.get("sharpeRatio") or "-99").replace("%", ""))
        except ValueError:
            sh = -99
        return (src, -sh, (e.get("title") or "").lower())

    entries.sort(key=sort_key)

    payload = {
        "count": len(entries),
        "library": sum(1 for e in entries if e["source"] == "library"),
        "new100": sum(1 for e in entries if e["source"] == "new100"),
        "by_locale": {
            "en": sum(1 for e in entries if e["locale"] == "en"),
            "zh": sum(1 for e in entries if e["locale"] == "zh"),
        },
        "note": "TEMP LAB ONLY — not published. draft-preview routes with ENABLE_DRAFT_PREVIEW.",
        "strategies": entries,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    LIST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Full strategy list (temp lab preview)",
        "",
        f"- Total: **{payload['count']}**",
        f"- Library: **{payload['library']}**",
        f"- New academic drafts: **{payload['new100']}**",
        f"- Locales: en={payload['by_locale']['en']}, zh={payload['by_locale']['zh']}",
        "",
        "| # | Source | Locale | Title | CAGR | Sharpe | MaxDD | Template | Slug |",
        "|---|--------|--------|-------|------|--------|-------|----------|------|",
    ]
    for i, e in enumerate(entries, 1):
        lines.append(
            f"| {i} | {e['source']} | {e['locale']} | {e['title'].replace('|', '/')} | "
            f"{e.get('annualisedReturn') or '—'} | {e.get('sharpeRatio') or '—'} | "
            f"{e.get('maxDrawdown') or '—'} | {e.get('template') or '—'} | `{e['slug']}` |"
        )
    LIST_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} count={payload['count']} library={payload['library']} new100={payload['new100']}")
    print(f"Wrote {LIST_MD}")


if __name__ == "__main__":
    main()
