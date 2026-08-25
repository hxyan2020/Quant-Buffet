# Original QuantConnect / library Python
# locale=zh slug="原油的开盘区间突破策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
class OpeningRangeBreakoutCrudeOil(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.period:int = 21
    self.treshhold_value:int = 2
    self.future:Future = self.AddFuture(Futures.Energies.CrudeOilWTI, \
                        Resolution.Minute, \
                        dataNormalizationMode=DataNormalizationMode.BackwardsRatio, \
                        contractDepthOffset=0)
    self.symbol:Symbol = self.future.Symbol
    self.daily_ret:RollingWindow = RollingWindow[float](self.period)
    
    self.recent_open:float = 0
    
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
            if close != 0 and self.recent_open != 0 and close != self.recent_open:
                todays_ret:float = close / self.recent_open - 1
                self.daily_ret.Add(todays_ret)
                if self.daily_ret.IsReady:
                    daily_returns:List[float] = list(self.daily_ret)
                    mean:float = np.mean(daily_returns)
                    std:float = np.std(daily_returns)
            
                    high_threshhold:float = mean + self.treshhold_value * std
                    low_threshhold:float = mean - self.treshhold_value * std
                    
                    if todays_ret > high_threshhold:
                        if not self.Portfolio.Invested:
                            self.MarketOrder(self.future.Mapped, 1)
                    elif todays_ret  None:
    self.day_close_flag = True

def DayOpen(self) -> None:
    self.day_open_flag = True
