# Original QuantConnect / library Python
# locale=en slug="abnormal-volume-effect-in-the-stock-market"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from typing import List, Dict
from pandas.core.frame import DataFrame
class AbnormalVolumeEffectStockMarket(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.data:Dict[Symbol, SymbolData] = {}
    self.period:int = 66
    self.leverage:int = 5
    self.std_treshold:float = 2.33
    self.performance_treshold:float = 0.01
    
    self.long:List[Symbol] = []
    
    self.selection_flag:bool = False
    self.last_selection:List[Fundamental] = []
    
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.fundamental_count:int = 1000
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            # Store daily price and volume.
            self.data[symbol].update(stock.AdjustedPrice, stock.Volume)
    
    # return already selected universe during the month
    if self.selection_flag:
        self.selection_flag = False
        selected:List[Fundamental] = [
            x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0
        ]
        if len(selected) > self.fundamental_count:
            selected = sorted(selected, key = self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]
        self.last_selection = selected
        # Warmup price rolling windows.
        for stock in self.last_selection:
            symbol:Symbol = stock.Symbol
            if symbol in self.data:
                continue
            self.data[symbol] = SymbolData(symbol, self.period, -1)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            if 'close' in history and 'volume' in history:
                closes:Series = history.loc[symbol]['close']
                volumes:Series = history.loc[symbol]['volume']
                for (time1, close), (time2, volume) in zip(closes.items(), volumes.items()):
                    self.data[symbol].update(close, volume)
    # fundamental returned ready data
    for stock in self.last_selection:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            continue
        if not self.data[symbol].is_ready():
            continue
        volumes:List[float] = [x for x in self.data[symbol]._volume]
        volume_mean:float = np.mean(volumes)
        volume_std:float = np.std(volumes)
        volume:float = volumes[0] # Takes todays volume
           
        closes:List[float] = [x for x in self.data[symbol]._price][:2] # First two are newest
        todays_return:float = (closes[0] - closes[1]) / closes[1]
         
        if volume > volume_mean + (self.std_treshold * volume_std):
            # selects only firms with no abnormal volume over the preceding 30 trading days
            if (self.data[symbol]._abnormal_date == -1) or (self.data[symbol]._abnormal_date = self.performance_treshold:
                    self.long.append(symbol)
            self.data[symbol]._abnormal_date = self.Time
                
    return self.long

def OnData(self, data: Slice) -> None:
    # Trade execution
    targets:List[PortfolioTarget] = [PortfolioTarget(symbol, 1. / len(self.long)) for symbol in self.long if symbol in data and data[symbol]]
    self.SetHoldings(targets, True)
    self.long.clear()

def Selection(self) -> None:
    self.selection_flag = True
    
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
    
class SymbolData():
def __init__(self, symbol:Symbol, period:int, abnormal_date:datetime):
    self._symbol:Symbol = symbol
    self._price:RollingWindow = RollingWindow[float](period)
    self._volume:RollingWindow = RollingWindow[float](period)
    self._abnormal_date:datetime = abnormal_date

def update(self, price:float, volume:float):
    self._price.Add(price)
    self._volume.Add(volume)

def is_ready(self) -> bool:
    return self._price.IsReady and self._volume.IsReady
