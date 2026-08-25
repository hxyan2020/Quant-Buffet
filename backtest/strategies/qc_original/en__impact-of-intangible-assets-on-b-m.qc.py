# Original QuantConnect / library Python
# locale=en slug="impact-of-intangible-assets-on-b-m"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from functools import reduce
from numpy import isnan
class ImpactOfIntangibleAssetsOnBM(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # value weighted stocks
    self.weight:Dict[Symbol, float] = {}
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.financial_statement_names:List[str] = [
        'FinancialStatements.IncomeStatement.ResearchAndDevelopment.ThreeMonths',
        'FinancialStatements.IncomeStatement.SellingGeneralAndAdministration.ThreeMonths',
        'ValuationRatios.BookValuePerShare',
        'EarningReports.BasicAverageShares.ThreeMonths',
        'FinancialStatements.BalanceSheet.Goodwill.ThreeMonths',
        'MarketCap',
    ]
    self.quantile:int = 10
    self.leverage:int = 5
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.last_year = -1
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
				
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchange_codes and \
        all((not isnan(self.rgetattr(x, statement_name)) and self.rgetattr(x, statement_name) != 0) for statement_name in self.financial_statement_names)]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    iBE:Dict[Fundamental, float] = {}
    for stock in selected:
        Kcap:float = stock.FinancialStatements.IncomeStatement.ResearchAndDevelopment.ThreeMonths
        Ocap:float = stock.FinancialStatements.IncomeStatement.SellingGeneralAndAdministration.ThreeMonths
        # BE might be changed
        BE:float = stock.ValuationRatios.BookValuePerShare * stock.EarningReports.BasicAverageShares.ThreeMonths
        GoodWill:float = stock.FinancialStatements.BalanceSheet.Goodwill.ThreeMonths
        
        iBE[stock] = Kcap + Ocap + BE - GoodWill
    
    if len(iBE) >= self.quantile:
        sorted_by_iBE:List[Fundamental] = [x for x in sorted(iBE, key = iBE.get, reverse = True)]
        quantile:int = int(len(sorted_by_iBE) / self.quantile)
        # Long the top decile, short the bottom decile
        long:List[Fundamental] = sorted_by_iBE[:quantile]
        short:List[Fundamental] = sorted_by_iBE[-quantile:]
        
        # calculate weights
        for i, portfolio in enumerate([long, short]):
            mc_sum:float = sum(map(lambda x: x.MarketCap, portfolio))
            for stock in portfolio:
                self.weight[stock.Symbol] = ((-1) ** i) * stock.MarketCap / mc_sum
    return list(self.weight.keys())
    
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
                    
def Selection(self) -> None:
    if self.last_year != self.Time.year:
        self.last_year = self.Time.year
        self.selection_flag = True
# https://gist.github.com/wonderbeyond/d293e7a2af1de4873f2d757edd580288
def rgetattr(self, obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))
    
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
