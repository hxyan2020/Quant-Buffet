# Original QuantConnect / library Python
# locale=en slug="intraday-momentum-in-crude-oil-etf"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class IntradayMomentumCrudeOil(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.last_day_close:float = 0
    self.symbol:Symbol = self.AddEquity('USO', Resolution.Minute).Symbol
    self.ret:float|None = None
    
def OnData(self, data:Slice) -> None:
    if self.symbol in data and data[self.symbol]:
        # day close
        if self.Time.hour == 16 and self.Time.minute == 0:
            self.last_day_close = data[self.symbol].Value
        
        # rebalance
        elif self.Time.hour == 15 and self.Time.minute == 30:
            q:float = self.CalculateOrderQuantity(self.symbol, 1)
            
            if self.ret:
                if self.ret > 0:
                    self.MarketOrder(self.symbol, q)
                    self.MarketOnCloseOrder(self.symbol, -q)
                else:
                    self.MarketOrder(self.symbol, -q)
                    self.MarketOnCloseOrder(self.symbol, q)
            
            self.ret = None
        
        # day open - calculation
        elif self.Time.hour == 10 and self.Time.minute == 0:
            if self.last_day_close == 0: return
            
            price:float = data[self.symbol].Value
            self.ret = price / self.last_day_close - 1
            self.last_day_close = 0
