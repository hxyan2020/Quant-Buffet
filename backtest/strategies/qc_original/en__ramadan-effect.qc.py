# Original QuantConnect / library Python
# locale=en slug="ramadan-effect"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
from pandas.tseries.offsets import BDay

class RamadanEffect(XXX):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.symbols: List[Symbol] = [
        self.AddEquity(x, Resolution.Daily).Symbol for x in ['TUR', 'GULF', 'GAF', 'PAK', 'UAE', 'QAT', 'EGPT', 'EWM', 'EIDO', 'KSA']
    ]

    # Source: https://www.infoplease.com/calendars/holidays/islamic-holidays
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/calendar/ramadan_dates.csv')
    date_pairs_str: List[str] = csv_string_file.split('\r\n')
    self.date_ranges: List[List] = []

    for pair in date_pairs_str:
        split: List[str] = pair.split(';')
        
        self.date_ranges.append(
            pd.date_range(start=datetime.strptime(split[0], "%d.%m.%Y").date(), 
            end=datetime.strptime(split[1], "%d.%m.%Y").date())
        )

def OnData(self, slice: Slice) -> None:
    if any(str(self.Time.date()) in self.date_ranges[i] for i in range(len(self.date_ranges))):
        # open trades
        if not self.Portfolio.Invested:
            portfolio: List[PortfolioTarget] = [
                PortfolioTarget(symbol, 1. / len(self.symbols)) for symbol in self.symbols if symbol in slice and slice[symbol]
            ]
            self.SetHoldings(portfolio, True)
    else:
        # close trades
        if self.Portfolio.Invested:
            self.Liquidate()
