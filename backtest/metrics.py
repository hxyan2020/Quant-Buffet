"""Performance metrics for Quant Buffet in-house backtests."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _ann_factor(index: pd.DatetimeIndex) -> float:
    if len(index) < 2:
        return 252.0
    years = (index[-1] - index[0]).days / 365.25
    if years <= 0:
        return 252.0
    return len(index) / years


def compute_metrics(
    equity: pd.Series,
    *,
    benchmark: pd.Series | None = None,
    risk_free: float = 0.0,
    trades_count: int = 0,
) -> dict:
    eq = equity.dropna().astype(float)
    if len(eq) < 5:
        return {"error": "insufficient equity points"}

    rets = eq.pct_change().dropna()
    ann = _ann_factor(eq.index)
    total_return = float(eq.iloc[-1] / eq.iloc[0] - 1)
    years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1e-9)
    cagr = float((eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1)
    vol = float(rets.std(ddof=1) * math.sqrt(ann)) if len(rets) > 1 else 0.0
    excess = rets - risk_free / ann
    sharpe = float(excess.mean() / excess.std(ddof=1) * math.sqrt(ann)) if excess.std(ddof=1) > 0 else 0.0

    downside = rets.copy()
    downside[downside > 0] = 0
    downside_std = float(downside.std(ddof=1) * math.sqrt(ann)) if len(downside) > 1 else 0.0
    sortino = float((rets.mean() * ann - risk_free) / downside_std) if downside_std > 0 else 0.0

    peak = eq.cummax()
    dd = eq / peak - 1
    max_dd = float(dd.min())
    calmar = float(cagr / abs(max_dd)) if max_dd < 0 else 0.0

    win_days = float((rets > 0).mean()) if len(rets) else 0.0

    out = {
        "start": eq.index[0].strftime("%Y-%m-%d"),
        "end": eq.index[-1].strftime("%Y-%m-%d"),
        "years": round(years, 2),
        "start_equity": round(float(eq.iloc[0]), 2),
        "end_equity": round(float(eq.iloc[-1]), 2),
        "total_return": round(total_return, 6),
        "cagr": round(cagr, 6),
        "volatility": round(vol, 6),
        "sharpe": round(sharpe, 4),
        "sortino": round(sortino, 4),
        "max_drawdown": round(max_dd, 6),
        "calmar": round(calmar, 4),
        "daily_win_rate": round(win_days, 4),
        "trades": trades_count,
    }

    if benchmark is not None:
        b = benchmark.reindex(eq.index).ffill().dropna()
        aligned = pd.concat([eq.rename("s"), b.rename("b")], axis=1).dropna()
        if len(aligned) > 5:
            sr = aligned["s"].pct_change().dropna()
            br = aligned["b"].pct_change().dropna()
            common = sr.index.intersection(br.index)
            sr, br = sr.loc[common], br.loc[common]
            b_total = float(aligned["b"].iloc[-1] / aligned["b"].iloc[0] - 1)
            b_cagr = float((aligned["b"].iloc[-1] / aligned["b"].iloc[0]) ** (1 / years) - 1)
            cov = np.cov(sr, br)[0, 1]
            var_b = np.var(br, ddof=1)
            beta = float(cov / var_b) if var_b > 0 else 0.0
            alpha = float((sr.mean() - beta * br.mean()) * ann)
            out.update(
                {
                    "benchmark_total_return": round(b_total, 6),
                    "benchmark_cagr": round(b_cagr, 6),
                    "alpha": round(alpha, 6),
                    "beta": round(beta, 4),
                }
            )
    return out
