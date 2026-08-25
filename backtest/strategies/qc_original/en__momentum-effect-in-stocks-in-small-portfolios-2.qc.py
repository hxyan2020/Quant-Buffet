# Original QuantConnect / library Python
# locale=en slug="momentum-effect-in-stocks-in-small-portfolios-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List
import pandas as pd
class MomentumEffectinStocksinSmallPortfolios(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100_000)
    self.UniverseSettings.Leverage = 10
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0
    self.settings.daily_precise_end_time = False
    self.fundamental_count: int = 1_000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.rank_period: int = 12 * 21 # days
    self.quantile: int = 10
    self.month_counter: int = 11
    self.rebalance_period: int = 12 # months
    
    # daily prices
    self.symbol_data: Dict[Symbol, SymbolData] = {}
    self.long_symbols: List[Symbol] = []
    self.short_symbols: List[Symbol] = []
    self.selection_flag: bool = True
    
    market = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthStart(market), 
                    self.TimeRules.AfterMarketOpen(market), 
                    self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the rolling window every day
    for f in fundamental:
        if f.Symbol in self.symbol_data:
            self.symbol_data[f.Symbol].update(f.Price)
    # selection once a month
    if not self.selection_flag:
        return Universe.Unchanged
    filtered: List[Fundamental] = [
        f for f in fundamental if f.HasFundamentalData and f.MarketCap != 0
    ]
    sorted_filter: List[Fundamental] = sorted(filtered,
                                            key=self.fundamental_sorting_key,
                                            reverse=True)[:self.fundamental_count]
    
    # warmup price rolling windows
    for f in sorted_filter:
        if f.Symbol in self.symbol_data:
            continue
        
        self.symbol_data[f.Symbol] = SymbolData(f.Symbol, self.rank_period)
        history: pd.DataFrame = self.History(f.Symbol, self.rank_period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {f.Symbol} yet")
            continue
        closes: pd.Series = history.loc[f.Symbol].close
        for time, close in closes.items():
            self.symbol_data[f.Symbol].update(close)
            
    ready_symbols: List[Symbol] = [f.Symbol for f in sorted_filter 
                                    if self.symbol_data[f.Symbol].is_ready()]
    
    # performance sorting
    performance: Dict[Symbol, float] = {symbol: self.symbol_data[symbol].performance() 
                                        for symbol in ready_symbols}
    if len(performance) >= self.quantile:
        quantile: int = int(len(performance) / self.quantile)
        sorted_by_perf: List[Symbol] = sorted(performance, key=performance.get, reverse=True)
        self.long_symbols = sorted_by_perf[:quantile]
        self.short_symbols = sorted_by_perf[-quantile:]
    
    return self.long_symbols + self.short_symbols
        
def OnData(self, slice: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # trade execution
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long_symbols, self.short_symbols]):
        for symbol in portfolio:
            if slice.ContainsKey(symbol) and slice[symbol] is not None:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    self.SetHoldings(targets, True)
    self.long_symbols.clear()
    self.short_symbols.clear()
    
def Selection(self) -> None:
    # rebalance every 12 months
    if self.month_counter == self.rebalance_period:
        self.selection_flag = True
    self.month_counter += 1
    if self.month_counter > self.rebalance_period: 
        self.month_counter = 1
class SymbolData():
def __init__(self, symbol: Symbol, period: int) -> None:
    self.Symbol: Symbol = symbol
    self.Price: RollingWindow = RollingWindow[float](period)

def update(self, value: float) -> None:
    self.Price.Add(value)

def is_ready(self) -> bool:
    return self.Price.IsReady
    
def performance(self) -> float:
    closes: List[float] = [x for x in self.Price]
    return closes[0] / closes[-1] - 1
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
