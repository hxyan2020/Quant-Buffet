# Original QuantConnect / library Python
# locale=zh slug="管理层多元化战略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from io import StringIO
from pandas.core.frame import DataFrame
from typing import List, Dict
import pandas as pd
# endregion
class ManagementDiversityStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.leverage: int = 3
    self.selection_month: int = 6
    self.short_allocation: float = -.0
    self.weights: Dict[Symbol, float] = {}
    # source: https://www.fair360.com/top-50-list/2023/
    top_diversity_firms: str = self.Download('data.quantpedia.com/backtesting_data/economic/top50_diversity_firms.csv')
    self.top_diversity_firms_df: DataFrame = pd.read_csv(StringIO(top_diversity_firms), delimiter=';')
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # selection in the beginning of June
    if not self.selection_flag:
        return Universe.Unchanged
    selected: Dict[str, Fundamental] = {
        x.Symbol.Value: x for x in fundamental if x.HasFundamentalData and x.MarketCap != 0
    }
    long: List[Fundamental] = []
    if str(self.Time.year) in list(self.top_diversity_firms_df.columns):
        long = [selected[x] for x in self.top_diversity_firms_df[str(self.Time.year)].values if x in selected]
    else:
        self.Liquidate()
    if len(long) != 0:
        # calculate weights based on values
        self.weights[self.market] = self.short_allocation
        sum_long: float = sum([x.MarketCap for x in long])
        for stock in long:
            self.weights[stock.Symbol] = stock.MarketCap / sum_long
    return list(self.weights.keys())
def OnData(self, data: Slice) -> None:
    # yearly rebalance
    if not self.selection_flag:
        return
    self.selection_flag = False
    targets: List[PortfolioTarget] = [PortfolioTarget(symbol, weight) for symbol, weight in self.weights.items() if symbol in data and data[symbol]]      
    self.SetHoldings(targets, True)
        
    self.weights.clear()
def Selection(self) -> None:
    if self.Time.month == self.selection_month:
        self.selection_flag = True

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
