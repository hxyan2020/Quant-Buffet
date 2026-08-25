"""Audit stored metrics + sample trade blotters for new_100 and full library."""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backtest.data import load_price_panel  # noqa: E402
from backtest.engine import EngineConfig, PortfolioEngine  # noqa: E402
from backtest.metrics import compute_metrics  # noqa: E402
from backtest.templates import build_strategy  # noqa: E402

NEW = json.loads((ROOT / "backtest/drafts/new_100/backtest_summary.json").read_text(encoding="utf-8"))
FULL = json.loads((ROOT / "backtest/results/batch_full_summary.json").read_text(encoding="utf-8"))
CURVES = ROOT / "backtest/drafts/new_100/equity_curves"
POSTS = ROOT / "backtest/drafts/new_100/posts"
CATALOG = json.loads((ROOT / "backtest/catalog/strategies_full.json").read_text(encoding="utf-8"))
OUT = ROOT / "backtest/drafts/metrics_trade_audit.json"


def pct(x):
    return None if x is None else round(float(x) * 100, 2)


def parse_site_pct(s):
    if not s or not isinstance(s, str):
        return None
    t = s.strip().replace("%", "")
    try:
        return float(t) / 100.0
    except ValueError:
        return None


def identity_ok(m: dict, tol=2e-3) -> list[str]:
    flags = []
    if not m:
        return ["missing_metrics"]
    start_eq = m.get("start_equity")
    end_eq = m.get("end_equity")
    years = m.get("years")
    cagr = m.get("cagr")
    tot = m.get("total_return")
    dd = m.get("max_drawdown")
    vol = m.get("volatility")
    sharpe = m.get("sharpe")
    wr = m.get("daily_win_rate")
    trades = m.get("trades")
    if start_eq is None or end_eq is None or not years:
        flags.append("missing_equity_or_years")
        return flags
    if start_eq <= 0 or end_eq <= 0:
        flags.append("nonpositive_equity")
    if not (90_000 <= start_eq <= 101_000):
        flags.append(f"start_equity_odd:{start_eq}")
    implied_tot = end_eq / start_eq - 1
    if tot is not None and abs(implied_tot - tot) > 0.01:
        flags.append("total_return_mismatch")
    implied_cagr = (end_eq / start_eq) ** (1 / max(years, 1e-9)) - 1
    if cagr is not None and abs(implied_cagr - cagr) > tol:
        flags.append("cagr_identity_fail")
    if dd is not None and not (-1.0001 <= dd <= 0.001):
        flags.append(f"max_dd_out_of_range:{dd}")
    if vol is not None and vol < -1e-9:
        flags.append("negative_vol")
    if vol is not None and vol > 2.5:
        flags.append(f"extreme_vol:{vol:.2f}")
    if sharpe is not None and (not math.isfinite(sharpe) or abs(sharpe) > 8):
        flags.append(f"extreme_sharpe:{sharpe}")
    if wr is not None and not (0 <= wr <= 1):
        flags.append(f"winrate_out_of_range:{wr}")
    if trades is not None and trades < 0:
        flags.append("negative_trades")
    if years is not None and years < 0.4:
        flags.append(f"short_window:{years}")
    if cagr is not None and cagr > 1.5:
        flags.append(f"extreme_cagr:{cagr:.2f}")
    if cagr is not None and cagr < -0.5:
        flags.append(f"extreme_neg_cagr:{cagr:.2f}")
    beta = m.get("beta")
    if beta is not None and abs(beta) > 4:
        flags.append(f"extreme_beta:{beta}")
    return flags


def fingerprint(m: dict, template: str, assets) -> str:
    assets_key = ",".join(sorted(assets or []))
    return f"{template}|{assets_key}|{round(m.get('cagr') or 0, 5)}|{round(m.get('sharpe') or 0, 3)}|{m.get('trades')}"


