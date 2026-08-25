# Original QuantConnect / library Python
# locale=en slug="combining-seasonality-and-momentum-in-us-equity-sectors"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class SeasonalityandMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2007, 1, 1)
    self.SetCash(100000)
    self.cyclical = ["VAW", "XLI", "XLY"]
    self.defensive = ["XLP", "XLV", "VGT", "XLU"]
    self.neutral = ["XLK", "XLF", "XLE", "VNQ"]
    self.symbols = self.cyclical + self.defensive + self.neutral
    self.period = 21
    self.SetWarmUp(self.period)
    
    self.short_momentum = {}
    self.long_momentum = {}
    
    for symbol in self.symbols:
        data = self.AddEquity(symbol, Resolution.Daily)
        data.SetLeverage(10)
        data.SetFeeModel(CustomFeeModel())
        
        self.short_momentum[symbol] = self.ROC(symbol, self.period, Resolution.Daily)
        self.long_momentum[symbol] = self.ROC(symbol, 12*self.period, Resolution.Daily)
        
    self.recent_month = -1
def OnData(self, data):
    if self.IsWarmingUp: return
    
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    
    returns_12M = { x : self.long_momentum[x].Current.Value for x in self.symbols if self.long_momentum[x].IsReady and x in data and data[x] }
    returns_1M = { x : self.short_momentum[x].Current.Value for x in self.symbols if self.short_momentum[x].IsReady and x in data and data[x] }
    
    if len(returns_12M) = 11 :
        for symbol in self.cyclical:
            score[symbol] += 4
    elif self.Time.month >= 5 and self.Time.month  9]
    short = [x[0] for x in score.items() if x[1]
