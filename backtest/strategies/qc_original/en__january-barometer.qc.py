# Original QuantConnect / library Python
# locale=en slug="january-barometer"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class JanuaryBarometer(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000) 
    
    leverage:int = 5
    data:Equity = self.AddEquity("SPY", Resolution.Daily)
    data.SetLeverage(leverage)
    self.market:Symbol = data.Symbol
    
    data:Equity = self.AddEquity("SHY", Resolution.Daily)
    data.SetLeverage(leverage)
    self.bond:Symbol = data.Symbol
    
    self.max_missing_days:int = 5

    self.start_price:float|None = None
    self.recent_month:int = -1
    
def OnData(self, data):
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    
    if self.Securities[self.market].GetLastData() and self.Securities[self.bond].GetLastData():
        if (self.Time.date() - self.Securities[self.market].GetLastData().Time.date()).days  0:
                    self.SetHoldings(self.market, 1)
                else:
                    self.start_price = None
                    self.Liquidate(self.market)
                    self.SetHoldings(self.bond, 1)
        else:
            self.Liquidate()
    else:
        self.Liquidate()
