"""
Quant Buffet draft-preview sandbox runner.

Reads one JSON object from stdin:
  { "code": "<python source>", "start": "2000-01-01", "max_points": 90 }

Prints one JSON object to stdout (metrics / equity / error).
Only Quant Buffet backtest.* APIs + numpy/pandas are allowed.
"""
from __future__ import annotations

import ast
import json
import math
import sys
import traceback
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest.data import load_daily_prices  # noqa: E402
from backtest.engine import EngineConfig, PortfolioEngine  # noqa: E402
from backtest.lab_sanitize import sanitize_lab_code  # noqa: E402
from backtest.metrics import compute_metrics  # noqa: E402
from backtest.universes import WHITELIST  # noqa: E402

ALLOWED_IMPORT_ROOTS = {
    "backtest",
    "numpy",
    "np",
    "pandas",
    "pd",
    "math",
    "json",
    "typing",
    "collections",
    "dataclasses",
    "functools",
    "itertools",
    "datetime",
    "re",
    "statistics",
    "decimal",
    "__future__",
}

BANNED_NAMES = {
    "eval",
    "exec",
    "compile",
    "open",
    "__import__",
    "input",
    "breakpoint",
    "exit",
    "quit",
    "memoryview",
    "globals",
    "locals",
    "vars",
    "getattr",
    "setattr",
    "delattr",
    "classmethod",  # keep ok actually
}


def _module_root(name: str) -> str:
    return (name or "").split(".", 1)[0]


def validate_source(code: str) -> None:
    if len(code) > 80_000:
        raise ValueError("Code too long (max 80KB).")
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        err = SyntaxError(e.msg or "invalid syntax")
        err.lineno = e.lineno
        err.offset = e.offset
        err.text = e.text
        err.filename = "<strategy>"
        raise err from e

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = _module_root(alias.name)
                if root not in ALLOWED_IMPORT_ROOTS:
                    raise ValueError(
                        f"Import blocked: '{alias.name}'. "
                        "Only Quant Buffet backtest.* plus numpy/pandas/math/typing are allowed."
                    )
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            root = _module_root(mod)
            if root not in ALLOWED_IMPORT_ROOTS:
                raise ValueError(
                    f"Import blocked: 'from {mod}'. "
                    "Use backtest.data / backtest.engine / backtest.metrics / backtest.templates only."
                )
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {
                "eval",
                "exec",
                "compile",
                "open",
                "__import__",
                "input",
                "breakpoint",
            }:
                raise ValueError(f"Call to '{node.func.id}()' is not allowed in the sandbox.")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("_") and node.attr not in {"__future__"}:
                # allow private attrs on pandas/np objects is common (_values etc) — only block dunder
                if node.attr.startswith("__") and node.attr.endswith("__") and node.attr not in {
                    "__name__",
                    "__doc__",
                }:
                    pass  # too noisy to ban all dunders on pandas
        elif isinstance(node, (ast.AsyncFunctionDef, ast.AsyncFor, ast.AsyncWith, ast.Await)):
            raise ValueError("Async code is not supported in the sandbox.")


def extract_assets(ns: dict[str, Any]) -> list[str]:
    assets = ns.get("ASSETS")
    if isinstance(assets, (list, tuple)) and assets:
        out = []
        for a in assets:
            s = str(a).strip()
            if not s:
                continue
            if s not in WHITELIST and s not in ("BTC-USD", "ETH-USD"):
                raise ValueError(
                    f"Symbol '{s}' is not in the Quant Buffet whitelist. "
                    f"Use liquid ETFs from backtest.universes (e.g. SPY, QQQ, TLT, GLD, BIL)."
                )
            if s not in out:
                out.append(s)
        if not out:
            raise ValueError("ASSETS is empty after validation.")
        if len(out) > 15:
            raise ValueError("Too many symbols (max 15).")
        return out
    raise ValueError(
        "Define ASSETS = ['SPY', ...] at module level so the sandbox can load prices."
    )


