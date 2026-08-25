# Original QuantConnect / library Python
# locale=zh slug="信用违约掉期（cds）期限结构预测股票收益"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import List, Dict
#endregion
class CombinedStockandCDSMomentum(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2003, 1, 1)
    self.SetCash(100_000)
    self.UniverseSettings.Leverage = 5
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0
    self.settings.daily_precise_end_time = False
    
    self.quantile: int = 10
    self.selection_flag: bool = False
    self.tickers: List[str] = []
    self.long_symbols: List[Symbol] = []
    self.short_symbols: List[Symbol] = []
    self.cds_1y: Symbol = self.AddData(data_tools.EquityCDS1Y, 'CDS1Y', Resolution.Daily).Symbol
    self.cds_5y: Symbol = self.AddData(data_tools.EquityCDS5Y, 'CDS5Y', Resolution.Daily).Symbol
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthStart(market), 
                    self.TimeRules.AfterMarketOpen(market), 
                    self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    slope: Dict[Symbol, int] = {}
    
    # calculate slope of the CDS term structure
    if self.Securities.ContainsKey(self.cds_1y) and self.Securities.ContainsKey(self.cds_5y):
        cds_1y_data = self.Securities[self.cds_1y].GetLastData()
        cds_5y_data = self.Securities[self.cds_5y].GetLastData()
        
        if cds_1y_data and cds_5y_data:
            # data has not been initialized yet
            if len(self.tickers) == 0:
                self.tickers = list([x.upper() for x in cds_1y_data.GetStorageDictionary().Keys])
            
            if self.selection_flag:
                for f in fundamental:
                    symbol: Symbol = f.Symbol
                    ticker: str = symbol.Value
    
                    # calculate slope
                    if ticker in self.tickers:
                        cds_1y: int = cds_1y_data[ticker]
                        cds_5y: int = cds_5y_data[ticker]
                        slope[symbol] = cds_5y - cds_1y
    
    if not self.selection_flag:
        return Universe.Unchanged
    
    last_update_date_1y: datetime.date = data_tools.EquityCDS1Y.get_last_update_date()
    last_update_date_5y: datetime.date = data_tools.EquityCDS5Y.get_last_update_date()
    if (self.Securities[self.cds_1y].GetLastData() and last_update_date_1y = self.quantile:
        sorted_by_slope: List[Symbol] = sorted(slope, key=slope.get, reverse=True)
        quantile: int = int(len(sorted_by_slope) / self.quantile)
        self.long_symbols = sorted_by_slope[-quantile:]
        self.short_symbols = sorted_by_slope[:quantile]
    return self.long_symbols + self.short_symbols

def OnData(self, slice: Slice) -> None:
    if not self.selection_flag: 
        return
    self.selection_flag = False
    
    # trade execution
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long_symbols, self.short_symbols]):
        for symbol in portfolio:
            if slice.ContainsKey(symbol) and slice[symbol] is not None:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    self.SetHoldings(targets, True)
    self.long_symbols.clear()
    self.short_symbols.clear()
def Selection(self) -> None:
    self.selection_flag = True
