# Original QuantConnect / library Python
# locale=en slug="员工满意度因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion

class EmployeeSatisfactionFactor(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    
    self.tickers_by_year: Dict[int, List[str]] = {}
    
    # download companies employees satisfaction ratings for each year
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/index/employee_satisfaction_top_100.csv')
    lines: List[str] = csv_string_file.split('\r\n')
    
    for line in lines:
        line_split: List[str] = line.split(';')
        date: datetime.date = datetime.strptime(line_split[0], "%d.%m.%Y").date()
        year: int = date.year
        
        # store list of tickers by year
        self.tickers_by_year[date.year] = line_split[1:]
    
    self.leverage: int = 5

    self.current_year: int = -1
    self.selection_flag: bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    
    self.long: List[Symbol] = []
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.BeforeMarketClose(market), self.Selection)

def Selection(self) -> None:
    # beginning of February rebalance
    if self.Time.month == 2:
        self.selection_flag = True
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    self.current_year = self.Time.year
    
    # rebalance yearly
    if not self.selection_flag or self.current_year - 1 not in self.tickers_by_year:
        return Universe.Unchanged
        
    current_top_companies: List[str] = self.tickers_by_year[self.current_year - 1]
    
    # filter stock symbols from top companies in previous year
    self.long = [x.Symbol for x in fundamental if x.Symbol.Value in current_top_companies]
    
    return self.long

def OnData(self, slice) -> None:
    # rebalance yearly
    if self.selection_flag == False:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, 1. / len(self.long)) for symbol in self.long if symbol in slice and slice[symbol]]
    self.SetHoldings(portfolio, True)

    self.long.clear()

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
