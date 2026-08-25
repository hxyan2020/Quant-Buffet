# Original QuantConnect / library Python
# locale=en slug="accrual-effect-in-family-firms"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List
from data_tools import SymbolData, CustomFeeModel
# endregion

class AccrualEffectInFamilyFirms(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    self.quantile:int = 5

    self.max_missing_days:int = 356 + 10

    self.data:Dict[Symbol, SymbolData] = {}
    self.weights:Dict[Symbol, float] = {}

    family_businesses_csv:str = self.Download('data.quantpedia.com/backtesting_data/economic/family_businesses_tickers.csv').replace('\r\n', '')
    self.tickers:List[str] = family_businesses_csv.split(';')

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.selection_month:int = 6
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    
    self.Schedule.On(self.DateRules.MonthEnd(self.market), self.TimeRules.BeforeMarketClose(self.market, 0), self.Selection)

def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected_symbols:List[CoarseFundamental] = [x.Symbol for x in coarse if x.Symbol.Value in self.tickers]

    return selected_symbols

def FineSelectionFunction(self, fine:List[FineFundamental]) -> List[Symbol]:
    curr_date:datetime.date = self.Time.date()
    total_accurals:Dict[Symbol, float] = {}

    for stock in fine:
        if stock.FinancialStatements.BalanceSheet.CurrentAssets.TwelveMonths != 0 and \
            stock.FinancialStatements.BalanceSheet.CurrentLiabilities.TwelveMonths != 0 and \
            stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths != 0:

            symbol:Symbol = stock.Symbol

            operating_assets:float = stock.FinancialStatements.BalanceSheet.CurrentAssets.TwelveMonths
            operating_liabilities:float = stock.FinancialStatements.BalanceSheet.CurrentLiabilities.TwelveMonths

            net_operating_assets:float = operating_assets - operating_liabilities

            if symbol not in self.data:
                self.data[symbol] = SymbolData()

            if not self.data[symbol].net_operating_assets_data_coming(curr_date, self.max_missing_days):
                self.data[symbol].reset()

            if self.data[symbol].net_operating_assets_ready():
                total_assets:float = stock.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths
                net_operating_assets_change:float = self.data[symbol].get_net_operating_assets_change(net_operating_assets)
                total_accurals_value:float = net_operating_assets_change / total_assets

                total_accurals[symbol] = total_accurals_value

            self.data[symbol].set_net_operating_assets(curr_date, net_operating_assets)

    # make sure there are enough stocks for selection
    if len(total_accurals)  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in self.weights:
            self.Liquidate(symbol)
            
    for symbol, w in self.weights.items():
        self.SetHoldings(symbol, w)
            
    self.weights.clear()
    
def Selection(self):
    if self.selection_month == self.Time.month:
        self.selection_flag = True
