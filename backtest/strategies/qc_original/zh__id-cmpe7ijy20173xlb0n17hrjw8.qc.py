# Original QuantConnect / library Python
# locale=zh slug="基于现金的运营盈利能力"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from functools import reduce
from numpy import isnan
class CashBasedOperatingProﬁtability(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100000)
    
    self.weight:Dict[Symbol, float] = {}
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.rebalance_month:int = 12
    self.quantile:int = 10
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.financial_statement_names:List[str] = [
        'FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths',
        'FinancialStatements.IncomeStatement.SellingAndMarketingExpense.TwelveMonths',
        'FinancialStatements.IncomeStatement.CostOfRevenue.TwelveMonths',
        'FinancialStatements.IncomeStatement.GeneralAndAdministrativeExpense.TwelveMonths',
    ]
    self.month:int = -1
    self.rebalance_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.AddUniverse(self.FundamentalSelectionFunction)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
            
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if self.month == self.Time.month:
        return Universe.Unchanged
    else:
        self.month = self.Time.month
        if self.Time.month != self.rebalance_month:
            return Universe.Unchanged
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price >= self.min_share_price and x.Market == 'usa' and \
        all((not isnan(self.rgetattr(x, statement_name)) and self.rgetattr(x, statement_name) != 0) for statement_name in self.financial_statement_names)
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    # CBOP calculation
    cbop:Dict[Fundamental, float] = { stock : (stock.FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths - stock.FinancialStatements.IncomeStatement.SellingAndMarketingExpense.TwelveMonths -
                stock.FinancialStatements.IncomeStatement.CostOfRevenue.TwelveMonths - stock.FinancialStatements.IncomeStatement.GeneralAndAdministrativeExpense.TwelveMonths)
                for stock in selected}
    
    # Sorting by market cap and cbop.
    if len(cbop) >= self.quantile * 2:
        top_market_cap:List = sorted(cbop.items(), key = lambda x: x[0].MarketCap, reverse=True)[:int(len(cbop) / 2)]
        sorted_by_cbop:List = sorted(top_market_cap, key = lambda x:x[1], reverse=True)
        quantile:int = int(len(sorted_by_cbop) / self.quantile)
        long:List[Fundamental] =  [x[0] for x in sorted_by_cbop[:quantile]]
        short:List[Fundamental] = [x[0] for x in sorted_by_cbop[-quantile:]]
            
        # Market cap weighting.
        for i, portfolio in enumerate([long, short]):
            mc_sum:float = sum(map(lambda x: x.MarketCap, portfolio))
            for stock in portfolio:
                self.weight[stock.Symbol] = ((-1) ** i) * stock.MarketCap / mc_sum
    
    self.rebalance_flag = True
    return list(self.weight.keys())
    
def OnData(self, data: Slice) -> None:
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    
    # Trade execution.
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
# https://gist.github.com/wonderbeyond/d293e7a2af1de4873f2d757edd580288
def rgetattr(self, obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
