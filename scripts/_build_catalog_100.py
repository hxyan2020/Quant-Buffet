"""Build a quality 100-strategy catalog for in-house backtests."""
from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from html import unescape
from pathlib import Path

DB = Path("prisma/dev.db")
OUT = Path("backtest/catalog/strategies_100.json")

WHITELIST = {
    "SPY", "QQQ", "IWM", "DIA", "VOO", "VTI", "IWB", "IJH", "IJR", "MDY", "OEF", "RSP",
    "EFA", "EEM", "VEA", "VWO", "VGK", "EWJ", "EWZ", "FXI", "EWU", "EWG", "EWQ", "EWI",
    "EWP", "EWN", "EWK", "EWD", "EWL", "EWC", "EWA", "EWH", "EWT", "EWY", "EWS", "EIDO",
    "THD", "EPHE", "ECH", "EPOL", "EZA", "ARGT", "TUR", "ASHR", "ACWX", "ACWI", "URTH",
    "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY", "XLC", "XLRE",
    "VNQ", "IYR", "RWX",
    "TLT", "IEF", "IEI", "SHY", "SHV", "BIL", "BND", "AGG", "LQD", "HYG", "TIP", "MBB",
    "GLD", "SLV", "DBC", "GSG", "DBA", "USO", "UNG", "VIXY", "SVXY",
}

# Hard skip — cannot reconstruct without alt data / derivatives
SKIP_IDEAS = [
    "employee sentiment",
    "box office",
    "lunar",
    "fomc",
    "commitment of traders",
    "cointegration",
    "pairs trading",
    "option chain",
    "add_option",
    "cryptocurrenc",
    "bitcoin",
    "intraday momentum",
    "earnings management",
    "stock split",
    "demographic",
    "military expenditure",
]

# Soft skip — fundamental signals; allow only as ETF momentum/equal-weight proxies
PROXY_ONLY = [
    "cape",
    "accrual",
    "value effect",
    "value factor",
    "spin-off",
    "spin off",
    "ipo",
    "oil beta",
    "betting against beta",
    "skewness",
    "double bottom",
]


def strip_html(h: str) -> str:
    t = unescape(h or "")
    t = re.sub(r"<[^>]+>", "\n", t)
    return t


def extract_code_equities(code: str) -> list[str]:
    out = []
    for pat in [
        r"add_equity\(\s*[\"']([A-Z]{2,5})[\"']",
        r"AddEquity\(\s*[\"']([A-Z]{2,5})[\"']",
    ]:
        for m in re.findall(pat, code, flags=re.I):
            u = m.upper()
            if u in WHITELIST and u not in out:
                out.append(u)
    # quoted whitelist tickers in arrays
    for m in re.findall(r"[\"']([A-Z]{2,5})[\"']", code):
        if m in WHITELIST and m not in out:
            out.append(m)
    return out


def extract_text_tickers(text: str) -> list[str]:
    out = []
    for m in re.findall(r"\b([A-Z]{2,5})\b", text):
        if m in WHITELIST and m not in out:
            out.append(m)
    return out


def sma_period(code: str) -> int:
    m = re.search(r"(\d+)\s*\*\s*21", code)
    if m:
        return int(m.group(1)) * 21
    m = re.search(r"(?:moving_avg_period|sma_period)\s*=\s*(\d+)", code, re.I)
    if m:
        v = int(m.group(1))
        return v if v > 20 else v * 21
    m = re.search(r"SimpleMovingAverage\([^,]+,\s*(\d+)", code, re.I)
    if m:
        return int(m.group(1))
    return 200


