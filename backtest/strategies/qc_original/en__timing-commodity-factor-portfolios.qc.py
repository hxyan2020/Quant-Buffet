# Original QuantConnect / library Python
# locale=en slug="timing-commodity-factor-portfolios"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from collections import deque
from AlgorithmImports import *
import numpy as np
class TimingCommodityFactor(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2002, 1, 1)
    self.SetCash(100000)
    self.symbols = [
        "CME_S1",   # Soybean Futures, Continuous Contract
        "CME_W1",   # Wheat Futures, Continuous Contract
        "CME_SM1",  # Soybean Meal Futures, Continuous Contract
        "CME_BO1",  # Soybean Oil Futures, Continuous Contract
        "CME_C1",   # Corn Futures, Continuous Contract
        "CME_O1",   # Oats Futures, Continuous Contract
        "CME_LC1",  # Live Cattle Futures, Continuous Contract
        "CME_FC1",  # Feeder Cattle Futures, Continuous Contract
        "CME_LN1",  # Lean Hog Futures, Continuous Contract
        "CME_GC1",  # Gold Futures, Continuous Contract
        "CME_SI1",  # Silver Futures, Continuous Contract
        "CME_PL1",  # Platinum Futures, Continuous Contract
        "CME_CL1",  # Crude Oil Futures, Continuous Contract
        "CME_HG1",  # Copper Futures, Continuous Contract
        "CME_LB1",  # Random Length Lumber Futures, Continuous Contract
        # "CME_NG1",  # Natural Gas (Henry Hub) Physical Futures, Continuous Contract
        "CME_PA1",  # Palladium Futures, Continuous Contract 
        "CME_RR1",  # Rough Rice Futures, Continuous Contract
        "CME_DA1",  # Class III Milk Futures
        "ICE_RS1",  # Canola Futures, Continuous Contract
        "ICE_GO1",  # Gas Oil Futures, Continuous Contract
        "CME_RB2",  # Gasoline Futures, Continuous Contract
        "CME_KW2",  # Wheat Kansas, Continuous Contract
        "ICE_WT1",  # WTI Crude Futures, Continuous Contract
                    
        "ICE_CC1",  # Cocoa Futures, Continuous Contract 
        "ICE_CT1",  # Cotton No. 2 Futures, Continuous Contract
        "ICE_KC1",  # Coffee C Futures, Continuous Contract
        "ICE_O1",   # Heating Oil Futures, Continuous Contract
        "ICE_OJ1",  # Orange Juice Futures, Continuous Contract
        "ICE_SB1",  # Sugar No. 11 Futures, Continuous Contract
    ]
    self.data = {}
    self.top = {}
    self.low = {}
    
    ret_period = 120
    vol_period = 60
    ma_period = 5
    
    self.SetWarmUp(max(ret_period, vol_period, ma_period))
    
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetLeverage(5)
        data.SetFeeModel(CustomFeeModel())
        
        ma = self.SMA(symbol, ma_period, Resolution.Daily)
        self.data[symbol] = SymbolData(symbol, ret_period, vol_period, ma)
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.At(0, 0), self.Rebalance)
def OnData(self, data):
    last_update_date = {}
    for symbol in self.data:
        # data is still coming
        if self.securities[symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[symbol]:
            self.liquidate(symbol)
            self.data[symbol].History.clear()
            continue
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data.Keys:
            if data[symbol_obj]:
                price = data[symbol_obj].Value
                self.data[symbol].Update(price)
                last_update_date[symbol] = self.Time.date()
    
    if self.IsWarmingUp: return

    sma_top = list(data for data in self.top if data[1].IsReady() and data[1].Price > data[1].MA.Current.Value and data[0] in last_update_date)
    sma_low = list(data for data in self.low if data[1].IsReady() and data[1].Price  symbol_data.MA.Current.Value:
                if symbol_data.Weight != 0:
                    self.SetHoldings(symbol, symbol_data.Weight)
        elif self.Portfolio[symbol].IsLong:
            if symbol_data.Price = symbol_data.MA.Current.Value:
                self.Liquidate(symbol)       
def Rebalance(self):
    if self.IsWarmingUp: return
    self.Liquidate()
    sorted_by_ret = sorted([d for d in self.data.items() if d[1].IsReady()], key=lambda x: x[1].Return(), reverse = True)
    self.top = sorted_by_ret[:int(1/3 * len(sorted_by_ret))]
    self.low = sorted_by_ret[-int(1/3 * len(sorted_by_ret)):]
    
    # Weighting
    total_vol = sum((1.0/data[1].Volatility()) for data in self.top if data[1].IsReady()) + sum((1.0/data[1].Volatility()) for data in self.low if data[1].IsReady())
    for data in self.top + self.low:
        if data[1].IsReady():
            vol = data[1].Volatility()
            data[1].Weight = (1.0 / vol) / total_vol
class SymbolData:
def __init__(self, symbol, ret_lookback, vol_lookback, ma):
    self.Symbol = symbol
    self.History = deque(maxlen=max(ret_lookback, vol_lookback))
    self.Price = 0.0
    self.MA = ma
    self.Weight = 0
    
    self.ret_lookback = ret_lookback
    self.vol_lookback = vol_lookback
def IsReady(self):
    return len(self.History) == self.History.maxlen
    
def Update(self, value):
    self.Price = float(value)
    self.History.append(float(value))
def Return(self):
    prices = np.array(self.History)[-self.ret_lookback:]
    return (prices[-1]-prices[0])/prices[0]
def Volatility(self):
    prices = np.array(self.History)[-self.vol_lookback:]
    returns = (prices[1:]-prices[:-1])/prices[:-1]
    return np.std(returns)
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
