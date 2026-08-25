# Original QuantConnect / library Python
# locale=en slug="stock-issuance-effect"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from numpy import isnan
from functools import reduce
class StockIssuanceEffect(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.data:Dict[Symbol, SymbolData] = {}  # symbol data
    self.period:int = 3 # years
    self.rebalance_month:int = 5
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.financial_statement_names:List[str] = [
        'MarketCap',
        'FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths',
        'EarningReports.BasicAverageShares.TwelveMonths',
        'FinancialStatements.IncomeStatement.CostOfRevenue.TwelveMonths',
        'FinancialStatements.IncomeStatement.SellingGeneralAndAdministration.TwelveMonths',
        'FinancialStatements.IncomeStatement.InterestExpense.TwelveMonths',
    ]
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.BeforeMarketClose(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchange_codes and \
        all(not isnan(self.rgetattr(x, statement_name)) for statement_name in self.financial_statement_names) and x.Price >= self.min_share_price and \
        x.ValuationRatios.BookValuePerShare  self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
    
        self.data[symbol].update(stock.EarningReports.BasicAverageShares.TwelveMonths)
        if self.data[symbol].is_ready():
            # long the non-issuers and short the > 5% issuers
            if not self.data[symbol].is_issuer():
                self.long.append(stock.Symbol)
            else:
                self.short.append(stock.Symbol)
    return self.long + self.short
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # order execution
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()

def Selection(self) -> None:
    if self.Time.month == self.rebalance_month:
        self.selection_flag = True
# https://gist.github.com/wonderbeyond/d293e7a2af1de4873f2d757edd580288
def rgetattr(self, obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))
class SymbolData():
def __init__(self, period:int) -> None:
    self._period:int = period
    self._shares_outstanding:RollingWindow = RollingWindow[float](period)
    
def update(self, value:float) -> None:
    self._shares_outstanding.Add(value)

def is_ready(self) -> bool:
    return self._shares_outstanding.IsReady
def is_non_issuer(self) -> bool:
    return (self._shares_outstanding[1] / self._shares_outstanding[2] - 1)  bool:
    return (self._shares_outstanding[1] / self._shares_outstanding[2] - 1) >= 0.05

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
