"""Quant Buffet in-house backtest: market data helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf

CACHE_DIR = Path(__file__).resolve().parent / "data_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_daily_prices(
    symbols: list[str],
    start: str = "2000-01-01",
    end: str | None = None,
    *,
    use_cache: bool = True,
    strict: bool = False,
) -> pd.DataFrame:
    """
    Adjusted close panel (columns = tickers), forward-filled within each series
    but not across missing history before a ticker's IPO.
    """
    frames: list[pd.Series] = []
    errors: list[str] = []
    for symbol in symbols:
        cache_symbol = symbol.replace("/", "-").replace("^", "")
        cache = CACHE_DIR / f"{cache_symbol}_{start}_{end or 'latest'}.csv"
        try:
            if use_cache and cache.exists() and cache.stat().st_size > 50:
                s = pd.read_csv(cache, parse_dates=["Date"], index_col="Date")["AdjClose"]
            else:
                raw = yf.download(
                    symbol,
                    start=start,
                    end=end,
                    auto_adjust=True,
                    progress=False,
                    threads=False,
                )
                if raw is None or raw.empty:
                    raise RuntimeError(f"No price data for {symbol}")
                if isinstance(raw.columns, pd.MultiIndex):
                    close = raw["Close"]
                    if isinstance(close, pd.DataFrame):
                        close = close.iloc[:, 0]
                else:
                    close = raw["Close"]
                s = close.rename(symbol).dropna()
                s.index = pd.to_datetime(s.index).tz_localize(None)
                out = s.rename("AdjClose").to_frame()
                out.index.name = "Date"
                out.to_csv(cache)
                s = out["AdjClose"]
            s.name = symbol
            if s.dropna().empty:
                raise RuntimeError(f"Empty series for {symbol}")
            frames.append(s)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{symbol}: {exc}")
            if strict:
                raise

    if not frames:
        raise RuntimeError(f"No price data loaded. Errors: {errors[:5]}")

    prices = pd.concat(frames, axis=1).sort_index()
    prices = prices.apply(lambda col: col.ffill())
    if errors:
        prices.attrs["load_errors"] = errors
    return prices


def load_price_panel(
    symbols: list[str],
    start: str = "2000-01-01",
    end: str | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Load prices; return (panel, missing_symbols)."""
    unique = list(dict.fromkeys(symbols))
    prices = load_daily_prices(unique, start=start, end=end, strict=False)
    missing = [s for s in unique if s not in prices.columns]
    return prices, missing
