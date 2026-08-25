# Original QuantConnect / library Python
# locale=en slug="opening-range-breakout-orb-strategy-in-qqq"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# endregion

class OpeningRangeBreakoutORBStrategyinQQQ(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(25000)

    self.market:Symbol = self.AddEquity("QQQ", Resolution.Minute).Symbol
    self.Consolidate(self.market, timedelta(minutes=5), self.FiveMinuteBarHandler)

    self.profit_target_multiplier:float = 10.
    self.max_leverage:float = 4.
    self.risk:float = 0.01 # % of account size 
    self.sl_price:Union[float, None] = None
    self.tp_price:Union[float, None] = None

    MarketOnCloseOrder.SubmissionTimeBuffer = timedelta(minutes=1)
    self.Schedule.On(self.DateRules.EveryDay(self.market),
             self.TimeRules.BeforeMarketClose(self.market, 1),
             self.BeforeDayClose)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetLeverage(self.max_leverage * 2)
        security.SetFeeModel(CustomFeeModel())

def BeforeDayClose(self) -> None:
    self.cancel_open_orders()
    self.sl_price = None
    self.tp_price = None
    
    self.MarketOnCloseOrder(self.market, -self.Portfolio[self.market].Quantity, tag='MOC')

def FiveMinuteBarHandler(self, consolidated):
    if consolidated.EndTime.hour == 9 and consolidated.EndTime.minute == 35:
        first_bar_open:float = consolidated.Open
        first_bar_close:float = consolidated.Close
        
        # long
        if first_bar_close > first_bar_open: # bullish candle
            R:float = first_bar_close - consolidated.Low
            quantity:int = int(min([(self.Portfolio.TotalPortfolioValue * self.risk) / R, (self.max_leverage * self.Portfolio.TotalPortfolioValue) / first_bar_close]))
            if quantity >= 1:
                self.sl_price = consolidated.Low
                self.tp_price = first_bar_close + (R * self.profit_target_multiplier)
                self.MarketOrder(self.market, quantity, tag='MarketOrder')
        
        # short
        elif first_bar_close = 1:
                self.sl_price = consolidated.High
                self.tp_price = first_bar_close - (R * self.profit_target_multiplier)
                self.MarketOrder(self.market, -quantity, tag='MarketOrder')

def OnOrderEvent(self, orderEvent: OrderEvent) -> None:
    if orderEvent.Status == OrderStatus.Filled:
        order_ticket = self.Transactions.GetOrderTicket(orderEvent.OrderId)
        
        # NOTE tag text can be altered by lean, for example:
        # MarketOrder - Warning: fill at stale price {datetime}, using QuoteBar data.
        # that's the reason 'in' keyword is used
        if 'MarketOrder' in order_ticket.Tag:
            self.stop_loss_ticket = self.StopMarketOrder(self.market, -order_ticket.Quantity, self.sl_price)
            self.take_profit_ticket = self.LimitOrder(self.market, -order_ticket.Quantity, self.tp_price)

        # either SL or TP
        else:
            self.cancel_open_orders()

def cancel_open_orders(self) -> None:
    # cancel all opened orders
    orders_to_cancel = self.Transactions.GetOrderTickets(lambda order_ticket: order_ticket.Status not in [OrderStatus.Filled, OrderStatus.Canceled, OrderStatus.Invalid])
    for ticket in orders_to_cancel:
        response = ticket.Cancel()

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee:float = parameters.Order.AbsoluteQuantity * 0.0005
    return OrderFee(CashAmount(fee, "USD"))
