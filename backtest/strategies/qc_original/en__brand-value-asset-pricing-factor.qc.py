# Original QuantConnect / library Python
# locale=en slug="brand-value-asset-pricing-factor"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import pandas as pd
from io import StringIO
#endregion
class InsiderTradingCombinedwithShareRepurchases(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.long: List[Symbol] = []
    self.brands_by_year_n: Dict[int, List[str]] = {}
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # Data source: https://interbrand.com/best-global-brands/
    csv_string_file = self.Download(f'data.quantpedia.com/backtesting_data/economic/brand_value_fifteen_lowest.csv')
    # take values of each column, expect first one in each row and does not take first row as a header
    separated_file = pd.read_csv(StringIO(csv_string_file), sep=';', header=None)
    
    for row in separated_file.itertuples():
        brand_tickers = []
        for ticker in row[2:]:
            brand_tickers.append(ticker)
        self.brands_by_year_n[int(row[1])] = brand_tickers
    self.selection_flag: boll = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    year_key: int = self.Time.year - 1
    if year_key in self.brands_by_year_n:
        self.long = [f.Symbol for f in fundamental if f.Symbol.Value in self.brands_by_year_n[year_key]]
    return self.long
def OnData(self, slice: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # rebalance
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, 1. / len(self.long)) for symbol in self.long if symbol in slice and slice[symbol]]
    self.SetHoldings(portfolio, True)
    self.long.clear()
        
def Selection(self) -> None:
    self.selection_flag = True
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
