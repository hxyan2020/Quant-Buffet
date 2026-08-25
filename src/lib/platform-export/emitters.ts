import type { QbStrategySketch } from "./parse-qb";
import { patternLabel } from "./parse-qb";

export type ExportPlatformId =
  | "quantconnect"
  | "backtrader"
  | "zipline"
  | "vectorbt"
  | "freqtrade"
  | "yfinance_pandas";

export type ExportPlatform = {
  id: ExportPlatformId;
  name: string;
  ide: string;
  blurb: string;
};

export const EXPORT_PLATFORMS: ExportPlatform[] = [
  {
    id: "quantconnect",
    name: "QuantConnect / LEAN",
    ide: "QuantConnect Cloud or LEAN CLI",
    blurb: "QCAlgorithm with Equity securities and monthly rebalance.",
  },
  {
    id: "backtrader",
    name: "Backtrader",
    ide: "Local Python + backtrader",
    blurb: "Cerebro strategy with Yahoo data feeds.",
  },
  {
    id: "zipline",
    name: "Zipline-Reloaded",
    ide: "Local Python + zipline-reloaded",
    blurb: "Pipeline-friendly algorithm with order_target_percent.",
  },
  {
    id: "vectorbt",
    name: "VectorBT",
    ide: "Local Python + vectorbt / vectorbtpro",
    blurb: "Vectorized portfolio from signal matrix.",
  },
  {
    id: "freqtrade",
    name: "Freqtrade",
    ide: "Freqtrade bot / Jupyter",
    blurb: "IStrategy class for crypto or stock pairs.",
  },
  {
    id: "yfinance_pandas",
    name: "yfinance + pandas",
    ide: "Any Python IDE / notebook",
    blurb: "Minimal dependency script — download, signal, equity curve.",
  },
];

function header(sketch: QbStrategySketch, platform: string): string {
  return `# Generated from Quant Buffet → ${platform}
# Strategy: ${sketch.titleHint}
# Detected pattern: ${patternLabel(sketch.pattern)}
# Source uses Quant Buffet lab APIs (ASSETS + make_on_day / PortfolioEngine).
# Review fees, data, and risk before live trading — educational export only.
`;
}

function assetsLit(assets: string[]): string {
  return `[${assets.map((a) => `"${a}"`).join(", ")}]`;
}

function n(params: Record<string, number | string | boolean>, key: string, fallback: number): number {
  const v = params[key];
  return typeof v === "number" ? v : fallback;
}

function s(params: Record<string, number | string | boolean>, key: string, fallback: string): string {
  const v = params[key];
  return typeof v === "string" ? v : fallback;
}

function signalLogicComment(sketch: QbStrategySketch): string {
  switch (sketch.pattern) {
    case "sma_trend":
      return `Long assets where close > SMA(${n(sketch.params, "sma_days", 200)}); equal-weight; monthly.`;
    case "dual_ma":
      return `Long where SMA(${n(sketch.params, "fast", 50)}) > SMA(${n(sketch.params, "slow", 200)}); equal-weight.`;
    case "abs_momentum":
      return `Long assets with positive ${n(sketch.params, "lookback", 252)}-day return; equal-weight; monthly.`;
    case "dual_momentum":
      return `Hold top relative winners if absolute momentum > 0 else ${s(sketch.params, "cash_symbol", "BIL")}.`;
    case "momentum_rotation":
      return `Hold top ${n(sketch.params, "top_n", 1)} by ${n(sketch.params, "lookback", 126)}-day return; monthly.`;
    case "mean_reversion":
      return `Buy when return z-score < ${n(sketch.params, "entry_z", -1)} over ${n(sketch.params, "lookback", 20)} days.`;
    case "equal_weight":
      return `Equal-weight all assets; monthly rebalance.`;
    case "vol_target":
      return `Scale weights to target vol ${n(sketch.params, "target_vol", 0.1)} using ${n(sketch.params, "lookback", 63)}-day vol.`;
    case "risk_parity":
      return `Inverse-volatility weights; lookback ${n(sketch.params, "lookback", 63)}.`;
    default:
      return `Custom Quant Buffet logic — adapt the signal block to match your lab on_day().`;
  }
}

