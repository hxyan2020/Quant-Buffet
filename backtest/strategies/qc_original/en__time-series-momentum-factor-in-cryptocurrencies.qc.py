# Original QuantConnect / library Python
# locale=en slug="time-series-momentum-factor-in-cryptocurrencies"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
#endregion
class TimeSeriesMomentumCryptocurrencies(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    self.symbols = ['BTCUSD', 'ETCUSD', 'ETHUSD', 'LTCUSD', 'XMRUSD', 'ZECUSD']
    self.data = {}
    self.percentage_traded = 0.1
    
    for symbol in self.symbols:
        data = self.AddCrypto(symbol, Resolution.Daily, Market.Bitfinex)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(10)
        self.data[symbol] = RollingWindow[float](5)
    
def OnData(self, data):
    for symbol in self.data:
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data.Bars and data[symbol_obj]:
            self.data[symbol].Add(data[symbol_obj].Value)
    if self.Time.date().weekday() != 0:
        return
    perf_vol = {}
    
    for symbol in self.symbols:
        if self.data[symbol].IsReady:
            prices = np.array([x for x in self.data[symbol]])
            perf = prices[0] / prices[-1] - 1
            
            daily_returns = prices[:-1] / prices[1:] - 1
            vol = np.std(daily_returns)
            perf_vol[symbol] = (perf, vol)
    # Volatility weighting
    total_vol = sum([1 / x[1][1] for x in perf_vol.items()])
    if total_vol == 0: return
    weight = {}
    for symbol in perf_vol:
        vol = perf_vol[symbol][1]
        if vol != 0:
            weight[symbol] = (1.0 / vol) / total_vol
        else: 
            weight[symbol] = 0
    # Trade execution.
    long = [x[0] for x in perf_vol.items() if x[1][0] > 0]
    invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long:
            self.Liquidate(symbol)
    for symbol in long:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, self.percentage_traded * weight[symbol])
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
