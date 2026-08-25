# Original QuantConnect / library Python
# locale=en slug="非盈利公司中的价值效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# endregion

class ValueEffectInUnprofitableFirms(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    self.quantile:int = 5

    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.weight:Dict[Symbol, float] = {}

    self.fundamental_count:int = 1000
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.BeforeMarketClose(market, 0), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = sorted([x for x in fundamental if x.HasFundamentalData and x.MarketCap and \
        ((x.SecurityReference.ExchangeId == "NYS") or (x.SecurityReference.ExchangeId == "NAS") or (x.SecurityReference.ExchangeId == "ASE")) and \
        x.FinancialStatements.IncomeStatement.TotalRevenue.ThreeMonths != 0
        and not np.isnan(x.FinancialStatements.IncomeStatement.TotalRevenue.ThreeMonths)], 
        key = lambda x: x.DollarVolume)[-self.fundamental_count:]

    revenue_price_ratio:Dict[Fundamental, float] = { stock : (stock.FinancialStatements.IncomeStatement.TotalRevenue.ThreeMonths / stock.AdjustedPrice) \
        for stock in selected }

    if len(revenue_price_ratio)  None:
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)

    self.weight.clear()

def Selection(self) -> None:
    self.selection_flag = True

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