/** Shared signal builder used by pandas-style platforms. */
function pandasSignalBody(sketch: QbStrategySketch): string {
  const a = "assets";
  switch (sketch.pattern) {
    case "sma_trend": {
      const w = n(sketch.params, "sma_days", 200);
      return `
sma = close.rolling(${w}, min_periods=${w}).mean()
signal = (close > sma).astype(float)
signal = signal.div(signal.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)`;
    }
    case "dual_ma": {
      const f = n(sketch.params, "fast", 50);
      const sl = n(sketch.params, "slow", 200);
      return `
fast = close.rolling(${f}, min_periods=${f}).mean()
slow = close.rolling(${sl}, min_periods=${sl}).mean()
signal = (fast > slow).astype(float)
signal = signal.div(signal.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)`;
    }
    case "abs_momentum": {
      const lb = n(sketch.params, "lookback", 252);
      return `
mom = close.pct_change(${lb})
signal = (mom > 0).astype(float)
signal = signal.div(signal.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)`;
    }
    case "dual_momentum": {
      const lb = n(sketch.params, "lookback", 252);
      const cash = s(sketch.params, "cash_symbol", "BIL");
      return `
mom = close.pct_change(${lb})
risky = [c for c in close.columns if c != "${cash}"]
signal = pd.DataFrame(0.0, index=close.index, columns=close.columns)
for dt, row in mom.iterrows():
    candidates = [c for c in risky if pd.notna(row.get(c)) and row[c] > 0]
    if not candidates:
        if "${cash}" in signal.columns:
            signal.loc[dt, "${cash}"] = 1.0
        continue
    best = max(candidates, key=lambda c: row[c])
    signal.loc[dt, best] = 1.0`;
    }
    case "momentum_rotation": {
      const lb = n(sketch.params, "lookback", 126);
      const top = n(sketch.params, "top_n", 1);
      return `
mom = close.pct_change(${lb})
signal = pd.DataFrame(0.0, index=close.index, columns=close.columns)
for dt, row in mom.iterrows():
    ranked = row.dropna().sort_values(ascending=False)
    picks = list(ranked.head(${top}).index)
    if picks:
        w = 1.0 / len(picks)
        for p in picks:
            signal.loc[dt, p] = w`;
    }
    case "mean_reversion": {
      const lb = n(sketch.params, "lookback", 20);
      const ez = n(sketch.params, "entry_z", -1);
      return `
rets = close.pct_change()
mu = rets.rolling(${lb}, min_periods=${lb}).mean()
sd = rets.rolling(${lb}, min_periods=${lb}).std().replace(0, np.nan)
z = (rets - mu) / sd
signal = (z < ${ez}).astype(float)
signal = signal.div(signal.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)`;
    }
    case "vol_target": {
      const lb = n(sketch.params, "lookback", 63);
      const tv = n(sketch.params, "target_vol", 0.1);
      return `
rets = close.pct_change()
vol = rets.rolling(${lb}, min_periods=${lb}).std() * np.sqrt(252)
raw = (${tv} / vol.replace(0, np.nan)).clip(upper=1.0)
signal = raw.div(raw.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)`;
    }
    case "risk_parity": {
      const lb = n(sketch.params, "lookback", 63);
      return `
rets = close.pct_change()
vol = rets.rolling(${lb}, min_periods=${lb}).std().replace(0, np.nan)
inv = 1.0 / vol
signal = inv.div(inv.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)`;
    }
    case "equal_weight":
    default:
      return `
signal = pd.DataFrame(1.0 / len(${a}), index=close.index, columns=close.columns)`;
  }
}

