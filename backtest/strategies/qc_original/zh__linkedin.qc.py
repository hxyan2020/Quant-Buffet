# Original QuantConnect / library Python
# locale=zh slug="linkedin员工数据对股票收益的影响"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import CustomFeeModel, SymbolData
# endregion
class TheImpactOfLinkedinDataAboutEmployeesOnStockReturns(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    self.quantile:int = 5
    self.min_share_price:float = 5.
    self.max_missing_days:int = 35
    self.data:Dict[Symbol, SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.BeforeMarketClose(market, 0), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and \
        x.MarketCap != 0 and x.Price >= self.min_share_price
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    curr_date:datetime.date = self.Time.date()
    total_employees_change:Dict[Fundamental, float] = {}
    for stock in selected:
        # The number of employees as indicated on the latest Annual Report, 10-K filing, Form 20-F or equivalent report indicating the employee count at the end of latest fiscal year.
        total_employees:float = stock.CompanyProfile.TotalEmployeeNumber
        if total_employees == 0:
            continue
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData()
        if self.data[symbol].prev_total_employees_ready() and not self.data[symbol].missed_prev_month(curr_date, self.max_missing_days) \
            and total_employees != self.data[symbol].get_prev_total_employees():
            total_employees_change_value:float = self.data[symbol].get_total_employees_change(total_employees)
        
            total_employees_change[stock] = total_employees_change_value
        self.data[symbol].set_prev_total_employees(curr_date, total_employees)
    if len(total_employees_change)  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
