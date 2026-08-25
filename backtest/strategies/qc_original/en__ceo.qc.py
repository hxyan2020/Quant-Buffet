# Original QuantConnect / library Python
# locale=en slug="做空ceo薪酬过高的公司"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from io import StringIO
from pandas.core.frame import DataFrame
from typing import List, Dict
import pandas as pd
# endregion

class ShortingCompaniesWiththeMostOverpaidCEOs(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.leverage:int = 3
    self.selection_month:int = 3

    self.short:List[Symbol] = []

    # source: https://www.asyousow.org/reports/the-100-most-overpaid-ceos-2022
    overpaid_CEO:str = self.Download('data.quantpedia.com/backtesting_data/economic/overpaid_CEO.csv')
    self.overpaid_CEO_df:DataFrame = pd.read_csv(StringIO(overpaid_CEO), delimiter=';')

    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)
    
def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    # selection on start of March
    if not self.selection_flag:
        return Universe.Unchanged

    selected:List[Symbol] = [x.Symbol for x in coarse if x.HasFundamentalData and x.Market == 'usa']
    
    return selected

def FineSelectionFunction(self, fine:List[FineFundamental]) -> List[Symbol]:
    fine:List[FineFundamental] = [x for x in fine if x.MarketCap != 0 and \
        (x.SecurityReference.ExchangeId == 'NYS')]

    fine:Dict[str, Symbol] = {x.Symbol.Value: x.Symbol for x in fine}

    if str(self.Time.year) in list(self.overpaid_CEO_df.columns):
        self.short = [fine[x] for x in self.overpaid_CEO_df[str(self.Time.year)].values if x in fine]
    else:
        self.Liquidate()

    return self.short

def OnData(self, data: Slice) -> None:
    # yearly rebalance
    if not self.selection_flag:
        return
    self.selection_flag = False

    invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for price_symbol in invested:
        if price_symbol not in self.short + [self.market]:
            self.Liquidate(price_symbol)

    # trade execution
    if len(self.short) != 0:
        if self.market in data and data[self.market]:
            self.SetHoldings(self.market, 1)
    
    for symbol in self.short:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, -1 / len(self.short))
        
    self.short.clear()

def Selection(self) -> None:
    if self.Time.month == self.selection_month:
        self.selection_flag = True

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
