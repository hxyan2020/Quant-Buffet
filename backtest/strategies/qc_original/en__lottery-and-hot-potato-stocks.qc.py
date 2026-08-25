# Original QuantConnect / library Python
# locale=en slug="lottery-and-hot-potato-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from typing import List, Dict, Tuple
from pandas.core.frame import DataFrame
from pandas.core.series import Series
from dataclasses import dataclass
#endregion
class LotteryAndHotPotatoStocks(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']    
    market: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    self.data: Dict[Symbol, SymbolData] = {}
    self.weight: Dict[Symbol, float] = {}
    
    self.period: int = 21
    self.quantile: int = 10
    self.section: int = 3
    self.leverage: int = 5
    self.min_share_price: int = 5
    
    self.fundamental_count = 3_000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.selection_flag = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        if symbol in self.data:
            # Store daily price.
            self.data[symbol].update(stock.AdjustedPrice)
    
    # Selection once a month.
    if not self.selection_flag:
        return Universe.Unchanged
    
    MIN_MAX: List[Tuple[Symbol, float, float]] = []
    
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.Price > self.min_share_price 
        and x.Market == 'usa' 
        and x.MarketCap != 0 
        and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    # Warmup price rolling windows.
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes: Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
            
        if not self.data[symbol].is_ready():
            continue
        
        highest_loss, highest_gain = self.data[symbol].highest_loss_and_gain()
        MIN_MAX.append(MinMax(stock, highest_loss, highest_gain))
    
    if len(MIN_MAX)  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    
class SymbolData():
def __init__(self, period: int) -> None:
    self.Closes: RollingWindow = RollingWindow[float](period)
    
def update(self, close: float) -> None:
    self.Closes.Add(close)
    
def is_ready(self) -> bool:
    return self.Closes.IsReady
    
def highest_loss_and_gain(self) -> float:
    closes = np.array([x for x in self.Closes])
    returns = (closes[:-1] - closes[1:]) / closes[1:]
    
    return np.min(returns), np.max(returns)
@dataclass   
class MinMax():
symbol: Symbol
MIN: float 
MAX: float 
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