function emitQuantConnect(sketch: QbStrategySketch): string {
  const assets = assetsLit(sketch.assets);
  const sma = n(sketch.params, "sma_days", 200);
  const fast = n(sketch.params, "fast", 50);
  const slow = n(sketch.params, "slow", 200);
  const lb = n(sketch.params, "lookback", 252);
  const top = n(sketch.params, "top_n", 1);
  const cash = s(sketch.params, "cash_symbol", "BIL");
  const entryZ = n(sketch.params, "entry_z", -1);

  let rebalanceBody = "";
  switch (sketch.pattern) {
    case "sma_trend":
      rebalanceBody = `
        longs = []
        for symbol in self.symbols:
            hist = self.History(symbol, ${sma} + 5, Resolution.Daily)
            if hist.empty: continue
            close = hist["close"].unstack(level=0).iloc[:, 0] if hasattr(hist["close"], "unstack") else hist["close"]
            if len(close) < ${sma}: continue
            if float(close.iloc[-1]) > float(close.iloc[-${sma}:].mean()):
                longs.append(symbol)
        weight = 1.0 / len(longs) if longs else 0.0
        for symbol in self.symbols:
            self.SetHoldings(symbol, weight if symbol in longs else 0.0)`;
      break;
    case "dual_ma":
      rebalanceBody = `
        longs = []
        need = ${slow} + 5
        for symbol in self.symbols:
            hist = self.History(symbol, need, Resolution.Daily)
            if hist.empty: continue
            close = hist["close"]
            if hasattr(close, "unstack"):
                close = close.unstack(level=0).iloc[:, 0]
            if len(close) < ${slow}: continue
            if float(close.iloc[-${fast}:].mean()) > float(close.iloc[-${slow}:].mean()):
                longs.append(symbol)
        weight = 1.0 / len(longs) if longs else 0.0
        for symbol in self.symbols:
            self.SetHoldings(symbol, weight if symbol in longs else 0.0)`;
      break;
    case "dual_momentum":
      rebalanceBody = `
        scores = {}
        for symbol in self.symbols:
            hist = self.History(symbol, ${lb} + 5, Resolution.Daily)
            if hist.empty: continue
            close = hist["close"]
            if hasattr(close, "unstack"):
                close = close.unstack(level=0).iloc[:, 0]
            if len(close) < ${lb} + 1: continue
            scores[symbol] = float(close.iloc[-1] / close.iloc[-${lb} - 1] - 1)
        cash = next((s for s in self.symbols if s.Value == "${cash}"), None)
        risky = {s: v for s, v in scores.items() if s.Value != "${cash}" and v > 0}
        for symbol in self.symbols:
            self.SetHoldings(symbol, 0)
        if risky:
            best = max(risky, key=risky.get)
            self.SetHoldings(best, 1.0)
        elif cash is not None:
            self.SetHoldings(cash, 1.0)`;
      break;
    case "momentum_rotation":
      rebalanceBody = `
        scores = {}
        for symbol in self.symbols:
            hist = self.History(symbol, ${lb} + 5, Resolution.Daily)
            if hist.empty: continue
            close = hist["close"]
            if hasattr(close, "unstack"):
                close = close.unstack(level=0).iloc[:, 0]
            if len(close) < ${lb} + 1: continue
            scores[symbol] = float(close.iloc[-1] / close.iloc[-${lb} - 1] - 1)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:${top}]
        for symbol in self.symbols:
            self.SetHoldings(symbol, 0)
        if ranked:
            w = 1.0 / len(ranked)
            for symbol, _ in ranked:
                self.SetHoldings(symbol, w)`;
      break;
    case "mean_reversion":
      rebalanceBody = `
        import numpy as np
        picks = []
        for symbol in self.symbols:
            hist = self.History(symbol, ${n(sketch.params, "lookback", 20)} + 5, Resolution.Daily)
            if hist.empty: continue
            close = hist["close"]
            if hasattr(close, "unstack"):
                close = close.unstack(level=0).iloc[:, 0]
            rets = close.pct_change().dropna()
            if len(rets) < ${n(sketch.params, "lookback", 20)}: continue
            window = rets.iloc[-${n(sketch.params, "lookback", 20)}:]
            z = (window.iloc[-1] - window.mean()) / (window.std() or 1e-9)
            if z < ${entryZ}:
                picks.append(symbol)
        w = 1.0 / len(picks) if picks else 0.0
        for symbol in self.symbols:
            self.SetHoldings(symbol, w if symbol in picks else 0.0)`;
      break;
    case "equal_weight":
      rebalanceBody = `
        w = 1.0 / len(self.symbols) if self.symbols else 0.0
        for symbol in self.symbols:
            self.SetHoldings(symbol, w)`;
      break;
    default:
      rebalanceBody = `
        # Pattern: ${sketch.pattern} — ${signalLogicComment(sketch)}
        # Default: equal-weight. Port your make_on_day weights here via SetHoldings.
        w = 1.0 / len(self.symbols) if self.symbols else 0.0
        for symbol in self.symbols:
            self.SetHoldings(symbol, w)`;
  }

  return `${header(sketch, "QuantConnect LEAN")}
from AlgorithmImports import *


class QuantBuffetExport(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2010, 1, 1)
        self.SetCash(100000)
        tickers = ${assets}
        self.symbols = []
        for t in tickers:
            if "-" in t:  # crypto proxy e.g. BTC-USD
                self.symbols.append(self.AddCrypto(t.replace("-USD", ""), Resolution.Daily).Symbol)
            else:
                self.symbols.append(self.AddEquity(t, Resolution.Daily).Symbol)
        self.Schedule.On(
            self.DateRules.MonthStart(self.symbols[0]),
            self.TimeRules.AfterMarketOpen(self.symbols[0], 30),
            self.Rebalance,
        )
        # Logic: ${signalLogicComment(sketch)}

    def Rebalance(self):${rebalanceBody}
`;
}

