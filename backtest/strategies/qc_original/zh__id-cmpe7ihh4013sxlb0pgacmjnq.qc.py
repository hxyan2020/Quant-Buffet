# Original QuantConnect / library Python
# locale=zh slug="隔夜股票交易"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from typing import Dict, List
class OvernightStockTrading(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.leverage:int = 10
    self.quantile:int = 10
    self.period:int = 12 * 21
    self.min_share_price:int = 5
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Minute).Symbol
    
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.fundamental_count:int = 100
    
    self.selected:List[Symbol] = [] # symbols of selected stocks from fundamentalSelectionFunction
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    self.data:Dict[Symbol, SymbolData] = {}
    
    self.months_counter:int = 1
    self.selection_flag:bool = True
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.EveryDay(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol, 20), self.MarketClose)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # updating overnight data and stock price every day
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        if symbol in self.data:
            # update stock price
            self.data[symbol].price = stock.AdjustedPrice
            
            # get history data
            history:DataFrame = self.History(symbol, 1, Resolution.Daily)
            # update overnight return and change prev_close_price
            self.UpdateOvernightReturns(history, symbol)
            
    # one year rebalance
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    # sort stocks by dollar volume
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and x.Market == 'usa'
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            continue
        
        # create object of SymbolData class for current stock
        self.data[symbol] = SymbolData(self.period)
        
        # get history data
        history:DataFrame = self.History(symbol, self.period + 1, Resolution.Daily)
        # update overnight return and change prev_close_price
        self.UpdateOvernightReturns(history, symbol)
        
    # change self.selected list on rebalance
    self.selected = [x.Symbol for x in selected]
        
    return self.selected
        
def MarketClose(self) -> None:
    total_performance:Dict[Symbol, float] = {} # storing total overnight returns performance for self.period overnight returns
    
    # calculate total overnight performances
    for symbol in self.selected:
        if not self.data[symbol].is_overnight_returns_ready():
            continue
        
        # calculate and store total overnight performance
        total_performance[symbol] = self.data[symbol].total_overnight_performance()
        
    if len(total_performance) >= self.quantile:
        # quantile selection
        quantile:int = int(len(total_performance) / self.quantile)    
        sorted_by_total_perf:List[Symbol] = [x[0] for x in sorted(total_performance.items(), key=lambda item: item[1])]
        
        # long top quantile stocks and short bottom quantile stocks
        self.long = sorted_by_total_perf[-quantile:]
        self.short = sorted_by_total_perf[:quantile]
        
        long_length:int = len(self.long)
        short_length:int = len(self.short)
        
        # trade execution
        for symbol in self.long:
            current_price = self.data[symbol].price
            if current_price != 0 and self.Securities[symbol].Price != 0 and self.Securities[symbol].IsTradable: 
                quantity = np.floor((self.Portfolio.TotalPortfolioValue / long_length) / current_price)
                self.MarketOnCloseOrder(symbol, quantity)
                self.MarketOnOpenOrder(symbol, -quantity)
            
        for symbol in self.short:
            current_price = self.data[symbol].price
            if current_price != 0 and self.Securities[symbol].Price != 0 and self.Securities[symbol].IsTradable: 
                quantity = np.floor((self.Portfolio.TotalPortfolioValue / short_length) / current_price)
                self.MarketOnCloseOrder(symbol, -quantity)
                self.MarketOnOpenOrder(symbol, quantity)
def UpdateOvernightReturns(self, history, symbol: Symbol) -> None:
    ''' update overnight returns for specific stock according to history data '''
    
    # check if history isn't empty and history dataframe has required attributes
    if not history.empty and hasattr(history, 'close') and hasattr(history, 'open'):
        # get open and close prices from dataframe
        opens:Series = history['open']
        closes:Series = history['close']
        
        # update overnight return 
        for (_, open_price), (_, close_price) in zip(opens.items(), closes.items()):
            # update overnight return and change prev_close_price
            self.data[symbol].update(open_price, close_price)
    
def Selection(self) -> None:
    if self.months_counter % 12 == 0:
        self.selection_flag = True
    self.months_counter += 1

class SymbolData():
def __init__(self, period: int):
    self.overnight_returns:RollingWindow = RollingWindow[float](period)
    self.prev_close_price:Union[None, float] = None
    self.price:int = 0
    
def update(self, open_price: float, close_price: float) -> None:
    # update overnight returns only if prev_close_price isn't None
    if self.prev_close_price:
        overnight_return = open_price / self.prev_close_price - 1
        self.overnight_returns.Add(overnight_return)
    # change previous close price to current close price
    self.prev_close_price = close_price
    
def total_overnight_performance(self) -> float:
    return sum(list(self.overnight_returns))
    
def is_overnight_returns_ready(self) -> bool:
    return self.overnight_returns.IsReady
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