def classify(title: str, low: str, assets: list[str]) -> tuple[str, dict, str] | None:
    if any(k in low for k in SKIP_IDEAS):
        return None

    fidelity = "reconstructed_etf_rules"
    if any(k in low for k in PROXY_ONLY):
        if len(assets) < 4:
            return None
        # ETF-book proxy only (not the paper's fundamental signal)
        fidelity = "etf_universe_proxy"
        return (
            "momentum_rotation",
            {
                "lookback": 126,
                "top_n": max(1, min(3, len(assets) // 4)),
                "rebalance": "monthly",
            },
            fidelity,
        )

    if re.search(r"dual.?momentum|absolute.?momentum", low):
        cash = "BIL" if "BIL" in assets else ("SHY" if "SHY" in assets else "BIL")
        eqs = list(assets)
        if cash not in eqs:
            eqs.append(cash)
        risky = [a for a in eqs if a != cash]
        if not risky:
            eqs = ["SPY", cash]
        return (
            "dual_momentum",
            {
                "assets": eqs,
                "lookback": 252,
                "cash_symbol": cash,
                "rebalance": "monthly",
            },
            fidelity,
        )

    if re.search(r"risk parity|equal risk", low) and len(assets) >= 3:
        return "risk_parity", {"vol_lookback": 63, "rebalance": "monthly"}, fidelity

    if re.search(r"volatility.?target|managed volatility|vol target", low):
        return (
            "vol_target",
            {"target_vol": 0.10, "vol_lookback": 63, "rebalance": "monthly"},
            fidelity,
        )

    if re.search(r"mean.?revert|bollinger|reversal", low) and len(assets) >= 1:
        if len(assets) >= 4 and "reversal" in low:
            return (
                "momentum_rotation",
                {
                    "lookback": 21,
                    "top_n": max(1, len(assets) // 4),
                    "rebalance": "monthly",
                    "invert": True,
                },
                fidelity,
            )
        return (
            "mean_reversion",
            {
                "lookback": 20,
                "entry_z": -1.0,
                "exit_z": 0.0,
                "rebalance": "daily",
            },
            fidelity,
        )

    if re.search(r"golden.?cross|50.?day|200.?day.*cross|dual.?ma", low):
        return "dual_ma", {"fast": 50, "slow": 200, "rebalance": "daily"}, fidelity

    if re.search(
        r"trend.?follow|moving average|sma filter|price above|timing.*sma|avoid equity bear",
        low,
    ):
        return "sma_trend", {"sma_days": 200, "rebalance": "monthly"}, fidelity

    if (
        re.search(
            r"asset.?allocation|vigilant|defensive asset|bold asset|adaptive asset|sector.?rotat|country.?momentum|geographical|momentum.?factor|1-month momentum|alpha momentum|optimalized|multi-asset market breadth|industry momentum",
            low,
        )
        and len(assets) >= 3
    ):
        top_n = 1 if "vigilant" in low or "defensive" in low or "protective" in low else max(
            1, min(3, len(assets) // 3)
        )
        return (
            "momentum_rotation",
            {
                "lookback": 21 if "1-month" in low else 126,
                "top_n": top_n,
                "rebalance": "monthly",
            },
            fidelity,
        )

    if re.search(r"momentum", low) and len(assets) >= 4:
        return (
            "momentum_rotation",
            {
                "lookback": 126,
                "top_n": max(1, len(assets) // 4),
                "rebalance": "monthly",
            },
            fidelity,
        )

    if re.search(r"momentum", low) and len(assets) <= 3:
        return "abs_momentum", {"lookback": 252, "rebalance": "monthly"}, fidelity

    if len(assets) >= 4 and re.search(r"allocat|diversif|multi.?asset|portfolio|sector", low):
        return "equal_weight", {"rebalance": "monthly"}, fidelity

    if len(assets) >= 5:
        return "equal_weight", {"rebalance": "monthly"}, fidelity

    if len(assets) >= 2 and re.search(r"trend|timing|moving average|sma", low):
        return "sma_trend", {"sma_days": 200, "rebalance": "monthly"}, fidelity

    return None


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT slug, title, teaser, summary, annualisedReturn, sharpeRatio, maxDrawdown,
               pythonCodeHtml, contentHtml
        FROM Strategy
        WHERE locale='en' AND published=1 AND hasPythonCode=1
          AND slug != '__trashed'
        ORDER BY isPaywalled ASC, slug
        """
    ).fetchall()

    specs = []
    for r in rows:
        slug = r["slug"] or ""
        if not re.fullmatch(r"[a-z0-9\-]+", slug):
            continue
        code = strip_html(r["pythonCodeHtml"])
        content = strip_html(r["contentHtml"] or "")[:10000]
        title = r["title"] or ""
        teaser = r["teaser"] or ""
        low = f"{title}\n{teaser}\n{content[:3000]}\n{code[:3000]}".lower()

        assets = extract_code_equities(code)
        if len(assets) < 2:
            # pull from article text but keep only whitelist
            text_assets = extract_text_tickers(f"{title}\n{teaser}\n{content}\n{code}")
            if len(text_assets) > len(assets):
                assets = text_assets

        if not assets:
            continue

        classified = classify(title, low, assets)
        if not classified:
            continue
        template, params, fidelity = classified
        assets = params.pop("assets", assets)[:12]

        # Fix SMA from code when trend
        if template == "sma_trend":
            params["sma_days"] = sma_period(code)

        specs.append(
            {
                "slug": r["slug"],
                "title": title,
                "site_annualisedReturn": r["annualisedReturn"],
                "site_sharpeRatio": r["sharpeRatio"],
                "site_maxDrawdown": r["maxDrawdown"],
                "template": template,
                "assets": assets,
                "params": params,
                "fidelity": fidelity,
            }
        )

    # Prefer richer universes; cap single-asset fillers
    specs.sort(key=lambda s: (-len(s["assets"]), s["slug"]))

    selected = []
    seen = set()
    singles = 0
    for min_assets in (5, 3, 2, 1):
        for s in specs:
            if s["slug"] in seen:
                continue
            if len(s["assets"]) < min_assets:
                continue
            if len(s["assets"]) <= 2 and s["template"] in ("dual_momentum", "abs_momentum", "sma_trend"):
                if singles >= 45:
                    continue
                if len(s["assets"]) == 1 and s["template"] == "abs_momentum":
                    s = dict(s)
                    s["template"] = "dual_momentum"
                    s["assets"] = [s["assets"][0], "BIL"]
                    s["params"] = {
                        "lookback": 252,
                        "cash_symbol": "BIL",
                        "rebalance": "monthly",
                    }
                singles += 1
            selected.append(s)
            seen.add(s["slug"])
            if len(selected) >= 100:
                break
        if len(selected) >= 100:
            break

    # If still short, add classic parameterized SMA variants on known books from catalog leftovers
    # as extra rows only if we have unique slugs left — else stop.
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "count": len(selected),
        "note": (
            "Each entry is a Quant Buffet in-house reconstruction on liquid ETFs. "
            "Not a bit-identical QuantConnect/LEAN run. Rules mapped from strategy title/code "
            "to templates: sma_trend, dual_ma, dual_momentum, abs_momentum, momentum_rotation, "
            "equal_weight, mean_reversion, risk_parity, vol_target."
        ),
        "strategies": selected[:100],
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("selected", len(payload["strategies"]))
    print("templates", Counter(s["template"] for s in payload["strategies"]))
    assets = Counter(a for s in payload["strategies"] for a in s["assets"])
    print("unique assets", len(assets), assets.most_common(15))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
