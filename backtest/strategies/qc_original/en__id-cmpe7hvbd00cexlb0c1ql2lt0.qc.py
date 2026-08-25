# Original QuantConnect / library Python
# locale=en slug="迟缓型资产配置策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List
from dateutil.relativedelta import relativedelta, FR
# endregion

class LethargicAssetsAllocation(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    # set assets variables
    self.static_universe:List[str] = ['IWD', 'GLD', 'IEF']
    self.risky_asset:str = 'QQQ'
    self.safe_asset:str = 'SHY'
    
    self.spy_period:int = 10 * 21
    self.ue_period:int = 12

    # warm up of indicators
    self.SetWarmup(self.ue_period * 31, Resolution.Daily)

    for ticker in self.static_universe + [self.risky_asset, self.safe_asset]:
        self.AddEquity(ticker, Resolution.Daily)

    # SMA assets
    self.spy:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.ue:Symbol = self.AddData(UnemploymentRate, 'UE', Resolution.Daily).Symbol

    self.spy_sma = self.SMA(self.spy, self.spy_period, Resolution.Daily)
    self.ue_sma = self.SMA(self.ue, self.ue_period, Resolution.Daily)

def OnData(self, data: Slice) -> None:
    if self.IsWarmingUp:
        return

    # rebalance when 'UE' data are in - monthly
    if data.ContainsKey(self.ue) and data.ContainsKey(self.spy) and data[self.spy] and data[self.ue]:
        # both SMA indicators are warmed up and ready
        if all(sma.IsReady for sma in [self.spy_sma, self.ue_sma]):
            invested_tickers:List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
            traded_universe:List[str] = self.static_universe if not self.Portfolio.Invested else invested_tickers

            # change allocation of assets
            if not self.Portfolio.Invested:
                # both trends are negative - UE rate has risen
                if data[self.spy].Value  self.ue_sma.Current.Value:
                    traded_universe += [self.safe_asset]
                else:
                    traded_universe += [self.risky_asset]
            else:
                # SPY trend is positive
                if data[self.spy].Value > self.spy_sma.Current.Value:
                    if self.risky_asset not in traded_universe:
                        traded_universe = list(map(lambda x: x.replace(self.safe_asset, self.risky_asset), traded_universe))
            
            # firstly, liquidate symbols that should not be held
            for ticker in invested_tickers:
                if ticker not in traded_universe:
                    self.Liquidate(ticker)
            
            # rebalance new portfolio
            for ticker in traded_universe:
                if ticker in data and data[ticker]:
                    self.SetHoldings(ticker, 1 / len(traded_universe))
    else:
        if self.Portfolio.Invested:
            last_update_date:datetime.date = UnemploymentRate.get_last_update_date()
            
            # custom data stopped comming in
            if self.Securities[self.ue].GetLastData() and self.Time.date() > last_update_date:
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