function emitBacktrader(sketch: QbStrategySketch): string {
  return `${header(sketch, "Backtrader")}
"""
pip install backtrader yfinance
python this_file.py
"""
from __future__ import annotations

import backtrader as bt
import yfinance as yf

ASSETS = ${assetsLit(sketch.assets)}
# ${signalLogicComment(sketch)}


class QuantBuffetStrategy(bt.Strategy):
    params = dict(
        sma_days=${n(sketch.params, "sma_days", 200)},
        fast=${n(sketch.params, "fast", 50)},
        slow=${n(sketch.params, "slow", 200)},
        lookback=${n(sketch.params, "lookback", 252)},
        top_n=${n(sketch.params, "top_n", 1)},
        entry_z=${n(sketch.params, "entry_z", -1)},
        printlog=False,
    )

    def __init__(self):
        self.last_month = None
        self.inds = {}
        for d in self.datas:
            self.inds[d] = {
                "sma": bt.ind.SMA(d.close, period=self.p.sma_days),
                "fast": bt.ind.SMA(d.close, period=self.p.fast),
                "slow": bt.ind.SMA(d.close, period=self.p.slow),
            }

    def next(self):
        dt = self.datas[0].datetime.date(0)
        key = (dt.year, dt.month)
        if self.last_month == key:
            return
        self.last_month = key

        pattern = "${sketch.pattern}"
        selected = []
        if pattern == "sma_trend":
            selected = [d for d in self.datas if d.close[0] > self.inds[d]["sma"][0]]
        elif pattern == "dual_ma":
            selected = [d for d in self.datas if self.inds[d]["fast"][0] > self.inds[d]["slow"][0]]
        elif pattern in ("abs_momentum", "momentum_rotation", "dual_momentum"):
            scores = []
            for d in self.datas:
                if len(d) > self.p.lookback:
                    ret = d.close[0] / d.close[-self.p.lookback] - 1.0
                    scores.append((ret, d))
            scores.sort(reverse=True, key=lambda x: x[0])
            if pattern == "abs_momentum":
                selected = [d for ret, d in scores if ret > 0]
            elif pattern == "dual_momentum":
                risky = [(ret, d) for ret, d in scores if ret > 0 and d._name != "${s(sketch.params, "cash_symbol", "BIL")}"]
                if risky:
                    selected = [risky[0][1]]
                else:
                    selected = [d for d in self.datas if d._name == "${s(sketch.params, "cash_symbol", "BIL")}"]
            else:
                selected = [d for _, d in scores[: self.p.top_n]]
        else:
            selected = list(self.datas)

        for d in self.datas:
            self.order_target_percent(d, target=0.0)
        if selected:
            w = 1.0 / len(selected)
            for d in selected:
                self.order_target_percent(d, target=w)


if __name__ == "__main__":
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100_000.0)
    cerebro.broker.setcommission(commission=0.0005)
    for t in ASSETS:
        df = yf.download(t, start="2010-01-01", auto_adjust=True, progress=False)
        if df.empty:
            continue
        data = bt.feeds.PandasData(dataname=df, name=t)
        cerebro.adddata(data)
    cerebro.addstrategy(QuantBuffetStrategy)
    print("Starting:", cerebro.broker.getvalue())
    cerebro.run()
    print("Ending:", cerebro.broker.getvalue())
`;
}

