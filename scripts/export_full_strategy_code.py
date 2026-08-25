"""
Export in-house runners + preserved QC originals for the FULL catalog.

Reads: backtest/catalog/strategies_full.json
Writes:
  backtest/strategies/generated/{file_key}.py
  backtest/strategies/qc_original/{file_key}.qc.py | .MISSING.txt
  backtest/strategies/INDEX.json
  backtest/strategies/CATALOG.md  (paths + data sources; full code lives in generated/)
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backtest.codegen import FOOTER, render_strategy_body  # noqa: E402

CATALOG = ROOT / "backtest" / "catalog" / "strategies_full.json"
DB = ROOT / "prisma" / "dev.db"
OUT_IH = ROOT / "backtest" / "strategies" / "generated"
OUT_QC = ROOT / "backtest" / "strategies" / "qc_original"
INDEX = ROOT / "backtest" / "strategies" / "INDEX.json"
CATALOG_MD = ROOT / "backtest" / "strategies" / "CATALOG.md"


def strip_html(h: str) -> str:
    t = unescape(h or "")
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"</p>", "\n\n", t, flags=re.I)
    t = re.sub(r"</div>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("\xa0", " ")
    return t.strip() + ("\n" if t.strip() else "")


def build_header(
    *,
    file_key: str,
    slug: str,
    locale: str,
    title: str,
    template: str,
    fidelity: str,
    assets: list[str],
    has_qc: bool,
) -> str:
    qc_note = (
        f"Preserved unchanged at:\n  backtest/strategies/qc_original/{file_key}.qc.py"
        if has_qc
        else (
            "No QuantConnect / AlgoLib source was stored for this strategy in the DB.\n"
            "This in-house file is a theme-based reconstruction (see Fidelity)."
        )
    )
    assets_repr = repr(assets)
    return f'''\
"""
Quant Buffet IN-HOUSE backtest — {slug} [{locale}]
file_key: {file_key}
Title: {title}
Template: {template}
Fidelity: {fidelity}
Has QC source in DB: {has_qc}

