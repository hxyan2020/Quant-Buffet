# Original QuantConnect / library Python
# locale=en slug="现金持有效应与净经营资产策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# endregion

class CashHoldingsEffectAndNetOperatingAssets(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    self.cash_holdings_quantile:int = 5
    self.net_operating_assets_quantile:int = 2
    self.three_months_flag:bool = True
    
    self.weights:Dict[Symbol, float] = {}

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.coarse_count:int = 3000
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)

    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.        
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.BeforeMarketClose(self.market, 0), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    fundamental = [x for x in fundamental if not np.isnan(x.FinancialStatements.BalanceSheet.Cash.ThreeMonths) and x.FinancialStatements.BalanceSheet.Cash.ThreeMonths != 0 and \
        not np.isnan(x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths) and x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths != 0 and \
        not np.isnan(x.FinancialStatements.BalanceSheet.FinancialAssets.ThreeMonths) and x.FinancialStatements.BalanceSheet.FinancialAssets.ThreeMonths != 0 and \
        not np.isnan(x.FinancialStatements.BalanceSheet.TotalLiabilitiesAsReported.ThreeMonths) and x.FinancialStatements.BalanceSheet.TotalLiabilitiesAsReported.ThreeMonths != 0
        ]

    if self.coarse_count = 5]))[-self.coarse_count:]

    cash_holdings:Dict[Symbol, float] = {}
    net_operating_assets:Dict[Symbol, float] = {}

    for stock in selected:
        symbol:Symbol = stock.Symbol

        cash:float = stock.FinancialStatements.BalanceSheet.Cash.ThreeMonths if self.three_months_flag \
            else stock.FinancialStatements.BalanceSheet.Cash.TwelveMonths
        total_assets:float = stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths if self.three_months_flag \
            else stock.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths
        financial_assets:float = stock.FinancialStatements.BalanceSheet.FinancialAssets.ThreeMonths if self.three_months_flag \
            else stock.FinancialStatements.BalanceSheet.FinancialAssets.TwelveMonths
        total_liabilities:float = stock.FinancialStatements.BalanceSheet.TotalLiabilitiesAsReported.ThreeMonths if self.three_months_flag \
            else stock.FinancialStatements.BalanceSheet.TotalLiabilitiesAsReported.TwelveMonths

        if all([cash, total_assets, financial_assets, total_liabilities]):
            cash_holdings_value:float = cash / total_assets
            cash_holdings[symbol] = cash_holdings_value

            operating_assets:float = total_assets - financial_assets
            net_operating_assets_value:float = (operating_assets - total_liabilities) / total_assets
            net_operating_assets[symbol] = net_operating_assets_value

    if len(cash_holdings)  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in self.weights:
            self.Liquidate(symbol)
            
    for symbol, w in self.weights.items():
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, w)
            
    self.weights.clear()
    
def Selection(self) -> None:
    self.selection_flag = True

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
