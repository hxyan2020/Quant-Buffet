"""Code generation helpers for in-house strategy runners."""
from __future__ import annotations

import textwrap

def render_strategy_body(template: str, assets: list[str], params: dict) -> str:
    assets_lit = repr(assets)
    p = params or {}

    if template == "sma_trend":
        sma = int(p.get("sma_days", 200))
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            SMA_DAYS = {sma}

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                sma = prices[cols].rolling(SMA_DAYS, min_periods=SMA_DAYS).mean()
                state = {{"last": None}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    if sma.loc[dt].isna().all():
                        return
                    key = (dt.year, dt.month)
                    if state["last"] == key:
                        return
                    state["last"] = key
                    long = [
                        s for s in cols
                        if pd.notna(prices.at[dt, s]) and pd.notna(sma.at[dt, s])
                        and prices.at[dt, s] > sma.at[dt, s]
                    ]
                    w = {{}} if not long else {{s: 1.0 / len(long) for s in long}}
                    engine.set_target_weights(dt, w)

                ready = sma.dropna(how="all").index.min() if sma.notna().any().any() else None
                return on_day, ready
            """
        )

    if template == "dual_ma":
        fast, slow = int(p.get("fast", 50)), int(p.get("slow", 200))
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            FAST = {fast}
            SLOW = {slow}

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                fast = prices[cols].rolling(FAST, min_periods=FAST).mean()
                slow = prices[cols].rolling(SLOW, min_periods=SLOW).mean()
                state = {{"last": None}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    if slow.loc[dt].isna().all():
                        return
                    if state["last"] == dt.date():
                        return
                    state["last"] = dt.date()
                    long = [
                        s for s in cols
                        if pd.notna(fast.at[dt, s]) and pd.notna(slow.at[dt, s])
                        and fast.at[dt, s] > slow.at[dt, s]
                    ]
                    w = {{}} if not long else {{s: 1.0 / len(long) for s in long}}
                    engine.set_target_weights(dt, w)

                ready = slow.dropna(how="all").index.min() if slow.notna().any().any() else None
                return on_day, ready
            """
        )

    if template == "abs_momentum":
        lb = int(p.get("lookback", 252))
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            LOOKBACK = {lb}

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                rets = prices[cols].pct_change(LOOKBACK)
                state = {{"last": None}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    if rets.loc[dt].isna().all():
                        return
                    key = (dt.year, dt.month)
                    if state["last"] == key:
                        return
                    state["last"] = key
                    long = [s for s in cols if pd.notna(rets.at[dt, s]) and rets.at[dt, s] > 0]
                    w = {{}} if not long else {{s: 1.0 / len(long) for s in long}}
                    engine.set_target_weights(dt, w)

                ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
                return on_day, ready
            """
        )

    if template == "dual_momentum":
        lb = int(p.get("lookback", 252))
        cash = p.get("cash_symbol") or "BIL"
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            LOOKBACK = {lb}
            CASH = {cash!r}

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                if CASH not in cols and CASH in prices.columns:
                    cols = cols + [CASH]
                risky = [c for c in cols if c != CASH]
                rets = prices[cols].pct_change(LOOKBACK)
                state = {{"last": None}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    key = (dt.year, dt.month)
                    if state["last"] == key:
                        return
                    state["last"] = key
                    scores = {{
                        s: float(rets.at[dt, s])
                        for s in risky
                        if s in rets.columns and pd.notna(rets.at[dt, s])
                    }}
                    if not scores:
                        engine.set_target_weights(dt, {{CASH: 1.0}} if CASH in cols else {{}})
                        return
                    best = max(scores, key=scores.get)
                    if scores[best] > 0:
                        engine.set_target_weights(dt, {{best: 1.0}})
                    elif CASH in cols:
                        engine.set_target_weights(dt, {{CASH: 1.0}})
                    else:
                        engine.set_target_weights(dt, {{}})

                ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
                return on_day, ready
            """
        )

    if template == "momentum_rotation":
        lb = int(p.get("lookback", 126))
        top_n = int(p.get("top_n", 1))
        invert = bool(p.get("invert", False))
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            LOOKBACK = {lb}
            TOP_N = {top_n}
            INVERT = {invert!r}  # True = short-term reversal (rank ascending)

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                rets = prices[cols].pct_change(LOOKBACK)
                state = {{"last": None}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    row = rets.loc[dt]
                    if row.isna().all():
                        return
                    key = (dt.year, dt.month)
                    if state["last"] == key:
                        return
                    state["last"] = key
                    ranked = row.dropna().sort_values(ascending=INVERT)
                    picks = list(ranked.head(TOP_N).index)
                    if not INVERT:
                        picks = [s for s in picks if ranked[s] > 0] or picks[:1]
                    w = {{}} if not picks else {{s: 1.0 / len(picks) for s in picks}}
                    engine.set_target_weights(dt, w)

                ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
                return on_day, ready
            """
        )

    if template == "equal_weight":
        once = p.get("rebalance") == "once"
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            REBALANCE_ONCE = {once!r}

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                state = {{"last": None, "done": False}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    available = [s for s in cols if pd.notna(prices.at[dt, s])]
                    if not available:
                        return
                    if REBALANCE_ONCE:
                        if state["done"]:
                            return
                        state["done"] = True
                        engine.set_target_weights(dt, {{s: 1.0 / len(available) for s in available}})
                        return
                    key = (dt.year, dt.month)
                    if state["last"] == key:
                        return
                    state["last"] = key
                    engine.set_target_weights(dt, {{s: 1.0 / len(available) for s in available}})

                counts = prices[cols].notna().sum(axis=1)
                need = max(1, len(cols) // 2)
                eligible = counts[counts >= need]
                ready = eligible.index.min() if not eligible.empty else None
                return on_day, ready
            """
        )

    if template == "mean_reversion":
        lb = int(p.get("lookback", 20))
        entry_z = float(p.get("entry_z", -1.0))
        exit_z = float(p.get("exit_z", 0.0))
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            LOOKBACK = {lb}
            ENTRY_Z = {entry_z}
            EXIT_Z = {exit_z}

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                mu = prices[cols].rolling(LOOKBACK, min_periods=LOOKBACK).mean()
                sd = prices[cols].rolling(LOOKBACK, min_periods=LOOKBACK).std(ddof=0)
                z = (prices[cols] - mu) / sd.replace(0, np.nan)
                held = {{s: False for s in cols}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    long = []
                    for s in cols:
                        zv = z.at[dt, s]
                        if pd.isna(zv):
                            continue
                        if not held[s] and zv <= ENTRY_Z:
                            held[s] = True
                        elif held[s] and zv >= EXIT_Z:
                            held[s] = False
                        if held[s]:
                            long.append(s)
                    w = {{}} if not long else {{s: 1.0 / len(long) for s in long}}
                    engine.set_target_weights(dt, w)

                ready = z.dropna(how="all").index.min() if z.notna().any().any() else None
                return on_day, ready
            """
        )

    if template == "vol_target":
        target = float(p.get("target_vol", 0.10))
        lb = int(p.get("vol_lookback", 63))
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            TARGET_VOL = {target}
            VOL_LOOKBACK = {lb}

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                rets = prices[cols].pct_change()
                vol = rets.rolling(VOL_LOOKBACK, min_periods=VOL_LOOKBACK).std() * np.sqrt(252)
                state = {{"last": None}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    key = (dt.year, dt.month)
                    if state["last"] == key:
                        return
                    state["last"] = key
                    weights = {{}}
                    for s in cols:
                        v = vol.at[dt, s]
                        if pd.isna(v) or v <= 1e-8:
                            continue
                        weights[s] = min(1.0, TARGET_VOL / float(v))
                    total = sum(weights.values())
                    if total > 1.0:
                        weights = {{k: v / total for k, v in weights.items()}}
                    engine.set_target_weights(dt, weights)

                ready = vol.dropna(how="all").index.min() if vol.notna().any().any() else None
                return on_day, ready
            """
        )

    if template == "risk_parity":
        lb = int(p.get("vol_lookback", 63))
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            VOL_LOOKBACK = {lb}

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                rets = prices[cols].pct_change()
                vol = rets.rolling(VOL_LOOKBACK, min_periods=VOL_LOOKBACK).std() * np.sqrt(252)
                state = {{"last": None}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    key = (dt.year, dt.month)
                    if state["last"] == key:
                        return
                    state["last"] = key
                    inv = {{
                        s: 1.0 / float(vol.at[dt, s])
                        for s in cols
                        if pd.notna(vol.at[dt, s]) and vol.at[dt, s] > 1e-8
                    }}
                    total = sum(inv.values())
                    weights = {{k: v / total for k, v in inv.items()}} if total > 0 else {{}}
                    engine.set_target_weights(dt, weights)

                ready = vol.dropna(how="all").index.min() if vol.notna().any().any() else None
                return on_day, ready
            """
        )

    raise ValueError(f"unknown template {template}")


FOOTER = r'''

def main() -> None:
    print(f"[{SLUG}] loading {ASSETS} from Yahoo Finance / cache…")
    prices = load_daily_prices(ASSETS, start="2000-01-01").dropna(how="all")
    on_day, ready = make_on_day(prices)
    if ready is None or pd.isna(ready):
        raise SystemExit("signal never ready — check symbol history")

    engine = PortfolioEngine(
        prices,
        EngineConfig(initial_cash=100_000, commission_bps=5.0, slippage_bps=2.0),
    )
    result = engine.run(on_day, start=ready)

    bench_sym = "SPY" if "SPY" in prices.columns else ASSETS[0]
    spy = prices[bench_sym].reindex(result.equity.index).ffill()
    bh = float(result.equity.iloc[0]) * (spy / spy.iloc[0])
    metrics = compute_metrics(result.equity, benchmark=bh, trades_count=len(result.trades))

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
'''


