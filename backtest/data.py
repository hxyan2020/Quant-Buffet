"""Quant Buffet in-house backtest: market data helpers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pandas as pd
import yfinance as yf

CACHE_DIR = Path(__file__).resolve().parent / "data_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# A Friday close is still valid on Monday. Longer gaps mean the file is not
# the latest Yahoo session and must be downloaded again.
_CACHE_MAX_LAG_DAYS = 4


def _cache_last_date(path: Path) -> pd.Timestamp | None:
    try:
        with path.open("rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            handle.seek(max(0, size - 512))
            tail = handle.read().decode("utf-8", errors="ignore")
        lines = [line.strip() for line in tail.splitlines() if line.strip()]
        if not lines:
            return None
        stamp = lines[-1].split(",")[0].strip()
        if stamp.lower() == "date":
            return None
        parsed = pd.Timestamp(stamp)
        if pd.isna(parsed):
            return None
        if parsed.tzinfo is not None:
            parsed = parsed.tz_convert(None)
        return parsed.normalize()
    except (OSError, ValueError, TypeError):
        return None


def cache_is_fresh(path: Path, *, max_lag_days: int = _CACHE_MAX_LAG_DAYS) -> bool:
    if not path.exists() or path.stat().st_size <= 50:
        return False
    last = _cache_last_date(path)
    if last is None:
        return False
    today = pd.Timestamp.now().normalize()
    return int((today - last).days) <= max_lag_days


def _write_cache(path: Path, series: pd.Series) -> None:
    frame = series.rename("AdjClose").to_frame()
    frame.index.name = "Date"
    tmp = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(tmp)
    tmp.replace(path)


def _download_adjusted_close(symbol: str, start: str, end: str | None) -> pd.Series:
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
    series = close.rename(symbol).dropna()
    if series.empty:
        raise RuntimeError(f"No price data for {symbol}")
    index = pd.to_datetime(series.index)
    if getattr(index, "tz", None) is not None:
        index = index.tz_convert(None)
    series.index = index
    series.name = symbol
    return series


def load_daily_prices(
    symbols: list[str],
    start: str = "2000-01-01",
    end: str | None = None,
    *,
    use_cache: bool = True,
    strict: bool = False,
    on_symbol: Callable[[str, int, int], None] | None = None,
) -> pd.DataFrame:
    """
    Adjusted close panel (columns = tickers), forward-filled within each series
    but not across missing history before a ticker's IPO.
    """
    frames: list[pd.Series] = []
    errors: list[str] = []
    refreshed: list[str] = []
    stale: list[str] = []
    total = len(symbols)
    for index, symbol in enumerate(symbols):
        if on_symbol is not None:
            on_symbol(symbol, index, total)
        cache_symbol = symbol.replace("/", "-").replace("^", "")
        cache = CACHE_DIR / f"{cache_symbol}_{start}_{end or 'latest'}.csv"
        try:
            fresh = use_cache and cache_is_fresh(cache)
            if fresh:
                s = pd.read_csv(cache, parse_dates=["Date"], index_col="Date")["AdjClose"]
            else:
                try:
                    downloaded = _download_adjusted_close(symbol, start, end)
                    previous_rows = 0
                    if cache.exists() and cache.stat().st_size > 50:
                        with cache.open("rb") as handle:
                            previous_rows = max(0, sum(1 for _ in handle) - 1)
                    if previous_rows and len(downloaded) + 5 < previous_rows:
                        raise RuntimeError(
                            f"Yahoo returned {len(downloaded)} rows, shorter than the saved {previous_rows}"
                        )
                    _write_cache(cache, downloaded)
                    s = pd.read_csv(cache, parse_dates=["Date"], index_col="Date")["AdjClose"]
                    refreshed.append(symbol)
                except Exception as download_exc:  # noqa: BLE001
                    if use_cache and cache.exists() and cache.stat().st_size > 50:
                        s = pd.read_csv(cache, parse_dates=["Date"], index_col="Date")["AdjClose"]
                        stale.append(symbol)
                        errors.append(f"{symbol}: refresh failed ({download_exc}); using saved history")
                    else:
                        raise
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
    prices.attrs["data_source"] = "Yahoo Finance adjusted close"
    prices.attrs["refreshed"] = refreshed
    prices.attrs["stale_symbols"] = stale
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