function emitZipline(sketch: QbStrategySketch): string {
  return `${header(sketch, "Zipline-Reloaded")}
"""
pip install zipline-reloaded yfinance
# Bundle data per Zipline docs, then:
# zipline run -f this_file.py --start 2015-1-1 --end 2024-12-31 -o result.pickle
"""
from zipline.api import order_target_percent, record, symbol, schedule_function, date_rules, time_rules
from zipline import run_algorithm
import pandas as pd

ASSETS = ${assetsLit(sketch.assets)}
# ${signalLogicComment(sketch)}


def initialize(context):
    context.assets = [symbol(t.replace("-USD", "")) for t in ASSETS if "-" not in t]
    context.lookback = ${n(sketch.params, "lookback", 252)}
    context.sma_days = ${n(sketch.params, "sma_days", 200)}
    context.top_n = ${n(sketch.params, "top_n", 1)}
    context.pattern = "${sketch.pattern}"
    schedule_function(rebalance, date_rules.month_start(), time_rules.market_open(minutes=30))


def rebalance(context, data):
    prices = data.history(context.assets, "price", context.lookback + 5, "1d")
    if prices.empty:
        return
    selected = []
    if context.pattern == "sma_trend":
        for asset in context.assets:
            series = prices[asset].dropna()
            if len(series) < context.sma_days:
                continue
            if series.iloc[-1] > series.iloc[-context.sma_days :].mean():
                selected.append(asset)
    elif context.pattern == "abs_momentum":
        for asset in context.assets:
            series = prices[asset].dropna()
            if len(series) <= context.lookback:
                continue
            if series.iloc[-1] / series.iloc[-context.lookback - 1] - 1 > 0:
                selected.append(asset)
    elif context.pattern == "momentum_rotation":
        scores = []
        for asset in context.assets:
            series = prices[asset].dropna()
            if len(series) <= context.lookback:
                continue
            scores.append((series.iloc[-1] / series.iloc[-context.lookback - 1] - 1, asset))
        scores.sort(reverse=True)
        selected = [a for _, a in scores[: context.top_n]]
    else:
        selected = list(context.assets)

    for asset in context.assets:
        order_target_percent(asset, 0)
    if selected:
        w = 1.0 / len(selected)
        for asset in selected:
            order_target_percent(asset, w)
    record(n_holdings=len(selected))
`;
}

