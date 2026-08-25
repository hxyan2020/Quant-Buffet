# Original QuantConnect / library Python
# locale=zh slug="股市中的选前漂移"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from pandas.tseries.offsets import BDay
from AlgorithmImports import *
from dateutil.relativedelta import relativedelta, MO
class PreElectionDriftStockMarket(QCAlgorithm):
def initialize(self) -> None:
    self.set_start_date(2000, 1, 1)
    self.set_cash(100_000)
    
    self.symbol: Symbol = self.add_equity("SPY", Resolution.MINUTE).symbol
def on_data(self, data: Slice) -> None:
    if self.time.year % 2 == 0:
        election_day: datetime.date = ((date(self.time.year, 11, 1) + relativedelta(weekday=MO(1))) + BDay(1)).date()
        
        # This condition make sure, that we invest into market six business days before election day
        # and position will be open right after hurricane Sandy, when market is open.
        if self.time.date() >= (election_day - BDay(6)).date() and self.time.date()
