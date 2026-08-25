# Original QuantConnect / library Python
# locale=en slug="seasonality-in-equity-long-short-factor-strategies"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
import numpy as np
# endregion

class SeasonalityinEquityLongShortFactorStrategies(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    # daily price data
    self.perf:Dict[str, float] = {}
    self.period:int = 21
    self.leverage:int = 10
    self.quantile:int = 4
    self.SetWarmUp(self.period, Resolution.Daily)

    # monthly returns
    self.monthly_returns:Dict[str, float] = {}
    self.min_seasonal_period:int = 5
    
    csv_string_file:str = self.Download('data.quantpedia.com/backtesting_data/equity/quantpedia_strategies/backtest_end_year.csv')
    lines:str = csv_string_file.split('\r\n')
    last_id:None|str = None
    for line in lines[1:]:
        split:str = line.split(';')
        id:str = str(split[0])
        
        data:QuantpediaEquity = self.AddData(QuantpediaEquity, id, Resolution.Daily)
        data.SetLeverage(self.leverage)
        data.SetFeeModel(CustomFeeModel())

        self.perf[id] = self.ROC(id, self.period, Resolution.Daily)
        self.monthly_returns[id] = []
        
        if not last_id:
            last_id = id

    self.recent_month:int = -1

def OnData(self, data):
    if self.IsWarmingUp:
        return
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    
    seasonal_return:Dict[str, float] = {}
    _last_update_date:Dict[str, datetime.date] = QuantpediaEquity.get_last_update_date()

    for id in self.perf:
        if self.perf[id].IsReady:# and id in data and data[id]:
            if _last_update_date[id] > self.Time.date():
                # store monthly returns
                perf:float = self.perf[id].Current.Value
                self.monthly_returns[id].append((perf, self.Time.month - 1))
                
                # calculate seasonal performance of those strategies
                seasonal_monthly_returns:List[float] = [x[0] for x in self.monthly_returns[id] if x[1] == self.Time.month]
                    
                # monthly data for at least 5 years is ready
                if len(seasonal_monthly_returns) >= self.min_seasonal_period:
                    seasonal_return[id] = np.average(seasonal_monthly_returns[-self.min_seasonal_period:])

    long:List[str] = []
    short:List[str] = []
    
    # seasonal return sorting
    if len(seasonal_return) >= self.quantile:
        sorted_by_perf:List[str] = sorted(seasonal_return.items(), key = lambda x: x[1], reverse = True)
        quantile:int = len(sorted_by_perf) // self.quantile
        long = [x[0] for x in sorted_by_perf[:quantile]]
        short = [x[0] for x in sorted_by_perf[-quantile:]]

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
