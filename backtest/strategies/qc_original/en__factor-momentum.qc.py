# Original QuantConnect / library Python
# locale=en slug="factor-momentum"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class FactorMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    # daily price data
    self.data:Dict[str, float] = {}
    self.period:int = 12 * 21
    self.SetWarmUp(self.period, Resolution.Daily)
    self.leverage:int = 10
    self.traded_count:int = 8
    csv_string_file:str = self.Download('data.quantpedia.com/backtesting_data/equity/quantpedia_strategies/backtest_end_year.csv')
    lines:str = csv_string_file.split('\r\n')
    last_id:None|str = None
    for line in lines[1:]:
        split:str = line.split(';')
        id:str = str(split[0])
        backtest_to:int = int(split[1])
        
        data:QuantpediaEquity = self.AddData(QuantpediaEquity, id, Resolution.Daily)
        data.SetLeverage(self.leverage)
        data.SetFeeModel(CustomFeeModel())
        
        self.data[id] = self.ROC(id, self.period, Resolution.Daily)
        
        if not last_id:
            last_id = id
    self.recent_month:int = -1
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

def OnData(self, data):
    if self.IsWarmingUp:
        return
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    
    if self.Time.month != 1: return
    
    _last_update_date:Dict[str, datetime.date] = QuantpediaEquity.get_last_update_date()
    
    # calculate performance of those strategies
    performance:Dict[str, float] = { x : self.data[x].Current.Value for x in self.data \
                if self.data[x].IsReady and \
                x in data and data[x] and \
                _last_update_date[x] > self.Time.date() }

    long:List[str] = []
    short:List[str] = []
    
    # performance sorting
    if len(performance) >= self.traded_count*2:
        sorted_by_perf:List[str] = sorted(performance.items(), key = lambda x: x[1], reverse = True)
        long = [x[0] for x in sorted_by_perf[:self.traded_count]]
        short = [x[0] for x in sorted_by_perf[-self.traded_count:]]
    # trade execution
    invested:List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
    
    long_count:int = len(long)                
    short_count:int = len(short)
    
    for symbol in long:
        self.SetHoldings(symbol, 1 / long_count)
    for symbol in short:
        self.SetHoldings(symbol, -1 / short_count)
# Quantpedia strategy equity curve data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaEquity(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/equity/quantpedia_strategies/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
_last_update_date:Dict[str, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[str, datetime.date]:
   return QuantpediaEquity._last_update_date
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaEquity()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    data['close'] = float(split[1])
    data.Value = float(split[1])
    
    # store last update date
    if config.Symbol.Value not in QuantpediaEquity._last_update_date:
        QuantpediaEquity._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaEquity._last_update_date[config.Symbol.Value]:
        QuantpediaEquity._last_update_date[config.Symbol.Value] = data.Time.date()
    
    return data
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
