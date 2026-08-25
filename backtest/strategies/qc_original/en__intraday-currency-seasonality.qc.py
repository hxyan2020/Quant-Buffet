# Original QuantConnect / library Python
# locale=en slug="intraday-currency-seasonality"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class IntradayCurrencySeasonality(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    data = self.AddForex("EURUSD", Resolution.Minute, Market.FXCM)
    data.SetFeeModel(CustomFeeModel())
    self.symbol = data.Symbol
def OnData(self, data):
    time = self.Time
    
    if time.hour == 3 and time.minute == 0:     # NY
        self.SetHoldings(self.symbol,-1)
    if time.hour == 11 and time.minute == 0:    # NY
        self.Liquidate(self.symbol)
        self.SetHoldings(self.symbol,1)
    if time.hour == 17 and time.minute == 0:    # NY
        self.Liquidate(self.symbol)
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
