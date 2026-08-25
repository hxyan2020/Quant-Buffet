# Original QuantConnect / library Python
# locale=zh slug="结合动量与反趋势策略在美国股票指数上的应用"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class MomentumandCountertrend(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.SetWarmUp(150)
    
    self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.qqq = self.AddEquity("QQQ", Resolution.Daily).Symbol
    
    self.qqq_short_ema = self.EMA("QQQ", 50, Resolution.Daily)
    self.qqq_long_ema = self.EMA("QQQ", 150, Resolution.Daily)
    
    self.low_history_period = 20
    self.spy_low_history = RollingWindow[float](self.low_history_period)
    
def OnData(self, data):
    if self.IsWarmingUp: return

    # QQQ trend-following strategy
    if self.qqq_short_ema.IsReady and self.qqq_long_ema.IsReady:
        if self.qqq in data.Bars:
            qqq_close = data.Bars[self.qqq].Close
            
            short_ema = self.qqq_short_ema.Current.Value
            long_ema = self.qqq_long_ema.Current.Value

            if (short_ema > long_ema) and (qqq_close > short_ema) and (qqq_close > long_ema):
                self.SetHoldings(self.qqq, 1/2)
            elif (short_ema
