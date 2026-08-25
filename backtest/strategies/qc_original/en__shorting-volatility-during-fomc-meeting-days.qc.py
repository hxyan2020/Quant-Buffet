# Original QuantConnect / library Python
# locale=en slug="shorting-volatility-during-fomc-meeting-days"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class ShortingVolatility(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2012, 1, 1)
    self.SetCash(100000)
    
    self.symbol = self.AddEquity("VIIX", Resolution.Minute).Symbol
    
    # fed days
    csv_string_file = self.Download('data.quantpedia.com/backtesting_data/economic/fed_days.csv')
    dates = csv_string_file.split('\r\n')
    self.dates = [datetime.strptime(x, "%Y-%m-%d") for x in dates]

def OnData(self, data) -> None:
    if self.symbol in data and data[self.symbol]:
        if self.Time.replace(minute=0, hour=0) in self.dates:
            if self.Time.hour == 9 and self.Time.minute == 35:
                if not self.Portfolio[self.symbol].IsShort:
                    self.SetHoldings(self.symbol, -1)
            
            elif self.Time.hour == 15 and self.Time.minute == 30:
                if self.Portfolio[self.symbol].IsShort:
                    self.Liquidate(self.symbol)