DATA SOURCE
-----------
Provider : Yahoo Finance via yfinance (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{{SYMBOL}}_2000-01-01_latest.csv
Symbols  : {assets}
Start    : 2000-01-01 (actual start = IPO + signal warmup)
Costs    : 5 bps commission + 2 bps slippage (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
{qc_note}

Run from repo root:
  python backtest/strategies/generated/{file_key}.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest.data import load_daily_prices
from backtest.engine import EngineConfig, PortfolioEngine
from backtest.metrics import compute_metrics

SLUG = {slug!r}
LOCALE = {locale!r}
FILE_KEY = {file_key!r}
TITLE = {title!r}
TEMPLATE = {template!r}
FIDELITY = {fidelity!r}
DATA_SOURCE = {{
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": {assets_repr},
    "history_start": "2000-01-01",
}}

'''


def load_qc_map() -> dict[tuple[str, str], str]:
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT locale, slug, pythonCodeHtml FROM Strategy WHERE published=1"
    ).fetchall()
    return {(locale, slug): strip_html(html or "") for locale, slug, html in rows}


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    qc_map = load_qc_map()
    OUT_IH.mkdir(parents=True, exist_ok=True)
    OUT_QC.mkdir(parents=True, exist_ok=True)
    (OUT_IH / "__init__.py").write_text(
        '"""Generated in-house strategy runners (full library)."""\n',
        encoding="utf-8",
    )

    # Remove old slug-only generated files that conflict? Keep all; new keys are locale__*
    index_rows = []
    md_lines = [
        "# Quant Buffet full strategy catalog\n",
        f"Total: **{catalog['count']}** published strategies (EN + ZH).\n\n",
        "Full in-house Python: `backtest/strategies/generated/{file_key}.py`  \n",
        "QC original (or MISSING marker): `backtest/strategies/qc_original/`  \n",
        "Machine index: `INDEX.json`  \n\n",
        "| file_key | locale | template | QC? | symbols | fidelity |\n",
        "|---|---|---|---|---|---|\n",
    ]

    n = len(catalog["strategies"])
    for i, spec in enumerate(catalog["strategies"], 1):
        file_key = spec["file_key"]
        slug = spec["slug"]
        locale = spec["locale"]
        title = (spec["title"] or slug).replace('"', "'")
        template = spec["template"]
        assets = spec["assets"]
        fidelity = spec["fidelity"]
        params = spec.get("params") or {}
        has_qc_flag = bool(spec.get("has_qc_source"))
        qc = qc_map.get((locale, slug), "")
        has_qc = has_qc_flag and bool(qc.strip())

        qc_path = OUT_QC / f"{file_key}.qc.py"
        miss_path = OUT_QC / f"{file_key}.MISSING.txt"
        if has_qc:
            qc_path.write_text(
                f"# Original QuantConnect / library Python\n"
                f'# locale={locale} slug="{slug}"\n'
                f"# Extracted from Strategy.pythonCodeHtml — NOT modified.\n\n"
                + qc,
                encoding="utf-8",
            )
            if miss_path.exists():
                miss_path.unlink()
        else:
            miss_path.write_text(
                f"No QuantConnect pythonCodeHtml in DB for locale={locale} slug={slug}\n"
                f"In-house reconstruction: backtest/strategies/generated/{file_key}.py\n"
                f"Fidelity: {fidelity}\n",
                encoding="utf-8",
            )
            if qc_path.exists():
                qc_path.unlink()

        body = render_strategy_body(template, assets, params)
        header = build_header(
            file_key=file_key,
            slug=slug,
            locale=locale,
            title=title,
            template=template,
            fidelity=fidelity,
            assets=assets,
            has_qc=has_qc,
        )
        footer = FOOTER.replace(
            'out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"',
            'out = ROOT / "backtest" / "results" / "per_strategy" / f"{FILE_KEY}.json"',
        ).replace(
            'f"backtest/strategies/qc_original/{SLUG}.qc.py"',
            'f"backtest/strategies/qc_original/{FILE_KEY}.qc.py"',
        )
        ih_path = OUT_IH / f"{file_key}.py"
        ih_path.write_text(header + "\n" + body + footer, encoding="utf-8")

        index_rows.append(
            {
                "file_key": file_key,
                "id": spec.get("id"),
                "slug": slug,
                "locale": locale,
                "title": spec["title"],
                "template": template,
                "fidelity": fidelity,
                "has_qc_source": has_qc,
                "assets": assets,
                "params": params,
                "data_source": {
                    "provider": "Yahoo Finance",
                    "library": "yfinance",
                    "field": "adjusted close (auto_adjust=True)",
                    "loader": "backtest.data.load_daily_prices",
                    "cache_dir": "backtest/data_cache",
                    "symbols": assets,
                    "history_start": "2000-01-01",
                },
                "in_house_python": f"backtest/strategies/generated/{file_key}.py",
                "quantconnect_python": (
                    f"backtest/strategies/qc_original/{file_key}.qc.py"
                    if has_qc
                    else f"backtest/strategies/qc_original/{file_key}.MISSING.txt"
                ),
            }
        )
        sym = ",".join(assets[:6]) + ("…" if len(assets) > 6 else "")
        md_lines.append(
            f"| `{file_key}` | {locale} | {template} | {'yes' if has_qc else 'no'} | {sym} | {fidelity} |\n"
        )

        if i % 250 == 0 or i == n:
            print(f"  exported {i}/{n}", flush=True)

    INDEX.write_text(
        json.dumps(
            {
                "count": len(index_rows),
                "stats": catalog.get("stats"),
                "in_house_libraries": [
                    "backtest/data.py",
                    "backtest/engine.py",
                    "backtest/metrics.py",
                    "backtest/templates.py",
                    "backtest/universes.py",
                    "backtest/codegen.py",
                ],
                "data_source_default": {
                    "provider": "Yahoo Finance",
                    "library": "yfinance",
                    "field": "adjusted close",
                    "cache": "backtest/data_cache/",
                },
                "strategies": index_rows,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    CATALOG_MD.write_text("".join(md_lines), encoding="utf-8")
    print("wrote", INDEX)
    print("wrote", CATALOG_MD)
    print("generated py:", len(list(OUT_IH.glob("*.py"))) - 1)
    print("qc files:", len(list(OUT_QC.glob("*.qc.py"))))
    print("missing markers:", len(list(OUT_QC.glob("*.MISSING.txt"))))


if __name__ == "__main__":
    main()
