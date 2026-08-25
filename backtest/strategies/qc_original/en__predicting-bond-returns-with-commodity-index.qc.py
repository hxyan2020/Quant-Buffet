# Original QuantConnect / library Python
# locale=en slug="predicting-bond-returns-with-commodity-index"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
#endregion
class PredictingBondReturnswithCommodityIndex(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.period = (10 * 12) * 21 + 21
    self.SetWarmUp(self.period, Resolution.Daily)
    
    data = self.AddData(QuantpediaIndices, 'SPGSCITR', Resolution.Daily)
    data.SetFeeModel(CustomFeeModel())
    self.symbol = data.Symbol
    
    # Daily price data.
    self.data = RollingWindow[float](self.period)
    self.max_missing_days:int = 5
    self.recent_month:int = -1
    
def OnData(self, data):
    # Store daily data.
    if self.symbol in data and data[self.symbol]:
        price = data[self.symbol].Value
        self.data.Add(price)
    
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    self.Liquidate()
    
    # Z score calc.
    z_score = 0
    if self.data.IsReady:
        if self.Securities[self.symbol].GetLastData() and (self.Time.date() - self.Securities[self.symbol].GetLastData().Time.date()).days  1: z_score = 1
                elif z_score
