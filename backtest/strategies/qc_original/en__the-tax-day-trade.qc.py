# Original QuantConnect / library Python
# locale=en slug="the-tax-day-trade"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class TaxDayAnomaly(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)  
    self.SetCash(100000) 
    
    self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.startPrice = None
    
# Tax day is on 15.4 each year.
def OnData(self, data):
    if self.Portfolio[self.symbol].Invested:
        self.Liquidate(self.symbol)
        
    # Beacause of unknown reasons market was closed on 14.4. and 16.4. is Sunday, so we invest on 13.4. in years 2001, 2006 and 2017.
    if self.Time.year in [2001, 2006, 2017] and self.Time.month == 4 and self.Time.day == 13:
        self.SetHoldings(self.symbol, 1)
    
    # When 16.4. is on the weekend, we invest on friday.
    if (self.Time.day == 14 or self.Time.day == 15) and self.Time.month == 4 and self.Time.weekday() == 5:
        self.SetHoldings(self.symbol, 1)
    
    if self.Time.day == 16 and self.Time.month == 4:
        self.SetHoldings(self.symbol, 1)
