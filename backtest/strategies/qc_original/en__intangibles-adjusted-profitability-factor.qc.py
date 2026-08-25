# Original QuantConnect / library Python
# locale=en slug="intangibles-adjusted-profitability-factor"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# endregion

class IntangiblesAdjustedProfitabilityFactor(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.leverage:int = 3
    self.quantile:int = 3
    self.coarse_count:int = 1000
    self.selection_month:int = 6

    self.long:List[Symbol] = []
    self.short:List[Symbol] = []

    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.market), self.TimeRules.BeforeMarketClose(self.market), self.Selection)
    
def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged

    selected:List[Symbol] = [x.Symbol
        for x in sorted([x for x in coarse if x.HasFundamentalData and x.Market == 'usa'],
            key = lambda x: x.DollarVolume, reverse = True)[:self.coarse_count]]
    # selected = [x.Symbol for x in coarse if x.HasFundamentalData and x.Market == 'usa']

    return selected

def FineSelectionFunction(self, fine:List[FineFundamental]) -> List[Symbol]:
    fine = [x for x in fine if x.MarketCap != 0 and \
            (x.SecurityReference.ExchangeId == 'NYS') or (x.SecurityReference.ExchangeId == 'NAS') or (x.SecurityReference.ExchangeId == 'ASE')]

    # if len(fine) > self.coarse_count:
    #     fine = sorted(fine, key=lambda x: x.MarketCap, reverse=True)[:self.coarse_count]

    # profitability calculation
    profitability:Dict[Symbol, float] = {
        stock.Symbol : stock.FinancialStatements.IncomeStatement.GrossProfit.TwelveMonths - stock.FinancialStatements.IncomeStatement.InterestExpense.TwelveMonths - stock.FinancialStatements.IncomeStatement.GeneralAndAdministrativeExpense.TwelveMonths \
        for stock in fine
    }
    
    # sort and divide into quantiles
    if len(profitability) >= self.quantile:
        sorted_roe:List[Symbol] = sorted(profitability, key=profitability.get, reverse=True)
        quantile:int = len(sorted_roe) // self.quantile
        self.long = sorted_roe[:quantile]
        self.short = sorted_roe[-quantile:]
        self.rebalance_flag = True

    return self.long + self.short

def OnData(self, data: Slice):
    # yearly rebalance
    if not self.selection_flag:
        return
    self.selection_flag = False

    invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in self.long + self.short:
            self.Liquidate(symbol)
    
    # trade execution
    for symbol in self.long:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, 1/len(self.long))
    
    for symbol in self.short:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, -1/len(self.long))

def Selection(self) -> None:
    # selection on end of June
    if self.Time.month != self.selection_month:
        return
    self.selection_flag = True

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
