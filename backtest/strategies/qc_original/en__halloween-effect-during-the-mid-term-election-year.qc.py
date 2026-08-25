# Original QuantConnect / library Python
# locale=en slug="halloween-effect-during-the-mid-term-election-year"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from pandas.tseries.offsets import BDay
from AlgorithmImports import *
class HalloweenEffectCombinedWithElectinCycle(QCAlgorithm):
def initialize(self) -> None:
    self.set_start_date(1999, 1, 1)
    self.set_cash(100_000)
    
    self.market: Symbol = self.add_equity("SPY", Resolution.DAILY).symbol
    self.cash: Symbol = self.add_equity("SHY", Resolution.DAILY).symbol
    
    self.current_year: int = -1
    self.count_years: int = 1 # At the start of this strategy it will increase this value by one.
def on_data(self, slice: Slice) -> None:
    if self.current_year != self.time.year:
        self.current_year = self.time.year
        self.count_years += 1
    
    # The investor buys these stocks at the beginning of December and holds them until the end of April.
    if self.count_years == 2 and self.time.month == 12 and not self.portfolio.invested:
        self.set_holdings(self.market, 0.5)
        self.set_holdings(self.cash, 0.5)
        self.count_years = 0
        
    # Holds them until the end of April.   
    if (self.time.date() + BDay(1)).month == 5 and self.portfolio.invested:
        self.liquidate()
