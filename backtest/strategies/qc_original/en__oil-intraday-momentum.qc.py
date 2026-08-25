# Original QuantConnect / library Python
# locale=en slug="oil-intraday-momentum"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from math import floor
#endregion
class OilIntradayMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(1000000)
    self.period = 3 * 21
    self.treshhold_value = 2
    self.future:Future = self.AddFuture(Futures.Energies.CrudeOilWTI, \
                        Resolution.Minute, \
                        dataNormalizationMode=DataNormalizationMode.BackwardsRatio, \
                        contractDepthOffset=0)
    self.symbol:Symbol = self.future.Symbol
    
    self.daily_ret = [] # daily returns
    self.open = 0   # latest open
    self.day_close_flag:bool = False
    self.day_open_flag:bool = False
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.EveryDay(self.market), self.TimeRules.BeforeMarketClose(self.market, 1), self.DayClose)
    self.Schedule.On(self.DateRules.EveryDay(self.market), self.TimeRules.AfterMarketOpen(self.market, 1), self.DayOpen)
    
def OnData(self, data: Slice) -> None:
    # close
    if self.day_close_flag:
        self.day_close_flag = False
        self.Liquidate()

        if self.symbol in data and data[self.symbol]:
            close:float = data[self.symbol].Close
            if close != 0 and self.open != 0 and close != self.open:
                todays_ret:float = close / self.open - 1
                self.daily_ret.append(todays_ret)
            
                if len(self.daily_ret)  high_threshhold:
                    if not self.Portfolio.Invested:
                        self.MarketOrder(self.future.Mapped, 1)
        
        self.open = 0
    
    # open
    if self.day_open_flag:
        self.day_open_flag = False
        if self.symbol in data and data[self.symbol]:
            self.open = data[self.symbol].Open
def DayClose(self) -> None:
    self.day_close_flag = True

def DayOpen(self) -> None:
    self.day_open_flag = True