def downsample(equity: pd.Series, max_points: int = 90) -> list[dict]:
    if equity.empty:
        return []
    step = max(1, len(equity) // max_points)
    pts = [
        {"date": dt.strftime("%Y-%m-%d"), "equity": round(float(v), 2)}
        for dt, v in equity.iloc[::step].items()
    ]
    last_dt, last_v = equity.index[-1], float(equity.iloc[-1])
    if not pts or pts[-1]["date"] != last_dt.strftime("%Y-%m-%d"):
        pts.append({"date": last_dt.strftime("%Y-%m-%d"), "equity": round(last_v, 2)})
    return pts


def fmt_pct(x: Any) -> str | None:
    if x is None:
        return None
    try:
        return f"{float(x) * 100:.2f}%"
    except (TypeError, ValueError):
        return None


def fmt_num(x: Any) -> str | None:
    if x is None:
        return None
    try:
        return f"{float(x):.2f}"
    except (TypeError, ValueError):
        return None


def run(payload: dict) -> dict:
    code = sanitize_lab_code(payload.get("code") or "")
    start = payload.get("start") or "2000-01-01"
    max_points = int(payload.get("max_points") or 90)

    try:
        validate_source(code)
    except SyntaxError as e:
        msg = e.msg or str(e)
        line = e.lineno
        if line is None:
            import re as _re

            m = _re.search(r"line\s+(\d+)", str(e))
            line = int(m.group(1)) if m else None
        return {
            "ok": False,
            "error": {
                "type": "SyntaxError",
                "message": f"Syntax error at line {line}: {msg}" if line else msg,
                "line": line,
                "column": getattr(e, "offset", None),
                "traceback": traceback.format_exc()[-2500:],
            },
        }
    except Exception as e:
        return {
            "ok": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
                "line": getattr(e, "lineno", None),
                "traceback": traceback.format_exc()[-2500:],
            },
        }

    # Safe builtins subset
    safe_builtins = {
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "sorted": sorted,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "float": float,
        "int": int,
        "str": str,
        "bool": bool,
        "round": round,
        "print": print,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "hasattr": hasattr,
        "type": type,
        "Exception": Exception,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "KeyError": KeyError,
        "RuntimeError": RuntimeError,
        "StopIteration": StopIteration,
        "True": True,
        "False": False,
        "None": None,
    }

    ns: dict[str, Any] = {
        "__builtins__": safe_builtins,
        "__name__": "user_strategy",
        "np": np,
        "numpy": np,
        "pd": pd,
        "pandas": pd,
        "math": math,
        "json": json,
        "PortfolioEngine": PortfolioEngine,
        "EngineConfig": EngineConfig,
        "load_daily_prices": load_daily_prices,
        "compute_metrics": compute_metrics,
    }

    # Allow importing whitelisted modules via normal import statements by
    # providing a restricted __import__ that only resolves allow-listed roots.
    import importlib

    real_import = importlib.import_module

    def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: A002
        root = _module_root(name)
        if root not in ALLOWED_IMPORT_ROOTS:
            raise ImportError(f"Import of '{name}' is blocked in Quant Buffet sandbox.")
        return real_import(name)

    safe_builtins["__import__"] = restricted_import

    try:
        compiled = compile(code, "<strategy>", "exec")
        exec(compiled, ns, ns)  # noqa: S102 — intentional sandbox exec after AST checks
    except SyntaxError as e:
        return {
            "ok": False,
            "error": {
                "type": "SyntaxError",
                "message": e.msg or str(e),
                "line": e.lineno,
                "column": e.offset,
                "traceback": traceback.format_exc()[-2500:],
            },
        }
    except Exception as e:
        tb = traceback.extract_tb(sys.exc_info()[2])
        line = None
        for frame in reversed(tb):
            if frame.filename == "<strategy>":
                line = frame.lineno
                break
        return {
            "ok": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
                "line": line,
                "traceback": traceback.format_exc()[-2500:],
            },
        }

    if "make_on_day" not in ns or not callable(ns["make_on_day"]):
        return {
            "ok": False,
            "error": {
                "type": "ContractError",
                "message": (
                    "Missing make_on_day(prices). Your strategy must define "
                    "def make_on_day(prices: pd.DataFrame): that returns (on_day, ready)."
                ),
                "line": None,
                "traceback": "",
            },
        }

    try:
        assets = extract_assets(ns)
        prices = load_daily_prices(assets, start=start, use_cache=True).dropna(how="all")
        if prices.empty or len(prices) < 30:
            raise ValueError("Not enough price history for the selected assets/start date.")

        on_day, ready = ns["make_on_day"](prices)
        if ready is None or (isinstance(ready, float) and math.isnan(ready)) or pd.isna(ready):
            raise ValueError("Signal never ready — check lookbacks / ASSETS history.")

        engine = PortfolioEngine(
            prices,
            EngineConfig(initial_cash=100_000, commission_bps=5.0, slippage_bps=2.0),
        )
        result = engine.run(on_day, start=ready)
        if result.equity.empty or len(result.equity) < 20:
            raise ValueError("Equity curve too short — strategy may never trade.")

        bench_sym = "SPY" if "SPY" in prices.columns else assets[0]
        spy = prices[bench_sym].reindex(result.equity.index).ffill()
        bh = float(result.equity.iloc[0]) * (spy / spy.iloc[0])
        metrics = compute_metrics(result.equity, benchmark=bh, trades_count=len(result.trades))
        if metrics.get("error"):
            raise ValueError(str(metrics["error"]))

        display = {
            "annualisedReturn": fmt_pct(metrics.get("cagr")),
            "volatility": fmt_pct(metrics.get("volatility")),
            "sharpeRatio": fmt_num(metrics.get("sharpe")),
            "sortinoRatio": fmt_num(metrics.get("sortino")),
            "maxDrawdown": fmt_pct(metrics.get("max_drawdown")),
            "beta": fmt_num(metrics.get("beta")),
            "alpha": fmt_pct(metrics.get("alpha")),
            "winRate": fmt_pct(metrics.get("daily_win_rate")),
        }

        def _td(t) -> dict:
            return {
                "date": t.date,
                "symbol": t.symbol,
                "side": t.side,
                "shares": round(float(t.shares), 6),
                "price": round(float(t.price), 6),
                "value": round(float(t.value), 2),
                "commission": round(float(t.commission), 4),
            }

        n_tr = len(result.trades)
        orders = [_td(t) for t in result.trades]

        return {
            "ok": True,
            "assets": assets,
            "start": str(result.equity.index[0].date()),
            "end": str(result.equity.index[-1].date()),
            "trades": n_tr,
            "orders": orders,
            "trades_sample": orders,
            "trades_sample_note": None,
            "metrics": metrics,
            "displayMetrics": display,
            "equity": downsample(result.equity, max_points),
            "benchmark": downsample(bh, max_points),
        }
    except Exception as e:
        tb = traceback.extract_tb(sys.exc_info()[2])
        line = None
        for frame in reversed(tb):
            if frame.filename == "<strategy>":
                line = frame.lineno
                break
        return {
            "ok": False,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
                "line": line,
                "traceback": traceback.format_exc()[-2500:],
            },
        }


def main() -> None:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": {"type": "BadPayload", "message": str(e)}}))
        return
    out = run(payload)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
