# Original QuantConnect / library Python
# locale=en slug="adaptive-moving-averages-used-for-market-timing"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
class AdaptiveMovingAveragesMarketTiming(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    data = self.AddEquity('SPY', Resolution.Daily)
    data.SetLeverage(5)
    self.symbol = data.Symbol
    self.period = 4 * 12 * 21
    self.SetWarmUp(self.period, Resolution.Daily)
    self.data = RollingWindow[float](self.period)
    
    self.ma = {}
    self.ma_signal = {}
    
    sma_periods = [x for x in range(1, 101, 4)]
    lma_periods = [x for x in range(5, 991, 20)]
    
    ma_combinations = [[i, j] for i in sma_periods for j in lma_periods if i lma_value else -1)
            
            # 4 years of SPY data is ready.
            if self.data.IsReady:
                values = np.array([x for x in self.data])
                daily_changes = values[:-1] / values[1:] - 1
            
                # Find optimal sma_lma pair.
                if self.ma_signal[sma_lma].IsReady:
                    # Multiply both vectors to get daily performance for sma_lma pair.
                    # Ignore last value from ma_signal since it's today's value. It will be used to trade decision for next day.
                    ma_signal_vector = [x for x in self.ma_signal[sma_lma]][1:]
                    return_vector = ma_signal_vector * daily_changes
                    
                    # Store avg daily performance for sma_lma pair.
                    avg_return[sma_lma] = np.average([x for x in return_vector])
            
        else:
            # MA is not ready yet.
            self.ma_signal[sma_lma].Add(0)
    if self.IsWarmingUp: return
    if len(avg_return) == 0: return
    
    # Optimalization
    optimal_sma_lma = max(avg_return, key=avg_return.get)
    
    # Trading
    last_signal = self.ma_signal[optimal_sma_lma][0]
    if last_signal == 1:
        self.SetHoldings(self.symbol, 1)
    elif last_signal == -1:
        self.SetHoldings(self.symbol, -1)
