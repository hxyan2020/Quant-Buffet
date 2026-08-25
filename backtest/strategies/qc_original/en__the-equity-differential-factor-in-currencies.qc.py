# Original QuantConnect / library Python
# locale=en slug="the-equity-differential-factor-in-currencies"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class EquityDifferentialCurrencies(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2004, 1, 1)
    self.SetCash(100000)
    
    self.symbols = {
        'CME_AD1' : 'ASX_YAP1',
        'CME_BP1' : 'LIFFE_Z1',
        'CME_CD1' : 'LIFFE_FCE1',
        'CME_EC1' : 'EUREX_FSTX1',
        'CME_JY1' : 'SGX_NK1',
        'CME_SF1' : 'EUREX_FSMI1'
    }
    self.data = {}
    self.period = 12*21
    self.SetWarmUp(self.period)
    self.leverage = 5
    
    for symbol in self.symbols:
        index = self.symbols[symbol]
        
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetLeverage(self.leverage)
        data.SetFeeModel(CustomFeeModel())
        
        self.AddData(QuantpediaFutures, index, Resolution.Daily)
        self.data[index] = RollingWindow[float](self.period)
        
    first_key = [x for x in self.symbols.keys()][0]
    symbol = self.Symbol(self.symbols[first_key])
    self.rebalance_flag: bool = False
    self.Schedule.On(self.DateRules.MonthStart(symbol), self.TimeRules.At(0, 0), self.Rebalance)
def OnData(self, data):
    for symbol in self.symbols:
        index:str = self.symbols[symbol]
        if index in data and data[index]:
            price:float = data[index].Value
            self.data[index].Add(price)
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    if self.IsWarmingUp: return
    index_return = {}
    for symbol in self.symbols:
        index = self.symbols[symbol]
        if all([self.Securities[x].GetLastData() and self.Time.date()  index_return[eq_index2]:
                        self.SetHoldings(key_i, self.leverage*(1/count))
                        self.SetHoldings(key_j, -self.leverage*(1/count))
                    else:
                        self.SetHoldings(key_i, -self.leverage*(1/count))
                        self.SetHoldings(key_j, self.leverage*(1/count))
def Rebalance(self):
    self.rebalance_flag = True
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
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
