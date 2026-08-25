# Original QuantConnect / library Python
# locale=en slug="trendfollowing-effect-within-reits"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class TrendfollowingEffectREITs(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    data: Equity = self.AddEquity('VNQ', Resolution.Daily)
    data.SetLeverage(5)
    self.vnq: Symbol = data.Symbol
    
    data: Equity = self.AddEquity('SHY', Resolution.Daily)
    data.SetLeverage(5)
    self.shy: Symbol = data.Symbol
    
    period: int = 24 * 21
    self.SetWarmUp(period, Resolution.Daily)
    
    self.data: SimpleMovingAverage = self.SMA(self.vnq, period, Resolution.Daily)
    # Warmup SMA.
    history: DataFrame = self.History(self.Symbol(self.vnq), period, Resolution.Daily)
    if not history.empty:
        closes = history.loc[self.vnq].close
        for time, close in closes.items():
            self.data.Update(time, close)
    
    self.recent_month: int = -1

def OnData(self, slice: Slice) -> None:
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    
    # if self.vnq in data and self.shy in data:
    #     if data[self.vnq] and data[self.shy]:
            
    if self.Securities[self.vnq].Price > self.data.Current.Value:
        if self.Portfolio[self.shy].Invested:
            self.Liquidate(self.shy)
        self.SetHoldings(self.vnq, 1)
    else:
        if self.Portfolio[self.vnq].Invested:
            self.Liquidate(self.vnq)
        self.SetHoldings(self.shy, 1)
