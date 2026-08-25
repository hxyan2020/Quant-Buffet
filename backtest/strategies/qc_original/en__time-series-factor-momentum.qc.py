# Original QuantConnect / library Python
# locale=en slug="time-series-factor-momentum"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from typing import List, Dict
#endregion
class TimeSeriesFactorMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100000)
    
    # daily price data
    self.data:Dict[str, SymbolData] = {}
    self.period:int = 12 * 21 * 3 # Three years daily closes
    self.leverage:int = 10
    self.SetWarmUp(self.period, Resolution.Daily)
    
    csv_string_file:str = self.Download('data.quantpedia.com/backtesting_data/equity/quantpedia_strategies/backtest_end_year.csv')
    lines:str = csv_string_file.split('\r\n')
    last_id:None|str = None
    for line in lines[1:]:
        split:str = line.split(';')
        id:str = str(split[0])
        
        data:QuantpediaEquitz = self.AddData(QuantpediaEquity, id, Resolution.Daily)
        data.SetLeverage(self.leverage)
        data.SetFeeModel(CustomFeeModel())
        self.data[id] = SymbolData(self.period)
        
        if not last_id:
            last_id = id
            
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.recent_month:int = -1

def OnData(self, data):
    if self.IsWarmingUp:
        return
    
    # Update equity close each day.
    for symbol in self.data:
        if symbol in data and data[symbol]:
            self.data[symbol].update(data[symbol].Value)
    
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    
    long:List[str] = []
    short:List[str] = []
    _last_update_date:Dict[str, datetime.date] = QuantpediaEquity.get_last_update_date()
    for symbol in self.data:
        if not self.data[symbol].is_ready():
            continue
        
        if symbol in data and data[symbol]:
            if _last_update_date[symbol] > self.Time.date():
                # Calculate factore score for each equity
                equity_score:float = self.data[symbol].calculate_z_score()
                
                # Go long if equity_score is positive
                # and short if equity_score is negative
                if equity_score >= 0:
                    long.append(symbol)
                else:
                    short.append(symbol)
            
    # Trade execution.
    invested:List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
            
    long_length:int = len(long)
    short_length:int = len(short)
    
    # Equally weighted long and short portfolio
    for symbol in long:
        self.SetHoldings(symbol, 1 / long_length)
        
    for symbol in short:
        self.SetHoldings(symbol, -1 / short_length)
class SymbolData():
def __init__(self, period:int):
    self.closes:RollingWindow[float] = RollingWindow[float](period)
    
def update(self, close:float):
    self.closes.Add(close)
    
def is_ready(self) -> bool:
    return self.closes.IsReady
    
def calculate_z_score(self) -> float:
    closes:List[float] = [x for x in self.closes]
    
    values:np.ndarray = np.array(closes) # Full period daily closes
    daily_returns:np.ndarray = (values[:-1] - values[1:]) / values[1:] # Daily returns for full period
    full_period_volatility:float = np.std(daily_returns) # Full period volatility
    
    monthly_returns:List[float] = [(values[i] - values[i + 20]) / values[i + 20] for i in range(0, len(values), 21)]
    
    # This equation is first in paper on page 10.
    return min(max( sum(monthly_returns) / full_period_volatility, -2), 2)
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
