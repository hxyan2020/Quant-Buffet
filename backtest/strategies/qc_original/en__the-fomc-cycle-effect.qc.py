# Original QuantConnect / library Python
# locale=en slug="the-fomc-cycle-effect"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class TheFOMCCycleEffect(QCAlgorithm):
def initialize(self) -> None:
    self.set_start_date(2000, 1, 1)
    self.set_cash(100_000)
    
    self.symbol: Symbol = self.add_equity("SPY", Resolution.MINUTE).symbol
    csv_string_file: str = self.download('data.quantpedia.com/backtesting_data/economic/fed_days.csv')
    dates: List[str] = csv_string_file.split('\r\n')
    dates_before_fed: List[datetime.date] = [(datetime.strptime(x, "%Y-%m-%d") - BDay(1)).date() for x in dates]
    
    self.trade_flag: bool = False
    self.days_to_switch_positions: bool = 5
    
    self.schedule.on(self.date_rules.on(dates_before_fed), self.time_rules.after_market_open(self.symbol, 1), self.day_before_FED)
    self.schedule.on(self.date_rules.every_day(self.symbol), self.time_rules.after_market_open(self.symbol, 1), self.rebalance)

def day_before_FED(self) -> None:
    self.set_holdings(self.symbol, 1)
    self.days_to_switch_positions = 5
    self.trade_flag = True
def rebalance(self) -> None:
    if self.trade_flag:
        if self.days_to_switch_positions == 0:
            if self.portfolio[self.symbol].is_long:
                self.liquidate(self.symbol)
            else:
                self.set_holdings(self.symbol, 1)
            
            self.days_to_switch_positions = 5
        self.days_to_switch_positions -= 1
