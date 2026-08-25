# Original QuantConnect / library Python
# locale=zh slug="外汇市场中的时间序列动量与波动率过滤相结合"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import datetime
import numpy as np
#endregion
class TimeSeriesMomentumCombinedwithVolatilityFiltersinFOREX(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    self.period = 12*21
    self.SetWarmUp(self.period)
    
    self.current_date = -1
    
    self.symbols = ["USDJPY", "GBPUSD", "EURUSD", "USDCHF", "USDCAD", "AUDUSD", "EURGBP", "EURJPY", "EURCHF"]
    self.data = {}
                   
    for symbol in self.symbols:
        data = self.AddForex(symbol, Resolution.Minute, Market.FXCM)
        data.SetFeeModel(CustomFeeModel())
    
        if symbol not in self.data:
            ma32 = SimpleMovingAverage(symbol, 32)
            ma61 = SimpleMovingAverage(symbol, 61)
            ma117 = SimpleMovingAverage(symbol, 117)
            
            self.data[symbol] = SymbolData(symbol, self.period, ma32, ma61, ma117, self.GetWeight(symbol))
def OnData(self, data):
    if self.Time.time() == datetime.time(0,0,0):
        # Updating last day close.
        for symbol in self.symbols:
            if symbol in data and data[symbol]:
                close = data[symbol].Value
                self.data[symbol].update(self.Time, close)
    
    # Trading one minute before day ends.
    if (self.Time + timedelta(minutes=1)).date() ==  self.current_date: 
        return
            
    self.current_date = (self.Time + timedelta(minutes=1)).date()
    
    # Wait until data are warmed up.
    if self.IsWarmingUp: return

    # Trade execution
    self.Liquidate()
    
    for symbol in self.symbols:
        if self.data[symbol].is_ready():
            yearly_vol = self.data[symbol].volatility(self.period)
            monthly_vol = self.data[symbol].volatility(21)

            price = self.data[symbol].Price
            ma32 = self.data[symbol].ma32()
            ma61 = self.data[symbol].ma61()
            ma117 = self.data[symbol].ma117()

            traded_weight = 0
            weight = self.data[symbol].Weight
                
            # Trend startegy
            if monthly_vol  ma61 and ma61 > ma117:
                    if price > ma32 and price > ma61 and price > ma117:
                        traded_weight = weight
                    elif price > ma61 and price > ma117:
                        traded_weight = weight * 2/3
                    elif price > ma117:
                        traded_weight = weight * 1/3
                    else:
                        continue
                #Short        
                elif ma32  yearly_vol:
                #Long        
                if ma32  ma61 and ma61 > ma117:
                    if price > ma32 and price > ma61 and price > ma117:
                        traded_weight = -weight
                    elif price > ma61 and price > ma117:
                        traded_weight = -weight * 2/3
                    elif price > ma117:
                        traded_weight = -weight * 1/3
                    else:
                        continue
                        
                self.SetHoldings(symbol, traded_weight)
                    
def GetWeight(self, argument):
    switcher = {
        "USDJPY": 0.2113,
        "GBPUSD": 0.1749,
        "EURUSD": 0.3576,
        "USDCHF": 0.0557,
        "USDCAD": 0.0507,
        "AUDUSD": 0.0642,
        "EURGBP": 0.0307,
        "EURJPY": 0.0364,
        "EURCHF": 0.0186,
    }
    return switcher.get(argument, "0.0")
class SymbolData:
def __init__(self, symbol, lookback, ma32, ma61, ma117, weight):
    self.Symbol = symbol
    self.Price = None
    self.MA32 = ma32
    self.MA61 = ma61
    self.MA117 = ma117
    self.Weight = weight
    self.History = RollingWindow[float](lookback)
def update(self, time, value):
    self.Price = value
    self.History.Add(value)
    self.MA32.Update(time, value)
    self.MA61.Update(time, value)
    self.MA117.Update(time, value)
    
def is_ready(self):
    return self.MA32.IsReady and self.MA61.IsReady and self.MA32.IsReady and self.History.IsReady

def ma32(self):
    return self.MA32.Current.Value
def ma61(self):
    return self.MA61.Current.Value
def ma117(self):
    return self.MA117.Current.Value
    
def volatility(self, period):
    prices = np.array([x for x in self.History])[:period]
    returns = (prices[:-1]-prices[1:])/prices[1:]
    return np.std(returns) * np.sqrt(period)
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
