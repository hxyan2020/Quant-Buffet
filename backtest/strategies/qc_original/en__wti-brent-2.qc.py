# Original QuantConnect / library Python
# locale=en slug="wti-brent-价差策略-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class WTIBRENTSpread(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols = [
        "ICE_WT1",  # WTI Crude Futures, Continuous Contract
        "ICE_B1"    # Brent Crude Oil Futures, Continuous Contract
    ]

    self.spread = RollingWindow[float](20)
    
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetLeverage(5)
        data.SetFeeModel(CustomFeeModel())
    
def OnData(self, data):
    symbol1 = self.Symbol(self.symbols[0])
    symbol2 = self.Symbol(self.symbols[1])
    
    if symbol1 in data.Keys and symbol2 in data.Keys and data[symbol1] and data[symbol2]:
        price1 = data[symbol1].Price
        price2 = data[symbol2].Price
        
        if price1 != 0 and price2 != 0:
            spread = price1 - price2
            self.spread.Add(spread)
    
    # MA calculation.
    if self.spread.IsReady:
        if (self.Time.date() - self.Securities[symbol1].GetLastData().Time.date()).days  spread_ma20:
                self.SetHoldings(symbol1, -1)
                self.SetHoldings(symbol2, 1)
            elif current_spread
