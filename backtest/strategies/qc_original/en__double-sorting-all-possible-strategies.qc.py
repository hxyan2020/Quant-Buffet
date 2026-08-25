# Original QuantConnect / library Python
# locale=en slug="double-sorting-all-possible-strategies"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
from pandas.core.frame import DataFrame
import data_tools
# endregion
class DoubleSortingAllPossibleStrategies(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.period: int = 12
    self.quantile: int = 10
    self.leverage: int = 5
    self.data: Dict[str, data_tools.SymbolData] = {}
    text: str = self.Download('data.quantpedia.com/backtesting_data/equity/quantpedia_strategies/525_related/anomaly_pairs.csv')
    self.strategies = text.split('\r\n') 
    for strategy in self.strategies:
        data: Security = self.AddData(data_tools.QuantpediaEquity, strategy, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        self.data[strategy] = data_tools.SymbolData()
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.recent_month:int = -1

def OnData(self, data: Slice) -> None:
    # monthly rebalance
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    
    # check if custom data is still coming
    _last_update_date: Dict[str, datetime.date] = data_tools.QuantpediaEquity.get_last_update_date()
    strategies_to_trade: List[str] = [
        strategy for strategy in self.strategies 
        if strategy in _last_update_date
        and self.Time.date()
