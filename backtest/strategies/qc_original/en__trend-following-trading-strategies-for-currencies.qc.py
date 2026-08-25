# Original QuantConnect / library Python
# locale=en slug="trend-following-trading-strategies-for-currencies"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from math import sqrt
from numpy import exp
class TrendFollowingTradingStrategiesforCurrencies(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols = [
                    "CME_AD1", # Australian Dollar Futures, Continuous Contract #1
                    "CME_BP1", # British Pound Futures, Continuous Contract #1
                    "CME_CD1", # Canadian Dollar Futures, Continuous Contract #1
                    "CME_EC1", # Euro FX Futures, Continuous Contract #1
                    "CME_JY1", # Japanese Yen Futures, Continuous Contract #1
                    "CME_MP1", # Mexican Peso Futures, Continuous Contract #1
                    "CME_NE1", # New Zealand Dollar Futures, Continuous Contract #1
                    "CME_SF1", # Swiss Franc Futures, Continuous Contract #1
                    ]
    
    self.period = 12 * 21
    self.SetWarmUp(self.period)
    
    self.leverage = 5
    # Daily price data.
    self.data = {}
    
    # EMA pairs.
    self.ema_8_24 = {}
    self.ema_16_48 = {}
    self.ema_32_96 = {}
    
    self.Settings.MinAbsolutePortfolioTargetPercentage = 1e-30
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage * 2)
        
        self.data[symbol] = RollingWindow[float](self.period)

        self.ema_8_24[symbol] = [self.EMA(symbol, 8, Resolution.Daily), self.EMA(symbol, 24, Resolution.Daily)]
        self.ema_16_48[symbol] = [self.EMA(symbol, 16, Resolution.Daily), self.EMA(symbol, 48, Resolution.Daily)]
        self.ema_32_96[symbol] = [self.EMA(symbol, 32, Resolution.Daily), self.EMA(symbol, 96, Resolution.Daily)]
        
def OnData(self, data):
    # Store daily price data.
    for symbol in self.symbols:
        if symbol in data and data[symbol]:
            price = data[symbol].Value
            self.data[symbol].Add(price)
    
    if self.IsWarmingUp: return
    signal = {}
    for symbol in self.symbols:
        if self.securities[symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[symbol]:
            self.liquidate(symbol)
            continue
        # Daily data is ready.
        if not self.data[symbol].IsReady:
            continue
    
        # First signal.
        # Source paper equation 5, page 5.
        x1 = self.ema_8_24[symbol][0].Current.Value - self.ema_8_24[symbol][1].Current.Value
        x2 = self.ema_16_48[symbol][0].Current.Value - self.ema_16_48[symbol][1].Current.Value
        x3 = self.ema_32_96[symbol][0].Current.Value - self.ema_32_96[symbol][1].Current.Value
        
        x = np.array([x1, x2, x3])
        prices = [x for x in self.data[symbol]]
        price_std_short = np.std(prices[:3 * 21])
        price_std_long = np.std(prices)
        
        # Normalization.
        # Source paper equation 6, page 6
        y = x / price_std_short
        
        # Normalization #2.
        # Source paper equation 7, page 6
        z = y / price_std_long
        
        # Response function.
        u = (z * exp((-z**2) / 4)) / (sqrt(2) * exp(-1/2))
        signal[symbol] = sum(1/len(z) * u)
    
    if len(signal) == 0:
        self.Liquidate()
        return
                
    # Trade execution
    for symbol, weight in signal.items():
        w = (1/len(signal)) * (self.leverage * weight)
        self.SetHoldings(symbol, w)
        
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
# Quantpedia data
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
_last_update_date:Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return QuantpediaFutures._last_update_date
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/futures/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaFutures()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['settle'] = float(split[1])
    data.Value = float(split[1])
    if config.Symbol.Value not in QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol.Value]:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = data.Time.date()
    return data