function emitVectorbt(sketch: QbStrategySketch): string {
  return `${header(sketch, "VectorBT")}
"""
pip install vectorbt yfinance
python this_file.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf
import vectorbt as vbt

ASSETS = ${assetsLit(sketch.assets)}
# ${signalLogicComment(sketch)}

raw = yf.download(ASSETS, start="2010-01-01", auto_adjust=True, progress=False)
close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
close = close.dropna(how="all").ffill()
assets = list(close.columns)
${pandasSignalBody(sketch)}

# Monthly rebalance: forward-fill month-start weights
monthly = signal.resample("ME").last().reindex(signal.index, method="ffill").fillna(0.0)
pf = vbt.Portfolio.from_orders(
    close=close,
    size=monthly,
    size_type="targetpercent",
    fees=0.0005,
    freq="1D",
)
print(pf.stats())
pf.plot().show()
`;
}

function emitFreqtrade(sketch: QbStrategySketch): string {
  const pair = sketch.assets[0]?.includes("-")
    ? sketch.assets[0].replace("-USD", "/USDT")
    : `${sketch.assets[0] || "BTC"}/USDT`;
  return `${header(sketch, "Freqtrade")}
# Drop into user_data/strategies/QuantBuffetExport.py
# freqtrade backtesting --strategy QuantBuffetExport
# Note: Freqtrade is crypto-oriented; map ETF ideas to perpetual/spot pairs carefully.

from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class QuantBuffetExport(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1d"
    minimal_roi = {"0": 0.10}
    stoploss = -0.15
    trailing_stop = False
    # Pattern: ${signalLogicComment(sketch)}
    # Example pair whitelist hint: ${pair}

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma_fast"] = ta.SMA(dataframe, timeperiod=${n(sketch.params, "fast", 50)})
        dataframe["sma_slow"] = ta.SMA(dataframe, timeperiod=${n(sketch.params, "sma_days", n(sketch.params, "slow", 200))})
        dataframe["mom"] = dataframe["close"].pct_change(${n(sketch.params, "lookback", 20)})
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pattern = "${sketch.pattern}"
        if pattern in ("sma_trend", "dual_ma"):
            dataframe.loc[
                (dataframe["close"] > dataframe["sma_slow"]) | (dataframe["sma_fast"] > dataframe["sma_slow"]),
                "enter_long",
            ] = 1
        elif pattern == "mean_reversion":
            dataframe.loc[dataframe["mom"] < ${n(sketch.params, "entry_z", -1)} * 0.01, "enter_long"] = 1
        else:
            dataframe.loc[dataframe["mom"] > 0, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["close"] < dataframe["sma_slow"], "exit_long"] = 1
        return dataframe
`;
}

function emitYfinancePandas(sketch: QbStrategySketch): string {
  return `${header(sketch, "yfinance + pandas")}
"""
pip install yfinance pandas numpy
python this_file.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf

ASSETS = ${assetsLit(sketch.assets)}
# ${signalLogicComment(sketch)}

raw = yf.download(ASSETS, start="2010-01-01", auto_adjust=True, progress=False)
close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
close = close.dropna(how="all").ffill()
assets = list(close.columns)
${pandasSignalBody(sketch)}

# Month-end rebalance → daily holdings
weights = signal.resample("ME").last().reindex(close.index, method="ffill").fillna(0.0)
rets = close.pct_change().fillna(0.0)
port = (weights.shift(1).fillna(0.0) * rets).sum(axis=1)
equity = (1 + port).cumprod() * 100_000
cagr = equity.iloc[-1] / equity.iloc[0] ** (252 / max(len(equity), 1)) - 1
print("Assets:", assets)
print("End equity:", round(float(equity.iloc[-1]), 2))
print("Approx days:", len(equity))
print(equity.tail())
`;
}

export function transformToPlatform(sketch: QbStrategySketch, platform: ExportPlatformId): string {
  switch (platform) {
    case "quantconnect":
      return emitQuantConnect(sketch);
    case "backtrader":
      return emitBacktrader(sketch);
    case "zipline":
      return emitZipline(sketch);
    case "vectorbt":
      return emitVectorbt(sketch);
    case "freqtrade":
      return emitFreqtrade(sketch);
    case "yfinance_pandas":
      return emitYfinancePandas(sketch);
    default:
      return emitYfinancePandas(sketch);
  }
}
