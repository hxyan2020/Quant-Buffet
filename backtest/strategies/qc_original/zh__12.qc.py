# Original QuantConnect / library Python
# locale=zh slug="12个月季节性反转"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from typing import List, Dict, Tuple
#endregion
class TwelveMonthSeasonalReversals(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # monthly prices
    self.data: Dict[Symbol, SymbolData] = {} 
    self.period: int = 5 * 12 + 1
    self.weight: Dict[Symbol, float] = {}
    self.min_share_price: int = 5
    self.quantile: int = 3
    self.leverage: int = 5
    self.fundamental_count: int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    # update the rolling window every month
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    selected: List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and x.Market == 'usa' \
        and x.MarketCap > 0 and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # warmup price rolling windows
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol in self.data:
            continue
        
        self.data[symbol] = SymbolData(self.period)
        history: DataFrame = self.History(symbol, self.period*30, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes: Series = history.loc[symbol].close
        
        closes_len: int = len(closes.keys())
        # find monthly closes
        for index, time_close in enumerate(closes.items()):
            # index out of bounds check.
            if index + 1  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
class SymbolData():
def __init__(self, period: int) -> None:
    self._monthly_prices: RollingWindow = RollingWindow[float](period)
        
def update(self, price: float) -> None:
    self._monthly_prices.Add(price)
        
def is_ready(self) -> bool:
    return self._monthly_prices.IsReady
    
def monthly_returns(self) -> np.ndarray:
    monthly_closes: np.ndarray = np.array([x for x in self._monthly_prices])
    return (monthly_closes[:-1] / monthly_closes[1:] - 1)
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
