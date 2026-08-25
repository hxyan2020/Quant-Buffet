# Original QuantConnect / library Python
# locale=en slug="mean-reversion-and-trend-following-based-on-min-and-max-in-btc"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# endregion

class MeanreversionandTrendFollowingBasedonMINandMAXinBTC(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    
    # NOTE Coinbase Pro, CoinAPI, and Bitfinex data is all set in UTC Time. This means that when accessing data from this brokerage, all data will be time stamped in UTC Time.
    self.crypto:Crypto = self.AddCrypto("BTCUSD", Resolution.Minute, Market.GDAX)
    self.crypto.SetLeverage(10)
    self.crypto.SetFeeModel(CustomFeeModel())
    self.crypto:Symbol = self.crypto.Symbol

    self.period:int = 10
    self.daily_prices:RollingWindow = RollingWindow[float](self.period)
    self.daily_close_hour:int = 22

def OnData(self, data):
    if self.crypto in data and data[self.crypto]:
        time:datetime.datetime = self.Time
        if time.hour == self.daily_close_hour and time.minute == 0:
            price:float = data[self.crypto].Value
            self.daily_prices.Add(price)

            if self.daily_prices.IsReady:
                daily_prices:list[float] = [x for x in self.daily_prices]
                daily_max:float = np.max(daily_prices)
                daily_min:float = np.min(daily_prices)

                # open/rebalance long position
                if price == daily_max or price == daily_min:
                    self.SetHoldings(self.crypto, 1)
                else:
                    # close position
                    if self.Portfolio[self.crypto].Invested:
                        self.Liquidate(self.crypto)

class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
