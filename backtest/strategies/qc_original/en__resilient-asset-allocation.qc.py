# Original QuantConnect / library Python
# locale=en slug="resilient-asset-allocation"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List
from dateutil.relativedelta import relativedelta, FR
# endregion

class ResilientAssetAllocation(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    # set assets variables
    self.static_universe:List[str] = ['QQQ', 'IWN', 'IEF', 'TLT', 'GLD']
    self.cash_universe:List[str] = ['IEF', 'TLT']
    self.canary_universe:List[str] = ['VWO', 'BND']

    self.ue_period:int = 12

    momentum_periods:List[int] = [21, 63, 126, 252]
    self.score_weights:np.ndarray = np.array([12, 4, 2, 1])

    self.symbol_data:Dict[List] = {}

    # warm up of indicators
    self.SetWarmup(self.ue_period * 31, Resolution.Daily)

    for ticker in self.static_universe + self.cash_universe:
        self.AddEquity(ticker, Resolution.Daily)

    for ticker in self.canary_universe:
        self.AddEquity(ticker, Resolution.Daily)            
        self.symbol_data[ticker] = [self.MOMP(ticker, period, Resolution.Daily) for period in momentum_periods]

    # SMA assets
    self.ue:Symbol = self.AddData(UnemploymentRate, 'UE', Resolution.Daily).Symbol

    self.ue_window = RollingWindow[float](12)

def OnData(self, data: Slice) -> None:
    if self.IsWarmingUp:
        return

    # calculate the momentum scores of the canary symbols
    canary_score:List[float] = [np.dot(np.array([momentum.Current.Value for momentum in item[1]]), self.score_weights) \
                    for item in self.symbol_data.items() if item[0] in self.canary_universe and \
                    all(indicator.IsReady for indicator in item[1])]
  
    # wait until all the assets' indicators are warmed-up
    if len(canary_score) != len(self.canary_universe):
        return

    # rebalance when 'UE' data are in - monthly
    if data.ContainsKey(self.ue) and data[self.ue]:
 
        self.ue_window.Add(data[self.ue].Value)

        if not self.ue_window.IsReady:
            return

        if self.ue_window.IsReady:
            invested_tickers:List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
            traded_universe:List[str] = self.static_universe if not self.Portfolio.Invested else invested_tickers

            # change allocation of assets
            if not self.Portfolio.Invested:
                # both trends are positive
                if data[self.ue].Value > self.ue_window[self.ue_window.Count-1] and canary_score[0]  last_update_date:
                self.Liquidate()

class UnemploymentRate(PythonData):
def GetSource(self, config: SubscriptionDataConfig, date: datetime, isLiveMode: bool) -> SubscriptionDataSource:
    return SubscriptionDataSource('data.quantpedia.com/backtesting_data/economic/UNEMPLOYMENT_RATE.csv', SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)

_last_update_date:datetime.date = datetime(1,1,1).date()

@staticmethod
def get_last_update_date() -> datetime.date:
   return UnemploymentRate._last_update_date

def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:
    data = UnemploymentRate()
    data.Symbol = config.Symbol

    if not line[0].isdigit(): return None
    split = line.split(';')
    
    # Parse the CSV file's columns into the custom data class - first Friday of the month
    data.Time = (datetime.strptime(split[0], '%Y-%m-%d').date() + relativedelta(weekday=FR(1))) + timedelta(days=1)

    if data.Time.date() > UnemploymentRate._last_update_date:
        UnemploymentRate._last_update_date = data.Time.date()

    data.Value = float(split[1])
    
    return data
