# Original QuantConnect / library Python
# locale=en slug="timing-the-small-cap-effect-ver-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class TimingtheSmallCap(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.period:int = 21
    self.SetWarmUp(self.period, Resolution.Daily)
    self.symbol:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.data:RollingWindow = RollingWindow[float](self.period)
    
    self.iwm:Symbol = self.AddEquity("IWM", Resolution.Daily).Symbol
    
    self.recent_month:int = -1
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
def OnData(self, data: Slice) -> None:
    if self.symbol in data and data[self.symbol]:
        price:float = data[self.symbol].Value
        self.data.Add(price)
    
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    if self.data.IsReady:
        if self.data[0] / self.data[self.period - 1] - 1 > 0:
            self.SetHoldings(self.iwm, 1)
        else:
            self.Liquidate(self.iwm)
