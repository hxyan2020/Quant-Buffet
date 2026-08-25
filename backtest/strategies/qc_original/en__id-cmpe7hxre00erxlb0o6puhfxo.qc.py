# Original QuantConnect / library Python
# locale=en slug="投资因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class InvestmentFactor(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap

    self.long:List[Symbol] = []
    self.short:List[Symbol] = []

    self.quantile:int = 5
    self.leverage:int = 3
    self.rebalance_month:int = 6
    self.min_share_price:float = 1.
    
    self.weight:Dict[Symbol, float] = {}
    
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged

    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0 and x.AdjustedPrice >= self.min_share_price and \
        ((x.SecurityReference.ExchangeId == "NYS") or (x.SecurityReference.ExchangeId == "NAS") or (x.SecurityReference.ExchangeId == "ASE")) and \
        not np.isnan(x.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths) and not np.isnan(x.OperationRatios.TotalAssetsGrowth.OneYear) and \
        x.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths != 0 and x.OperationRatios.TotalAssetsGrowth.OneYear != 0
        ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    # Sorting by investment factor.
    sorted_by_inv_factor:List[Fundamental] = sorted(selected, key = lambda x: (x.OperationRatios.TotalAssetsGrowth.OneYear / x.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths), reverse=True)
    
    if len(sorted_by_inv_factor) >= self.quantile:
        quintile:int = int(len(sorted_by_inv_factor) / self.quantile)
        self.long = [x.Symbol for x in sorted_by_inv_factor[-quintile:]]
        self.short = [x.Symbol for x in sorted_by_inv_factor[:quintile]]
    
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
        
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
