# Original QuantConnect / library Python
# locale=en slug="股票收益的12个月周期"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
from typing import List, Dict, Tuple
import pandas as pd

class Month12CycleinCrossSectionofStocksReturns(XXX):

def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)  
    self.SetCash(100_000)

    self.UniverseSettings.Leverage = 5
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0
    
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']
    self.fundamental_count: int = 1_000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.quantile: int = 5
    self.year_period: int = 13
    self.month_period: int = 30
    
    # Monthly close data.
    self.symbol_data: Dict[Symbol, SymbolData] = {}
    self.portfolio_weights: Dict[Symbol, float] = {}
    self.selection_flag: bool = False

    symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthEnd(symbol), 
                    self.TimeRules.BeforeMarketClose(symbol), 
                    self.Selection)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged

    # Update the rolling window every month.
    for f in fundamental:
        if f.Symbol in self.symbol_data:
            self.symbol_data[f.Symbol].update(f.AdjustedPrice)

    filtered: List[Fundamental] = [f for f in fundamental if f.HasFundamentalData
                                    and f.SecurityReference.ExchangeId in self.exchange_codes
                                    and not f.CompanyReference.IsREIT
                                    and f.MarketCap != 0]

    sorted_filter: List[Fundamental] = sorted(filtered,
                                            key=self.fundamental_sorting_key,
                                            reverse=True)[:self.fundamental_count]

    # Warmup price rolling windows.
    for f in sorted_filter:
        if f.Symbol in self.symbol_data:
            continue
        
        self.symbol_data[f.Symbol] = SymbolData(self.year_period)
        history: pd.DataFrame = self.History(f.Symbol, self.year_period * self.month_period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {f.Symbol} yet.")
            continue
        closes: pd.Series = history.loc[f.Symbol].close
        
        # Find monthly closes.
        for index, time_close in enumerate(closes.iteritems()):
            # index out of bounds check.
            if index + 1 = self.quantile:
        sorted_by_perf: List[Tuple[Fundamental, float]] = sorted(performance.items(), key=lambda x: x[1], reverse=True)
        quantile: int = int(len(sorted_by_perf) / self.quantile)
        longs = [x[0] for x in sorted_by_perf[:quantile]]
        shorts = [x[0] for x in sorted_by_perf[-quantile:]]

    # Market cap weighting.
    for i, portfolio in enumerate([longs, shorts]):
        mc_sum: float = sum(map(lambda x: x.MarketCap, portfolio))
        for security in portfolio:
            self.portfolio_weights[security.Symbol] = ((-1) ** i) * security.MarketCap / mc_sum

    return list(self.portfolio_weights.keys())

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())

def OnData(self, slice: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w)
                                        for symbol, w in self.portfolio_weights.items() 
                                        if slice.ContainsKey(symbol) and slice[symbol] is not None]
    self.SetHoldings(portfolio, True)
    self.portfolio_weights.clear()

def Selection(self) -> None:
    self.selection_flag = True

class SymbolData():
def __init__(self, period: int) -> None:
    self.price: RollingWindow = RollingWindow[float](period)

def update(self, value: float) -> None:
    self.price.Add(value)

def is_ready(self) -> bool:
    return self.price.IsReady
    
# One month performance, one year ago.
def performance(self) -> float:
    prices: List[float] = list(self.price)
    return (prices[-2] / prices[-1] - 1)

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
