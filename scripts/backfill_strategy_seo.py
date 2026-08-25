"""Backfill strategy SEO meta via sqlite3 (works without Prisma path quirks)."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

SITE = "Quant Buffet"
DRY = "--dry-run" in sys.argv


def clip(text: str, max_len: int) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_len:
        return clean
    sliced = clean[: max_len - 1]
    last = sliced.rfind(" ")
    return ((sliced[:last] if last > 40 else sliced).rstrip()) + "…"


def metric(label: str, value: str | None) -> str | None:
    if not value or not value.strip() or value.strip().upper() == "N/A":
        return None
    return f"{label} {value.strip()}"


def build(row: sqlite3.Row) -> tuple[str, str]:
    is_zh = row["locale"] == "zh"
    asset = (row["assetClass"] or "").split(",")[0].strip() or ("多资产" if is_zh else "multi-asset")
    region = (row["region"] or "").strip() or ("全球" if is_zh else "global")
    market = (row["market"] or "").strip() or ("市场" if is_zh else "markets")
    core = clip(
        f"{row['title']}｜{asset}量化策略" if is_zh else f"{row['title']} | {asset} Quant Strategy",
        48,
    )
    title = f"{core} | {SITE}"
    teaser = (row["teaser"] or "").strip()
    useful = clip(teaser, 90) if teaser and teaser.upper() != "N/A" and len(teaser) > 40 else None
    bits = [
        useful,
        f"{region}{market}量化交易策略（{asset}）" if is_zh else f"{region} {market} quant strategy ({asset})",
        (f"调仓：{row['frequency']}" if is_zh else f"{row['frequency']} rebalance") if row["frequency"] else None,
        metric("年化" if is_zh else "ann.", row["annualisedReturn"]),
        metric("夏普" if is_zh else "Sharpe", row["sharpeRatio"]),
        "含学术依据与 QuantConnect/LEAN Python 实现。" if is_zh else "Academic rationale + QuantConnect/LEAN Python.",
    ]
    return title, clip(" · ".join(b for b in bits if b), 160)


def main() -> None:
    db = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else Path("prisma/dev.db")
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        select id, title, locale, teaser, assetClass, region, market, frequency,
               annualisedReturn, sharpeRatio, metaTitle, metaDescription
        from Strategy where published = 1
        """
    ).fetchall()
    updated = 0
    for row in rows:
        title, desc = build(row)
        if row["metaTitle"] == title and row["metaDescription"] == desc:
            continue
        updated += 1
        if DRY:
            if updated <= 2:
                print("---", row["locale"], row["title"])
                print(title)
                print(desc)
            continue
        con.execute(
            "update Strategy set metaTitle=?, metaDescription=?, updatedAt=CURRENT_TIMESTAMP where id=?",
            (title, desc, row["id"]),
        )
    if not DRY:
        con.commit()
    print(f"{'Would update' if DRY else 'Updated'} {updated} / {len(rows)} in {db}")
    con.close()


if __name__ == "__main__":
    main()
