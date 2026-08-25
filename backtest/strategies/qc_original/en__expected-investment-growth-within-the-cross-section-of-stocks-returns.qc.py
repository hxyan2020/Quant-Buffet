# Original QuantConnect / library Python
# locale=en slug="expected-investment-growth-within-the-cross-section-of-stocks-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from collections import deque
from AlgorithmImports import *
import numpy as np
import statsmodels.api as sm
from numpy import isnan
from typing import Dict, List, Deque, Tuple
class ExpectedInvestmentGrowthwithintheCrosssectionofStocksReturns(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2005, 1, 1)  
    self.SetCash(100000)
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    # Monthly close data.
    self.data:Dict[Symbol, RollingWindow[float]] = {}
    self.period:int = 13
    self.leverage:int = 5
    self.rebalance_month:int = 12
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    # Regression data.
    self.regression_flag:bool = False
    self.regression_data:Dict[Symbol, Deque[Tuple[float, float, float, float]]] = {}
    self.regression_coefficients:Dict[Symbol, float] = {}
    self.regression_min_period:int = 5  # years
    
    # Last year's capital stock and CAPX data.
    self.last_year_data:Dict[Symbol, Tuple[float, float]] = {}
    
    self.fundamental_count:int = 1000
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
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
    # Update the rolling window every month.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].Add(stock.AdjustedPrice)

    selected:Dict[Symbol, Fundamental] = {x.Symbol: x
        for x in sorted([x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' \
            and (not isnan(x.FinancialStatements.CashFlowStatement.CapitalExpenditure.ThreeMonths) and x.FinancialStatements.CashFlowStatement.CapitalExpenditure.ThreeMonths != 0 and
                not isnan(x.FinancialStatements.BalanceSheet.TotalCapitalization.ThreeMonths) and x.FinancialStatements.BalanceSheet.TotalCapitalization.ThreeMonths != 0 and
                not isnan(x.FinancialStatements.BalanceSheet.Inventory.ThreeMonths) and x.FinancialStatements.BalanceSheet.Inventory.ThreeMonths != 0 and
                not isnan(x.FinancialStatements.BalanceSheet.CurrentDeferredTaxesLiabilities.ThreeMonths) and x.FinancialStatements.BalanceSheet.CurrentDeferredTaxesLiabilities.ThreeMonths != 0 and
                not isnan(x.FinancialStatements.BalanceSheet.CapitalStock.ThreeMonths) and x.FinancialStatements.BalanceSheet.CapitalStock.ThreeMonths != 0 and
                not isnan(x.FinancialStatements.IncomeStatement.PretaxIncome.ThreeMonths) and x.FinancialStatements.IncomeStatement.PretaxIncome.ThreeMonths != 0 and
                not isnan(x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.ThreeMonths) and x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.ThreeMonths != 0 and 
                not isnan(x.FinancialStatements.BalanceSheet.PreferredStock.ThreeMonths) and x.FinancialStatements.BalanceSheet.PreferredStock.ThreeMonths != 0
                )],
            key = lambda x: x.DollarVolume, reverse = True)[:self.fundamental_count]}
    
    predicted_eig:Dict[Symbol, float] = {}
    # Warmup price rolling windows.
    for stock in list(selected.values()):
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            if symbol not in self.regression_data:
                self.regression_data[symbol] = deque()
            
            self.data[symbol] = RollingWindow[float](self.period)
            history:DataFrame = self.History(symbol, self.period * 30, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes:Series = history.loc[symbol].close
            
            closes_len:int = len(closes.keys())
            # Find monthly closes.
            for index, time_close in enumerate(closes.items()):
                # index out of bounds check.
                if index + 1 = self.regression_min_period:
                    # Regression coefficients calc.
                    eigs:List[float] = [float(x[0]) for x in self.regression_data[symbol]]
                    momentums:List[float] = [float(x[1]) for x in self.regression_data[symbol]]
                    qs:List[float] = [float(x[2]) for x in self.regression_data[symbol]]
                    cfs:List[float] = [float(x[3]) for x in self.regression_data[symbol]]
    
                    x:List[float] = [momentums[:-1], qs[:-1], cfs[:-1]]
                    regression_model = self.MultipleLinearRegression(x, eigs[1:])
                    self.regression_coefficients[symbol] = regression_model.params
            if symbol not in self.last_year_data:
                self.last_year_data[symbol] = None
            self.last_year_data[symbol] = (capital_stock_t, capx_t)
        
        if symbol in self.regression_coefficients:
            alpha:float = self.regression_coefficients[symbol][0]
            betas:np.ndarray = np.array(self.regression_coefficients[symbol][1:])
            prediction_x:List[float] = [momentum, q, cf]
            if len(prediction_x) == len(betas):
                predicted_eig[symbol] = alpha + sum(np.multiply(betas, prediction_x))
    
    if self.regression_flag:
        self.regression_flag = False
    
    if len(predicted_eig) != 0:
        eig_values:List[float] = [x[1] for x in predicted_eig.items()]
        top_decile:float = np.percentile(eig_values, 90)
        bottom_decile:float = np.percentile(eig_values, 10)
        self.long:List[Symbol] = [x[0] for x in predicted_eig.items() if x[1] > top_decile]
        self.short:List[Symbol] = [x[0] for x in predicted_eig.items() if x[1]  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
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
        self.regression_flag = True    
    self.selection_flag = True

def MultipleLinearRegression(self, x:List[float], y:List[float]):
    x:np.ndarray = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
