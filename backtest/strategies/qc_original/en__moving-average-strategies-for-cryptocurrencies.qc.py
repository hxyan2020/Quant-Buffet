# Original QuantConnect / library Python
# locale=en slug="moving-average-strategies-for-cryptocurrencies"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class MovingAverageCryptocurrencies(QCAlgorithm):
def Initialize(self):
    self.set_start_date(2015, 1, 1)
    self.set_cash(100_000)
    self.symbol: Symbol = self.add_crypto('BTCUSD', Resolution.DAILY, Market.BITFINEX).symbol
    self.securities[self.symbol].set_fee_model(CustomFeeModel())
    
    self.MAs: List[SimpleMovingAverage] = [
        self.SMA(self.symbol, 1, Resolution.Daily),
        self.SMA(self.symbol, 2, Resolution.Daily),
        self.SMA(self.symbol, 4, Resolution.Daily),
        self.SMA(self.symbol, 10, Resolution.Daily),
        self.SMA(self.symbol, 20, Resolution.Daily)
    ]
        
def OnData(self, slice: Slice) -> None:
    if not self.symbol in slice: return
        
    price: float = slice[self.symbol].Value
    if price == 0: return
    long_signal_count: int = 0
    for ma in self.MAs:
        if ma.IsReady:
            if price > ma.Current.Value:
                long_signal_count += 1
    else:
        self.Liquidate()
    
    w: float = (0.1 / len(self.MAs)) * long_signal_count
    self.SetHoldings(self.symbol, w)
            
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
