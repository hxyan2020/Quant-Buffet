# Original QuantConnect / library Python
# locale=zh slug="股票回报横截面中的月末效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.tseries.offsets import BDay
from pandas.tseries.offsets import BMonthEnd
from typing import List, Dict, Tuple
#endregion
class TOTMCrossSection(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.leverage:int = 5
    self.quantile:int = 10
    self.min_share_price:int = 5
    self.offset_days:int = 4
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.fundamental_count:int = 1000
    self.selection_flag:bool = False 
    self.traded_this_month:bool = True
    
    self.data:Dict[Symbol, SymbolData] = {}
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    self.period:int = 5 # T-8 to T-4
    
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.close_days:int = 0
    self.close_flag:bool = False
    
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    self.close_days = 0
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    performances:Dict[Symbol, float] = {}     
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes:Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
        if self.data[symbol].is_ready():
            performances[symbol] = self.data[symbol].performance() # T-8 to T-4
    # Sort stocks based on performance        
    sorted_by_performance:List[Tuple[Symbol, float]] = sorted(performances.items(), key=lambda item: item[1], reverse=True)
    quantile:int = int(len(sorted_by_performance) / self.quantile)
    
    self.short = [x[0] for x in sorted_by_performance[:quantile]] # Best performance quantile
    self.long = [x[0] for x in sorted_by_performance[-quantile:]]
    return self.long + self.short
def OnData(self, data: Slice) -> None:
    offset = BMonthEnd()
    last_day:datetime = offset.rollforward(self.Time)
    trigger_day:datetime = last_day - BDay(self.offset_days)
    if self.Time == trigger_day:
        self.selection_flag = True
        
    if self.Portfolio.Invested:
        self.close_days += 1
        if self.close_days == 6:
            self.close_days = 0
            self.Liquidate()
        
    # Trade execution.
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()
class SymbolData():
def __init__(self, period:int):
    self._closes:RollingWindow = RollingWindow[float](period)
    
def update(self, close: float) -> None:
    self._closes.Add(close)
    
def is_ready(self) -> bool:
    return self._closes.IsReady
    
def performance(self) -> float:
    return (self._closes[0] / self._closes[self._closes.Count - 1]) - 1
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
