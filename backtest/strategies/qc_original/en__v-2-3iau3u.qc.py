# Original QuantConnect / library Python
# locale=en slug="自适应性质的资产配置策略-v-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict, Union
import data_tools
# endregion

class AdaptiveAssetAllocation(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    # set asset variables
    self.risk_assets:List[str] = ['SPY', 'QQQ', 'IWM', 'VGK', 'EWJ', 'EEM', 'VNQ', 'DBC', 'DBA', 'GLD', 'LQD', 'HYG', 'TLT']
    self.cash_assets:List[str] = ['SHV', 'IEF']

    self.roc_periods:List[int] = [3 * 21, 6 * 21, 12 * 21]
    self.sma_periods:List[int] = [50, 100, 200]
    self.warm_up_period:int = 12 * 21
    self.top_equities:int = 5

    self.roc:Dict[str, List[RateOfChange]] = {}
    self.sma:Dict[str, List[SimpleMovingAverage]] = {}
    self.ram:Dict[str, List[CustomRAM]] = {}

    # warm up of indicators
    self.SetWarmup(self.warm_up_period, Resolution.Daily)

    for ticker in self.risk_assets + self.cash_assets:
        # price data subscription
        data:Security = self.AddEquity(ticker, Resolution.Daily)
        
        # indicators subscription
        self.sma[ticker] = [self.SMA(ticker, period, Resolution.Daily) for period in self.sma_periods]
        self.roc[ticker] = [self.ROC(ticker, period, Resolution.Daily) for period in self.roc_periods]

        self.ram[ticker] = []
        for period in self.roc_periods:
            self.custom_indicator = data_tools.CustomRAM('RAM', period)
            self.RegisterIndicator(ticker, self.custom_indicator, Resolution.Daily)      
            self.ram[ticker].append(self.custom_indicator)

    self.recent_month:int = -1

def OnData(self, data:Slice) -> None:
    if self.IsWarmingUp:
        return

    aggregated_momentum:Dict[str, float] = {}
    rebalance_flag:bool = False

    for ticker in self.risk_assets + self.cash_assets:
        if ticker in data and data[ticker]:
            indicators:List[Union[RateOfChange, SimpleMovingAverage, CustomRAM]] = self.roc[ticker] + self.sma[ticker] + self.ram[ticker]

            # all indicators are warmed up and ready
            if all(indicator.IsReady for indicator in indicators):
                # calculate aggregated momentum average
                roc:float = sum([mom.Current.Value for mom in self.roc[ticker]])
                ram:float = sum([mom.Current.Value for mom in self.ram[ticker]])
                sma:float = sum([((data[ticker].Price / sma.Current.Value) - 1) for sma in self.sma[ticker]])
                aggregated_momentum[ticker] = (roc + sma + ram) / len(indicators)

            rebalance_flag = True
    
    # monthly rebalance
    if self.Time.month != self.recent_month and rebalance_flag:
        self.recent_month = self.Time.month

        weight:Dict[str, float] = {}

        if len(aggregated_momentum) >= self.top_equities:
            # sorting
            risk_asset_momentum:Dict[str, float] = {ticker: value for ticker, value in aggregated_momentum.items() if ticker in self.risk_assets}
            cash_asset_momentum:Dict[str, float] = {ticker: value for ticker, value in aggregated_momentum.items() if ticker in self.cash_assets}
            sorted_risk_by_momentum:List[str] = sorted(risk_asset_momentum, key=risk_asset_momentum.get, reverse=True)
            sorted_cash_by_momentum:List[str] = sorted(cash_asset_momentum, key=cash_asset_momentum.get, reverse=True)

            # portfolio consists of the top 5 positive momentum equities
            top_equities:List[str] = [ticker for ticker in sorted_risk_by_momentum][:self.top_equities]
            equities:List[str] = [ticker for ticker in top_equities if risk_asset_momentum[ticker] > 0]

            weight = {x: 1 / self.top_equities for x in equities}
            if len(equities)
