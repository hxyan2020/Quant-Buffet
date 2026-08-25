# Original QuantConnect / library Python
# locale=en slug="scheduled-economic-announcements-effect-in-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.tseries.offsets import BDay
#endregion
class ScheduledAnnouncementsAnomaly(QCAlgorithm):
def initialize(self):
    self.set_start_date(2000, 1, 1)
    self.set_cash(100_000)
    
    self.symbol: Symbol = self.add_equity("SPY", Resolution.MINUTE).symbol
    csv_string_file: str = self.download('data.quantpedia.com/backtesting_data/economic/economic_announcements.csv')
    dates: List[str] = csv_string_file.split('\r\n')
    self.announcement_dates_t_minus_one: List[datetime.date] = [(datetime.strptime(x, "%Y-%m-%d") - BDay(1)).date() for x in dates]
def on_data(self, data: Slice) -> None:
    if self.time.hour == 15 and self.time.minute == 44:
        if self.time.date() in self.announcement_dates_t_minus_one:
            if not self.portfolio[self.symbol].is_long:
                self.market_on_close_order(self.symbol, self.calculate_order_quantity(self.symbol, 1.))
        else:
            if self.portfolio[self.symbol].is_long:
                self.market_on_close_order(self.symbol, -self.portfolio[self.symbol].quantity)
