"""Inventory EN strategies and classify QC code patterns."""
from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from html import unescape
from pathlib import Path

DB = Path("prisma/dev.db")
OUT = Path("backtest/results/strategy_inventory.json")


def strip_html(h: str) -> str:
    t = unescape(h or "")
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def classify(code: str) -> list[str]:
    t = code.lower()
    tags: list[str] = []
    checks = [
        ("sma", r"\bsma\b|movingaverage|moving_avg|simplemovingaverage"),
        ("ema", r"\bema\b|exponentialmovingaverage"),
        ("momentum", r"momentum|rateofchange|\broc\b|returns\("),
        ("rsi", r"\brsi\b|relative strength"),
        ("mean_reversion", r"mean.?revert|z.?score|bollinger"),
        ("bollinger", r"bollinger"),
        ("macd", r"\bmacd\b"),
        ("breakout", r"breakout|donchian|channel"),
        ("pairs", r"pairs|cointegrat|spread"),
        ("options", r"addoption|optionchain|option\."),
        ("futures", r"addfuture|future\."),
        ("algolib", r"algolib|from algos"),
        ("universe", r"coarse|fine.?selection|universe"),
        ("schedule", r"schedule\.|date_rules|time_rules"),
        ("set_holdings", r"set_holdings|setholdings|set_holdings"),
        ("liquidate", r"liquidate"),
    ]
    for name, pat in checks:
        if re.search(pat, t):
            tags.append(name)
    if not tags:
        tags.append("other")
    return tags


def extract_tickers(code: str) -> list[str]:
    # add_equity("SPY") / Equity("SPY") / "SPY"
    found = re.findall(
        r"(?:add_equity|AddEquity|equity|Equity|symbol)\s*\(\s*[\"']([A-Z][A-Z0-9.\-]{0,8})[\"']",
        code,
    )
    found += re.findall(r"[\"']([A-Z]{2,5})[\"']\s*\)", code)
    skip = {
        "TRUE",
        "FALSE",
        "NONE",
        "SELF",
        "HTML",
        "HTTP",
        "HTTPS",
        "JSON",
        "UTC",
        "RESOLUTION",
        "DAILY",
        "MINUTE",
        "HOUR",
        "WEEKLY",
        "MONTHLY",
        "ORDER",
        "TYPE",
        "DATA",
        "BUY",
        "SELL",
        "LONG",
        "SHORT",
        "CASH",
        "USD",
        "QC",
    }
    out = []
    for t in found:
        if t in skip or len(t) < 2:
            continue
        if t not in out:
            out.append(t)
    return out[:20]


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT slug, title, annualisedReturn, sharpeRatio, maxDrawdown,
               volatility, beta, sortinoRatio, winRate, isPaywalled,
               hasPythonCode, length(pythonCodeHtml) AS code_len, pythonCodeHtml
        FROM Strategy
        WHERE locale = 'en' AND published = 1
        ORDER BY isPaywalled ASC, slug
        """
    ).fetchall()

    patterns = Counter()
    ticker_freq = Counter()
    inventory = []
    for r in rows:
        code = strip_html(r["pythonCodeHtml"] or "")
        tags = classify(code) if r["hasPythonCode"] else ["no_code"]
        tickers = extract_tickers(code) if r["hasPythonCode"] else []
        for tag in tags:
            patterns[tag] += 1
        for t in tickers:
            ticker_freq[t] += 1
        complex_ = any(x in tags for x in ("options", "futures", "universe", "algolib", "pairs"))
        inventory.append(
            {
                "slug": r["slug"],
                "title": r["title"],
                "annualisedReturn": r["annualisedReturn"],
                "sharpeRatio": r["sharpeRatio"],
                "maxDrawdown": r["maxDrawdown"],
                "isPaywalled": bool(r["isPaywalled"]),
                "code_len": r["code_len"] or 0,
                "tags": tags,
                "tickers": tickers,
                "simple_etf": bool(
                    r["hasPythonCode"]
                    and not complex_
                    and len(tickers) >= 1
                    and len(tickers) <= 12
                    and (r["code_len"] or 0) < 25000
                ),
            }
        )

    simple = [x for x in inventory if x["simple_etf"]]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "total_en": len(inventory),
        "with_code": sum(1 for x in inventory if "no_code" not in x["tags"]),
        "simple_etf_count": len(simple),
        "patterns": dict(patterns.most_common()),
        "top_tickers": ticker_freq.most_common(50),
        "simple_slugs": [x["slug"] for x in simple[:150]],
        "inventory": inventory,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"total={len(inventory)} simple_etf={len(simple)}")
    print("patterns", patterns.most_common(20))
    print("top tickers", ticker_freq.most_common(25))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
