# Original QuantConnect / library Python
# locale=en slug="daily-box-office-earnings-and-aggregate-stock-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class DailyBoxOfficeEarningsandAggregateStockReturns(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    # Daily box data indexed by date.
    self.daily_box_data = {}
    
    # Import daily box data.
    # Data source: https://www.boxofficemojo.com/daily/2020/?view=year
    daily_box_string_data = self.Download('data.quantpedia.com/backtesting_data/economic/daily_box_earnings.csv')
    lines = daily_box_string_data.split('\r\n')
    for line in lines[1:]:
        split_line = line.split(';')
        date = datetime.strptime(split_line[0], "%Y-%m-%d").date()
        
        if split_line[5] == '-':
            weekly_change = None
        else:
            weekly_change = float(split_line[5])
        
        self.daily_box_data[date] = weekly_change
    
def OnData(self, data):
    date_to_lookup = (self.Time - timedelta(days = 1)).date()
    
    if date_to_lookup in self.daily_box_data:
        weekly_change = self.daily_box_data[date_to_lookup]
        if weekly_change:
            if weekly_change > 15:
                self.SetHoldings(self.symbol, 1)
            else:
                self.SetHoldings(self.symbol, -1)
    else:
        self.Liquidate()
