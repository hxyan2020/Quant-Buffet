# Original QuantConnect / library Python
# locale=en slug="隔夜异常策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class OvernightAnomaly(QCAlgorithm):
def initialize(self):
    self.set_start_date(1998, 1, 2)
    self.set_cash(100_000)
    
    data: Equity = self.add_equity("SPY", Resolution.MINUTE)
    data.SetFeeModel(CustomFeeModel())
    self.symbol: Symbol = data.Symbol
    
    # NOTE: MarketOnClose orders must be placed with at least a 16 minute buffer before market close.
    self.schedule.on(self.date_rules.every_day(self.symbol), self.time_rules.before_market_close(self.symbol, 16), self.day_close)
def day_close(self) -> None:
    if not self.portfolio.invested:
        q: int = self.portfolio.total_portfolio_value // self.securities[self.symbol].price
        self.market_on_close_order(self.symbol, q)
        self.market_on_open_order(self.symbol, -q)
# Custom fee model (trading strategy is backtested without transaction costs to show a theoretical potential of overnight factor)
class CustomFeeModel(FeeModel):
def get_order_fee(self, parameters):
    fee = parameters.security.price * parameters.order.absolute_quantity * 0
    return OrderFee(CashAmount(fee, "USD"))
