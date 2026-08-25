# Original QuantConnect / library Python
# locale=zh slug="过滤后的短期反转"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
class FilteredShortTermReversal(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.symbol: Symbol = self.AddEquity("SPY", Resolution.Minute).Symbol
    # Setup consolidator.
    self.spy_onsolidator = TradeBarConsolidator(timedelta(days=1))
    self.spy_onsolidator.DataConsolidated += self.DailyData
    self.SubscriptionManager.AddConsolidator(self.symbol, self.spy_onsolidator)
    # SPY closes.
    self.period: int = 61
    self.data: RollingWindow = RollingWindow[float](self.period)
    # Warmup.
    history: DataFrame = self.History(self.symbol, self.period, Resolution.Daily)
    if not history.empty:
        closes = history.loc[self.symbol].close
        for time, close in closes.items():
            self.data.Add(close)
    
    self.run_days: RollingWindow = RollingWindow[float](2)

# On daily data.
def DailyData(self, sender, consolidated) -> None:
    self.data.Add(consolidated.Close)
    
    if self.data.IsReady:
        closes: np.ndarray = np.array([x for x in self.data])
        return_data: np.ndarray = closes[:-1] / closes[1:] - 1
        ret: float = return_data[0]
        
        if ret >= 0:
            self.run_days.Add(1)
        else:
            self.run_days.Add(0)
        
        if len(return_data) == self.period - 1:
            if self.run_days.IsReady:
                mean: float = np.mean(return_data)
                ret_std: float = np.std(return_data)
                
                run_days: List[float] = [x for x in self.run_days]
                
                # Positive run
                if sum(run_days) == 2:
                    if ret >= mean + ret_std:
                        if self.Portfolio[self.symbol].IsLong:
                            self.Liquidate()
                        self.SetHoldings(self.symbol, -1)
                    else:
                        self.Liquidate()
                # Negative run
                elif sum(run_days) == 0: 
                    if ret
