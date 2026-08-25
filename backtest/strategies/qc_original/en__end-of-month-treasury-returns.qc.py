# Original QuantConnect / library Python
# locale=en slug="end-of-month-treasury-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.tseries.offsets import BDay
from pandas.tseries.offsets import BMonthEnd
class EOMTreasuryReturns(QCAlgorithm):
def initialize(self) -> None:
    self.set_start_date(2000, 1, 1)
    self.set_cash(100_000)
    self.set_brokerage_model(BrokerageName.INTERACTIVE_BROKERS_BROKERAGE, AccountType.MARGIN)
    self.settings.minimum_order_margin_portfolio_percentage = 0
    self.settings.daily_precise_end_time = True
    
    self._traded_symbol: Symbol = self.add_equity('TLT', Resolution.MINUTE).symbol
    minute_offset: int = 1
    self._eom_trigger_day_offset: int = 6
    self._month_close_flag: bool = False
    self._day_close_flag: bool = False
    # schedule functions
    self.schedule.on(
        self.date_rules.every_day(self._traded_symbol), self.time_rules.before_market_close(self._traded_symbol, minute_offset), self._before_eod
    )
    self.schedule.on(
        self.date_rules.month_end(self._traded_symbol), self.time_rules.before_market_close(self._traded_symbol, minute_offset), self._month_close
    )

def on_data(self, slice: Slice) -> None:
    # close position
    if self._month_close_flag:
        self._month_close_flag = False
        if self.portfolio[self._traded_symbol].invested:
            self.liquidate(self._traded_symbol)
        
    if self._day_close_flag:
        self._day_close_flag = False
        if slice.contains_key(self._traded_symbol) and slice[self._traded_symbol]:
            offset = BMonthEnd()
            last_day: datetime = offset.rollforward(self.time)
            while not self.securities[self._traded_symbol].exchange.hours.is_date_open(last_day):
                last_day = last_day - timedelta(days=1)
            trigger_day: datetime = last_day - BDay(self._eom_trigger_day_offset)
            if self.time == trigger_day:
                self.set_holdings(self._traded_symbol, 1.)
    
def _before_eod(self) -> None:
    self._day_close_flag = True

def _month_close(self) -> None:
    self._month_close_flag = True