def audit_rows(rows: list[dict], source: str) -> dict:
    flags_all = []
    cagrs, sharpes, dds, trades, vols, wrs = [], [], [], [], [], []
    zero_trades = 0
    ok = 0
    err = 0
    fp = defaultdict(list)
    site_gap = []
    for r in rows:
        if r.get("status") != "ok":
            err += 1
            flags_all.append({"source": source, "slug": r.get("slug"), "issue": r.get("error") or "not_ok"})
            continue
        ok += 1
        m = r.get("metrics") or {}
        issues = identity_ok(m)
        assets = r.get("assets") or r.get("assets_used") or []
        fp[fingerprint(m, r.get("template") or "?", assets)].append(r.get("slug") or r.get("file_key"))
        if m.get("trades") == 0:
            zero_trades += 1
            issues.append("zero_trades")
        # monthly-ish: too few / too many trades
        years = m.get("years") or 0
        n_assets = max(len(assets), 1)
        t = m.get("trades") or 0
        if years >= 3 and t > 0:
            # monthly rebalance upper: ~2 sides * n_assets * 12 * years * 1.5 slack
            hi = n_assets * 12 * years * 4
            lo = max(2, years * 0.5)
            if t > hi:
                issues.append(f"trades_too_many:{t}")
            if t < lo:
                issues.append(f"trades_too_few:{t}")
        if m.get("cagr") is not None:
            cagrs.append(m["cagr"])
        if m.get("sharpe") is not None:
            sharpes.append(m["sharpe"])
        if m.get("max_drawdown") is not None:
            dds.append(m["max_drawdown"])
        if m.get("trades") is not None:
            trades.append(m["trades"])
        if m.get("volatility") is not None:
            vols.append(m["volatility"])
        if m.get("daily_win_rate") is not None:
            wrs.append(m["daily_win_rate"])
        site_c = parse_site_pct(r.get("site_annualisedReturn") or r.get("site_cagr"))
        if site_c is not None and m.get("cagr") is not None:
            gap = abs(m["cagr"] - site_c)
            if gap > 0.10:
                site_gap.append(
                    {
                        "slug": r.get("slug"),
                        "title": (r.get("title") or "")[:70],
                        "site_cagr": round(site_c * 100, 2),
                        "recon_cagr": round(m["cagr"] * 100, 2),
                        "gap_pp": round(gap * 100, 1),
                        "template": r.get("template"),
                        "assets": assets[:6],
                    }
                )
        for iss in issues:
            flags_all.append(
                {
                    "source": source,
                    "slug": r.get("slug") or r.get("file_key"),
                    "title": (r.get("title") or "")[:70],
                    "issue": iss,
                    "cagr": pct(m.get("cagr")),
                    "sharpe": m.get("sharpe"),
                    "max_dd": pct(m.get("max_drawdown")),
                    "trades": m.get("trades"),
                    "template": r.get("template"),
                }
            )

    clones = []
    for k, slugs in fp.items():
        if len(slugs) >= 3:
            clones.append({"fingerprint": k, "n": len(slugs), "examples": slugs[:8]})
    clones.sort(key=lambda x: -x["n"])

    def q(xs, p):
        if not xs:
            return None
        s = sorted(xs)
        i = min(len(s) - 1, max(0, int(round((len(s) - 1) * p))))
        return s[i]

    return {
        "n": len(rows),
        "ok": ok,
        "errors": err,
        "zero_trades": zero_trades,
        "flag_count": len(flags_all),
        "flagged_slugs": len({f["slug"] for f in flags_all}),
        "dist": {
            "cagr_p10": pct(q(cagrs, 0.1)),
            "cagr_p50": pct(q(cagrs, 0.5)),
            "cagr_p90": pct(q(cagrs, 0.9)),
            "sharpe_p10": None if not sharpes else round(q(sharpes, 0.1), 2),
            "sharpe_p50": None if not sharpes else round(q(sharpes, 0.5), 2),
            "sharpe_p90": None if not sharpes else round(q(sharpes, 0.9), 2),
            "dd_p10": pct(q(dds, 0.1)),
            "dd_p50": pct(q(dds, 0.5)),
            "dd_p90": pct(q(dds, 0.9)),
            "trades_p50": None if not trades else int(q(trades, 0.5)),
            "vol_p50": pct(q(vols, 0.5)),
            "daily_win_p50": pct(q(wrs, 0.5)),
        },
        "clone_clusters": clones[:12],
        "site_gap_n": len(site_gap),
        "site_gap_top": sorted(site_gap, key=lambda x: -x["gap_pp"])[:12],
        "flags_sample": flags_all[:40],
        "issue_counts": dict(Counter(f["issue"].split(":")[0] for f in flags_all)),
    }


def check_curves(rows: list[dict]) -> dict:
    mismatch = 0
    missing = 0
    samples = []
    for r in rows:
        slug = r.get("slug")
        m = r.get("metrics") or {}
        path = CURVES / f"{slug}.json"
        if not path.exists():
            missing += 1
            continue
        curve = json.loads(path.read_text(encoding="utf-8"))
        eq = curve.get("equity") or []
        if not eq:
            missing += 1
            continue
        last = eq[-1]["equity"]
        first = eq[0]["equity"]
        if abs(first - (m.get("start_equity") or 0)) > 1.0:
            mismatch += 1
            samples.append({"slug": slug, "kind": "start", "curve": first, "metrics": m.get("start_equity")})
        if abs(last - (m.get("end_equity") or 0)) > 1.0:
            mismatch += 1
            samples.append({"slug": slug, "kind": "end", "curve": last, "metrics": m.get("end_equity")})
    return {"missing_curves": missing, "endpoint_mismatch": mismatch, "samples": samples[:8]}


def check_posts_winrate() -> dict:
    n = 0
    null_wr = 0
    for f in POSTS.glob("*.json"):
        n += 1
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("winRate") in (None, "", "n/a"):
            null_wr += 1
    return {"posts": n, "winRate_null": null_wr}


