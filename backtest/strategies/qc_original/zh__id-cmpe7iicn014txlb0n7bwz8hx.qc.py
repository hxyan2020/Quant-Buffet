# Original QuantConnect / library Python
# locale=zh slug="隔夜动量策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from typing import List, Dict
from pandas.core.frame import DataFrame
#endregion
class OvernightMomentumStrategy(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100_000)
    
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']	
    self.period: int = 21 # need n of ovenight returns
    market: Symbol = self.AddEquity('SPY', Resolution.Minute).Symbol
    
    self.data: Dict[Symbol, SymbolData] = {} # storing objects of SymbolData under stocks symbols
    self.quantile: int = 10
    self.leverage: int = 20
    self.min_share_price: int = 5
    
    self.traded_quantity: Dict[Symbol, float] = {}
    
    self.fundamental_count: int = 100
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.BeforeMarketClose(market, 1), self.Selection)
    self.Schedule.On(self.DateRules.EveryDay(market), self.TimeRules.BeforeMarketClose(market, 20), self.MarketClose)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update overnight prices on daily basis
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        
        if symbol in self.data:
            # store current stock price
            self.data[symbol].current_price = stock.AdjustedPrice
            
            # get history prices
            history: DataFrame = self.History(symbol, 1, Resolution.Daily)
            # update overnight returns based on history prices
            self.UpdateOvernightReturns(symbol, history)
    
    # monthly rebalance
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.Market == 'usa'
        and x.MarketCap != 0
        and x.Price > self.min_share_price
        and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    # warm up overnight returns
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol in self.data and self.data[symbol].is_overnight_returns_ready():
            # get overnight returns from RollingWindow object and reverse it's list for simplier calculation of returns accumulation
            overnight_returns: List[float] = [x for x in self.data[symbol].overnight_returns]
            overnight_returns.reverse()
            # calculate accumulated returns
            accumulated_returns = np.prod([(1 + x) for x in overnight_returns]) - 1
            # update returns accumulated for last month
            self.data[symbol].returns_accumulated_last_month = accumulated_returns
            
            # go to next iteration, because there is no need for warm up overnight returns
            continue
        
        # initialize SymbolData object for current symbol
        self.data[symbol] = SymbolData(self.period)
        # get history of n + 1 days
        history: DataFrame = self.History(symbol, self.period + 1, Resolution.Daily)
        # update overnight returns based on history prices
        self.UpdateOvernightReturns(symbol, history)
            
    market_cap: Dict[Symbol, float] = {} # storing stocks market capitalization
    last_accumulated_returns: Dict[Symbol, float] = {} # storing stocks last accumuldated returns
    
    for stock in selected:
        symbol = stock.Symbol
        if not self.data[symbol].is_ready():
            continue
        # store stock's market capitalization
        market_cap[symbol] = stock.MarketCap
        # store stock's last accumulated returns
        last_accumulated_returns[symbol] = self.data[symbol].returns_accumulated_last_month
    
    # not enough data for decile selection     
    if len(last_accumulated_returns)  None:
    # send market on open and on close orders before market closes
    for symbol, q in self.traded_quantity.items():
        self.MarketOnCloseOrder(symbol, q)
        self.MarketOnOpenOrder(symbol, -q)
    
def UpdateOvernightReturns(self, symbol: Symbol, history: DataFrame) -> None:
    # calculate overnight returns only if history isn't empty
    if history.empty:
        return
    
    # get open and close prices
    opens = history.loc[symbol].open
    closes = history.loc[symbol].close
    
    # calculate overnight return for each day
    for (_, close_price), (_, open_price) in zip(closes.items(), opens.items()):
        # check if previous close price isn't None
        if self.data[symbol].prev_close_price:
            # calculate overnight return
            overnight_return = (open_price / self.data[symbol].prev_close_price) - 1
            # store overnight return
            self.data[symbol].update(overnight_return)
        
        # change value of prev close price for next calculation
        self.data[symbol].prev_close_price = close_price
    
def Selection(self) -> None:
    self.selection_flag = True
    self.traded_quantity.clear()
    
class SymbolData():
def __init__(self, period: int) -> None:
    self.overnight_returns: RollingWindow = RollingWindow[float](period)
    self.returns_accumulated_last_month: Union[None, float] = None
    self.prev_close_price: Union[None, float] = None
    self.current_price: float = 0.
    
def update(self, overnight_return: float) -> None:
    self.overnight_returns.Add(overnight_return)
    
def is_ready(self) -> bool:
    return self.returns_accumulated_last_month
    
def is_overnight_returns_ready(self) -> bool:
    return self.overnight_returns.IsReady
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
