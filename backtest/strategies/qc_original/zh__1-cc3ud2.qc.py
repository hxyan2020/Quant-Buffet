# Original QuantConnect / library Python
# locale=zh slug="短期（1个月）货币动量"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class ShortTermMomentumCurrencies(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.symbols = [
        "CME_AD1", # Australian Dollar Futures, Continuous Contract #1
        "CME_BP1", # British Pound Futures, Continuous Contract #1
        "CME_CD1", # Canadian Dollar Futures, Continuous Contract #1
        "CME_EC1", # Euro FX Futures, Continuous Contract #1
        "CME_JY1", # Japanese Yen Futures, Continuous Contract #1
        "CME_MP1", # Mexican Peso Futures, Continuous Contract #1
        "CME_NE1",# New Zealand Dollar Futures, Continuous Contract #1
        "CME_SF1", # Swiss Franc Futures, Continuous Contract #1
    ]
    
    self.period = 21
    self.quantile = 5
    self.SetWarmUp(self.period)
    
    self.data = {}
    
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetLeverage(5)
        data.SetFeeModel(CustomFeeModel())
        
        self.data[symbol] = RollingWindow[float](self.period)
    
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.At(0, 0), self.Rebalance)
def OnData(self, data):
    for symbol in self.data:
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data.Keys:
            if data[symbol_obj]:
                price = data[symbol_obj].Value
                if price != 0:
                    self.data[symbol].Add(price)
    
def Rebalance(self):
    if self.IsWarmingUp: return
    returns = {}
    for symbol in self.data:
        if self.data[symbol].IsReady:
            # Check if data is still coming.
            if self.securities[symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[symbol]:
                self.liquidate(symbol)
                continue
            
            ret = self.data[symbol][0] / self.data[symbol][self.period-1] - 1
            returns[symbol] = ret
    
    long = []
    short = []
    if len(returns) >= self.quantile:
        # Return sorting.
        sorted_by_return = sorted(returns.items(), key = lambda x: x[1], reverse = True)
        quintile = int(len(sorted_by_return) / self.quantile)
        long = [x[0] for x in sorted_by_return[:quintile]]
        short = [x[0] for x in sorted_by_return[-quintile:]]
    
    # Trade execution
    invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
    
    for symbol in long:
        self.SetHoldings(symbol, 1 / len(long))
    for symbol in short:
        self.SetHoldings(symbol, -1 / len(short))
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