def replay(spec: dict, prices: pd.DataFrame) -> dict:
    assets = [a for a in spec["assets"] if a in prices.columns]
    px = prices[assets].copy()
    on_day, ready = build_strategy(spec["template"], px, assets, spec.get("params") or {})
    engine = PortfolioEngine(px, EngineConfig(initial_cash=100_000, commission_bps=5.0, slippage_bps=2.0))
    result = engine.run(on_day, start=ready)
    trades = result.trades
    issues = []
    comm_bad = 0
    for t in trades:
        if t.shares <= 0 or t.price <= 0 or t.value < 0:
            issues.append("nonpositive_fill")
            break
        if t.side not in ("buy", "sell"):
            issues.append("bad_side")
            break
        expect = t.value * 0.0005
        if abs(t.commission - expect) > max(0.02, 0.05 * expect + 0.01):
            comm_bad += 1
    if comm_bad:
        issues.append(f"commission_mismatch_n={comm_bad}")
    if result.cash.min() < -1.0:
        issues.append(f"negative_cash:{float(result.cash.min()):.2f}")
    if (result.equity <= 0).any():
        issues.append("nonpositive_equity_path")
    # buy/sell balance per symbol
    from collections import defaultdict as dd

    net = dd(float)
    for t in trades:
        net[t.symbol] += t.shares if t.side == "buy" else -t.shares
    leftover = {s: round(v, 4) for s, v in net.items() if abs(v) > 1.0}
    # leftover shares at end is OK (open positions); just record
    m = compute_metrics(result.equity, trades_count=len(trades))
    sample = [
        {
            "date": t.date,
            "symbol": t.symbol,
            "side": t.side,
            "shares": t.shares,
            "price": t.price,
            "value": t.value,
            "commission": t.commission,
        }
        for t in trades[:4] + trades[-3:]
    ]
    months = {t.date[:7] for t in trades}
    return {
        "slug": spec.get("slug") or spec.get("title"),
        "template": spec["template"],
        "assets": assets,
        "n_trades": len(trades),
        "n_trade_months": len(months),
        "start": str(result.equity.index[0].date()),
        "end": str(result.equity.index[-1].date()),
        "start_equity": round(float(result.equity.iloc[0]), 2),
        "end_equity": round(float(result.equity.iloc[-1]), 2),
        "cagr": round(m["cagr"], 4),
        "sharpe": m["sharpe"],
        "max_dd": round(m["max_drawdown"], 4),
        "daily_win_rate": m["daily_win_rate"],
        "min_cash": round(float(result.cash.min()), 2),
        "open_share_net": leftover,
        "issues": issues,
        "sample_trades": sample,
    }


def main() -> None:
    new_rows = NEW.get("results") or []
    full_rows = FULL.get("results") or []
    new_audit = audit_rows(new_rows, "new100")
    full_audit = audit_rows(full_rows, "library")
    curves = check_curves(new_rows)
    posts = check_posts_winrate()

    # Replay sample blotters
    catalog_by_slug = {
        s["slug"]: s
        for s in (CATALOG.get("strategies") or [])
        if isinstance(s, dict) and s.get("slug")
    }
    samples_specs = []
    for row in new_rows:
        if row.get("template") in {"sma_trend", "vol_target", "abs_momentum", "mean_reversion", "risk_parity", "momentum_rotation", "dual_momentum", "equal_weight"}:
            if not any(s.get("template") == row["template"] for s in samples_specs):
                samples_specs.append(
                    {
                        "slug": row["slug"],
                        "title": row["title"],
                        "template": row["template"],
                        "assets": row["assets"],
                        "params": row.get("params") or {},
                    }
                )
    for slug in ["1-month-momentum-in-bonds", "hedging-factor-in-cryptocurrencies", "bitcoin-intraday-momentum"]:
        spec = catalog_by_slug.get(slug)
        if spec:
            samples_specs.append(spec)

    all_assets = sorted({a for s in samples_specs for a in s.get("assets") or []})
    panel, _missing = load_price_panel(all_assets, start="2000-01-01")
    blotters = []
    for spec in samples_specs:
        try:
            blotters.append(replay(spec, panel))
        except Exception as exc:  # noqa: BLE001
            blotters.append({"slug": spec.get("slug"), "issues": [f"replay_fail:{exc}"]})

    payload = {
        "new100": new_audit,
        "library": full_audit,
        "curves": curves,
        "posts_winrate": posts,
        "blotters": blotters,
        "notes": {
            "win_rate_definition": "metrics.daily_win_rate is share of DAYS with positive equity change, not trade-level win rate. Cash/flat days count as losses/non-wins, so SMA strategies often show ~30%.",
            "winRate_field": "new_100 posts write winRate from metrics['win_rate'] which does not exist; field is null.",
            "start_equity": "First mark is after the opening rebalance, so start_equity is ~100000 minus 7bps (5 commission + 2 slip).",
            "clones": "Identical (template, assets, cagr, sharpe, trades) means many papers share one ETF proxy.",
        },
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    print("new100 flags", new_audit["flag_count"], "issues", new_audit["issue_counts"])
    print("library flags", full_audit["flag_count"], "issues", full_audit["issue_counts"])
    print("clones new", len(new_audit["clone_clusters"]), "lib", len(full_audit["clone_clusters"]))
    print("site gaps", full_audit["site_gap_n"])
    print("curves", curves)
    print("posts", posts)
    for b in blotters:
        print("blotter", b.get("slug"), "trades", b.get("n_trades"), "issues", b.get("issues"))


if __name__ == "__main__":
    main()
