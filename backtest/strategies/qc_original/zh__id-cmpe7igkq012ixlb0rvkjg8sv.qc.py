# Original QuantConnect / library Python
# locale=zh slug="期货市场中的时间序列动量与波动率过滤相结合"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from collections import deque
class TimeSeriesMomentumVolatilityFilters(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.symbols = [
                'ICE_DX1',      # US Dollar Index Futures, Continuous Contract #1
                'CME_TY1',      # 10 Yr Note Futures, Continuous Contract #1
                'CME_ES1',      # E-mini S&P 500 Futures, Continuous Contract #1
                'CME_EC1',      # Euro FX Futures, Continuous Contract #1
                'CME_BP1',      # British Pound Futures, Continuous Contract #1
                'CME_HG1'       # Copper Futures, Continuous Contract
                ]
    
    self.period = 12*21
    self.vol_period = 21
    self.SetWarmUp(self.period)
    
    self.optimalization_count = 100
    
    self.data = {}
    self.macd = {}
    self.macd_signal = {}
    self.volatility = {}
    
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        
        self.data[symbol] = deque(maxlen=self.period+self.vol_period+1)
        self.volatility[symbol] = deque(maxlen=self.period)
        self.macd_signal[symbol] = deque(maxlen=self.period)
        
    self.macd['ICE_DX1'] = self.MACD('ICE_DX1', 1, 250, 1)
    self.macd['CME_TY1'] = self.MACD('CME_TY1', 1, 250, 1)
    self.macd['CME_HG1'] = self.MACD('CME_HG1', 1, 250, 1)
    
    self.macd['CME_EC1'] = self.MACD('CME_EC1', 1, 61, 1)
    self.macd['CME_BP1'] = self.MACD('CME_BP1', 1, 61, 1)
    
    self.macd['CME_ES1'] = self.MACD('CME_ES1', 3, 250, 1)
    
def OnData(self, data):
    for symbol in self.data:
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data.Keys:
            if data[symbol_obj]:
                price = data[symbol_obj].Value
                if price != 0:
                    self.data[symbol].append(price)
    if self.IsWarmingUp: return
    self.Liquidate()
    # Optimalization
    optimal_treshold = {}
    for symbol in self.symbols:
        if self.securities[symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[symbol]:
            self.liquidate(symbol)
            continue
        macd = self.macd[symbol]
        closes = np.array([x for x in self.data[symbol]])
        
        if macd.IsReady and len(closes) >= self.vol_period:
            # MACD SIGNAL = if short term MA is UNDER long term MA == 1 else -1
            self.macd_signal[symbol].append(1 if macd.Slow > macd.Fast else -1)
            daily_return = closes[:-1] / closes[1:] - 1
            vol = np.std(daily_return) * np.sqrt(252)
            self.volatility[symbol].append(vol)
        
            if len(closes) == self.data[symbol].maxlen and len(self.macd_signal[symbol]) == self.macd_signal[symbol].maxlen:
                values = np.array(closes)
                daily_changes = (values[1:] - values[:-1]) / values[:-1]
                
                vol_min = min(self.volatility[symbol])
                vol_max = max(self.volatility[symbol])
                
                vol_range = vol_max - vol_min
                vol_step = vol_range / self.optimalization_count
                
                avg_return = {}
                treshhold_value = vol_min
                while treshhold_value  self.macd[symbol].Slow:
                    self.SetHoldings(symbol, 1/count)
                else:
                    self.SetHoldings(symbol, -1/count)
            
            # high volatility enviroment
            else: 
                if self.macd[symbol].Fast > self.macd[symbol].Slow:
                    self.SetHoldings(symbol, -1/count)
                else:
                    self.SetHoldings(symbol, 1/count)
# Quantpedia data.
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
    data['back_adjusted'] = float(split[1])
    data['spliced'] = float(split[2])
    data.Value = float(split[1])
    if config.Symbol.Value not in QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol.Value]:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = data.Time.date()
    return data
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
