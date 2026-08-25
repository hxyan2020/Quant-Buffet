# Original QuantConnect / library Python
# locale=en slug="price-overreactions-in-the-forex"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class PriceOverreactionsintheForex(QCAlgorithm):
def initialize(self):
    self.set_start_date(2009, 1, 1)
    self.set_cash(100000)
    self.period: int = 50
    
    self.symbol: Symbol = self.add_forex('AUDUSD', Resolution.MINUTE, Market.OANDA).symbol
    self.securities[self.symbol].set_fee_model(CustomFeeModel())
    
    self.daily_returns: RollingWindow = RollingWindow[float](self.period)
    self.open_price: float | None = None
    
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.schedule.on(self.date_rules.every_day(self.symbol), self.time_rules.at(17, 0), self.at17)
        
def at17(self):
    history : DataFrame = self.history(self.symbol, self.period, Resolution.DAILY)
    if len(history) == self.period:
        if 'close' in history:
            closes: np.ndarray = np.array(history['close'].values)
            daily_returns: np.ndarray = closes[1:] / closes[:-1] - 1
            avg_ret: float = np.average(daily_returns)
            std: float = np.std(daily_returns)
            
            price: float = self.securities[self.symbol].close
            ret: float = price / closes[-1] - 1
            
            if ret > avg_ret + 2*std: 
                self.set_holdings(self.symbol, 1)
                holdings_q: float = self.portfolio[self.symbol].quantity
                self.market_on_close_order(self.symbol, -holdings_q)
# Custom fee model
class CustomFeeModel(FeeModel):
def get_order_fee(self, parameters):
    fee = parameters.security.price * parameters.order.absolute_quantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
