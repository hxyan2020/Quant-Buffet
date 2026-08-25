# Original QuantConnect / library Python
# locale=en slug="overnight-seasonality-in-bitcoin-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# endregion

class OvernightSeasonalityinBitcoin(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2016, 1, 1)
    self.SetCash(100000)
    
    # NOTE Coinbase Pro, CoinAPI, and Bitfinex data is all set in UTC Time. This means that when accessing data from this brokerage, all data will be time stamped in UTC Time.
    self.crypto = self.AddCrypto("BTCUSD", Resolution.Minute, Market.Bitfinex)
    self.crypto.SetLeverage(10)
    self.crypto.SetFeeModel(CustomFeeModel())
    self.crypto = self.crypto.Symbol

    self.open_trade_hour:int = 22
    self.close_trade_hour:int = 0

def OnData(self, data):
    if self.crypto in data and data[self.crypto]:
        time:datetime.datetime = self.UtcTime

        # open long position
        if time.hour == self.open_trade_hour and time.minute == 0:
            self.SetHoldings(self.crypto, 1)
        
    # close position
    if time.hour == self.close_trade_hour and time.minute == 0:
        if self.Portfolio[self.crypto].Invested:
            self.Liquidate(self.crypto)

class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
