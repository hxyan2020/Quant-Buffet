# Original QuantConnect / library Python
# locale=en slug="英国股票盈利能力预测"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import statsmodels.api as sm
from collections import deque
from numpy import isnan
# endregion

class ExpectedprofitabilityinUKStocks(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.regression_period:float = 5 * 4 # need n years of quarterly data
    self.regression_data:Dict = {}
    self.weights:Dict = {}

    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.quantile:int = 5
    self.min_share_price:int = 3
    self.leverage:int = 10

    self.months_counter:int = 0
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.AdjustedPrice > self.min_share_price and x.CompanyReference.BusinessCountryID == 'GBR' and x.MarketCap != 0 and 
                                    not isnan(x.OperationRatios.ROA.ThreeMonths) and x.OperationRatios.ROA.ThreeMonths != 0 and
                                    not isnan(x.EarningReports.BasicEPS.ThreeMonths) and x.EarningReports.BasicEPS.ThreeMonths != 0 and
                                    not isnan(x.FinancialStatements.BalanceSheet.TotalLiabilitiesAsReported.ThreeMonths) and x.FinancialStatements.BalanceSheet.TotalLiabilitiesAsReported.ThreeMonths != 0 and
                                    not isnan(x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths) and x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths != 0 and
                                    not isnan(x.FinancialStatements.BalanceSheet.TangibleBookValue.ThreeMonths) and x.FinancialStatements.BalanceSheet.TangibleBookValue.ThreeMonths != 0

                                    # NOTE not used
                                    # NOTE these could be potentially equal to 0
                                    # not isnan(x.FinancialStatements.IncomeStatement.TotalDividendPaymentofEquityShares.ThreeMonths) and
                                    # not isnan(x.FinancialStatements.CashFlowStatement.ChangeinFinancialAssets.TwelveMonths)
                                    ]

    # make sure regression data are consecutive
    if self.regression_data:
        symbols_to_remove:set = set(list(self.regression_data.keys())) - set([x.Symbol for x in selected])
        for symbol in symbols_to_remove:
            del self.regression_data[symbol]

    EROA:Dict[Symbol, float] = {}
    for stock in selected:
        symbol:Symbol = stock.Symbol
        ROA:float = stock.OperationRatios.ROA.ThreeMonths

        if symbol not in self.regression_data:
            # self.regression_data[symbol] = SymbolData(ROA)
            self.regression_data[symbol] = deque(maxlen=self.regression_period)
        
        TA:float = stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths
        NEG:float = 1 if stock.EarningReports.BasicEPS.ThreeMonths  skip first value in current_x since it's y value for ROA
            adjusted_current_x:List = [x for i, x in enumerate(current_x[1:]) if i not in x_variable_skip_indices]
            predicted_value:float = regression_model.predict(exog=[1] + adjusted_current_x)  # intercept + x
            EROA[stock] = predicted_value[0]

    if len(EROA) >= self.quantile:
        # perform selection
        sorted_by_EROA:List = sorted(EROA.items(), key = lambda x:x[1], reverse=True)
        quantile:int = int(len(sorted_by_EROA) / self.quantile)
        long:List = [x[0] for x in sorted_by_EROA[:quantile]]
        short:List = [x[0] for x in sorted_by_EROA[-quantile:]]

        # value weighting
        total_mc_long:int = sum([x.MarketCap for x in long])
        total_mc_short:int = sum([x.MarketCap for x in short])
        
        for stock in long:
            self.weights[stock.Symbol] = stock.MarketCap / total_mc_long
        for stock in short:
            self.weights[stock.Symbol] = -stock.MarketCap / total_mc_short

    return list(self.weights.keys())
    
def OnData(self, data: Slice) -> None:
    # rebalance quarterly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in self.weights:
            self.Liquidate(symbol)
            
    for symbol, w in self.weights.items():
        self.SetHoldings(symbol, w)
            
    self.weights.clear()

def MultipleLinearRegression(self, x:List, y:List):
    x = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
    
def Selection(self) -> None:
    # rebalance quarterly
    if self.months_counter % 3 == 0:
        self.selection_flag = True
    self.months_counter += 1

# Custom fee model
class CustomFeeModel():
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
