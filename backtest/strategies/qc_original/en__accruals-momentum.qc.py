# Original QuantConnect / library Python
# locale=en slug="accruals-momentum"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from collections import deque
import numpy as np
import statsmodels.api as sm
from typing import List, Dict, Deque, Tuple
from numpy import isnan
class AccrualsMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']	
    # Latest accruals data.
    self.accruals_data:Dict[Symbol, StockData] = {}
    self.min_share_price:int = 5
    self.period:int = 5
    self.leverage:int = 15
    self.quantile:int = 4
    
    # Accruals value for last year.
    self.latest_accruals:Dict[Symbol, StockData] = {}
    
    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    self.consecutive_period:int = 4
    self.low_residual_portfolios:Deque = deque(maxlen = self.consecutive_period)
    self.high_residual_portfolios:Deque = deque(maxlen = self.consecutive_period)
    
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.regression_period:int = 5
    self.regression_data:Dict[Symbol, Tuple[float]] = {}
    
    self.months:int = 12
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        symbol = security.Symbol
        
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
        self.regression_data[symbol] = deque(maxlen = self.regression_period)
            
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price >= self.min_share_price \
        and not isnan(x.FinancialStatements.BalanceSheet.CurrentAssets.Value) and x.FinancialStatements.BalanceSheet.CurrentAssets.Value > 0 \
        and not isnan(x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value) and x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value > 0 \
        and not isnan(x.FinancialStatements.BalanceSheet.CurrentLiabilities.Value) and x.FinancialStatements.BalanceSheet.CurrentLiabilities.Value > 0 \
        and not isnan(x.FinancialStatements.BalanceSheet.CurrentDebt.Value) and x.FinancialStatements.BalanceSheet.CurrentDebt.Value > 0 \
        and not isnan(x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.Value) and x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.Value > 0 \
        and not isnan(x.FinancialStatements.BalanceSheet.GrossPPE.Value) and x.FinancialStatements.BalanceSheet.GrossPPE.Value > 0 \
        and not isnan(x.FinancialStatements.IncomeStatement.TotalRevenueAsReported.Value) and x.FinancialStatements.IncomeStatement.TotalRevenueAsReported.Value > 0 \
        and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    updated:List[Symbol] = []
    residual:Dict[Symbol, float] = {}
    
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.accruals_data:
            # Data for previous year.
            self.accruals_data[symbol] = None
            
        if symbol not in self.latest_accruals:
            # Previous year's accruals.
            self.latest_accruals[symbol] = None
                    
        # Accrual calc.
        current_accruals_data:StockData = StockData(stock.FinancialStatements.BalanceSheet.CurrentAssets.Value, stock.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value,
                                            stock.FinancialStatements.BalanceSheet.CurrentLiabilities.Value, stock.FinancialStatements.BalanceSheet.CurrentDebt.Value, stock.FinancialStatements.BalanceSheet.IncomeTaxPayable.Value,
                                            stock.FinancialStatements.IncomeStatement.DepreciationAndAmortization.Value, stock.FinancialStatements.BalanceSheet.TotalAssets.Value,
                                            stock.FinancialStatements.IncomeStatement.TotalRevenueAsReported.Value)
        
        # There is not previous accruals data.
        if not self.accruals_data[symbol]:
            self.accruals_data[symbol] = current_accruals_data
            updated.append(symbol)
            continue
            
        current_accruals:float = self.CalculateAccruals(current_accruals_data, self.accruals_data[symbol])
        delta_sales:float = (current_accruals_data.Sales - self.accruals_data[symbol].Sales) / self.accruals_data[symbol].TotalAssets
        ppe:float = stock.FinancialStatements.BalanceSheet.GrossPPE.Value / self.accruals_data[symbol].TotalAssets
        # There is not previous accruals value.
        if not self.latest_accruals[symbol]:
            self.latest_accruals[symbol] = current_accruals
            updated.append(symbol)
            continue                
        
        # Regression data.
        accruals_factor:float = 1 / self.latest_accruals[symbol]
        reg_data:Tuple[float] = (current_accruals, accruals_factor, delta_sales, ppe)
        
        if symbol not in self.regression_data:
            self.regression_data[symbol] = deque(maxlen = self.regression_period)
        self.regression_data[symbol].append(reg_data)
        
        if len(self.regression_data[symbol]) == self.regression_data[symbol].maxlen:
            total_accruals:List[float] = [x[0] for x in self.regression_data[symbol]]
            accruals_factors:List[float] = [x[1] for x in self.regression_data[symbol]]
            sales_deltas:List[float] = [x[2] for x in self.regression_data[symbol]]
            ppes:List[float] = [x[3] for x in self.regression_data[symbol]]
            # Regression.
            x:List[List[float]] = [accruals_factors, sales_deltas, ppes]
            regression_model = MultipleLinearRegression(x, total_accruals)
            # x = [accruals_factors[:-1], sales_deltas[:-1], ppes[:-1]]
            # regression_model = MultipleLinearRegression(x, total_accruals[1:])
            alpha:float = regression_model.params[0]
            residual[symbol] = alpha
            
        # Update accruals data and value.
        self.accruals_data[symbol] = current_accruals_data
        self.latest_accruals[symbol] = current_accruals
        updated.append(symbol)
    
    # Make sure we ahve consecutive accruals data. 
    symbols_to_remove:List[Symbol] = []
    for symbol in self.accruals_data:
        if symbol not in updated:
            symbols_to_remove.append(symbol)
    for symbol in symbols_to_remove:
        del self.accruals_data[symbol]
        del self.latest_accruals[symbol]
    
    sorted_by_residual:List[Tuple[Symbol, float]] = sorted(residual.items(), key = lambda x : x[1], reverse = True)
    quartile:int = int(len(sorted_by_residual) / self.quantile)
    high_by_residual:List[Symbol] = [x[0] for x in sorted_by_residual[:quartile]]
    low_by_residual:List[Symbol] = [x[0] for x in sorted_by_residual[-quartile:]]
    
    self.high_residual_portfolios.append(high_by_residual)
    self.low_residual_portfolios.append(low_by_residual)
    
    if len(self.high_residual_portfolios) == self.high_residual_portfolios.maxlen and len(self.low_residual_portfolios) == self.low_residual_portfolios.maxlen:
            
        self.long = [x[0] for x in residual.items() if x[0] in self.high_residual_portfolios[0] and x[0] in self.high_residual_portfolios[1]
                                                    and x[0] in self.high_residual_portfolios[2] and x[0] in self.high_residual_portfolios[3]]
        self.short = [x[0] for x in residual.items() if x[0] in self.low_residual_portfolios[0] and x[0] in self.low_residual_portfolios[1]
                                                    and x[0] in self.low_residual_portfolios[2] and x[0] in self.low_residual_portfolios[3]]
    
    return self.long + self.short
# Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3188172                
def CalculateAccruals(self, current_accrual_data, prev_accrual_data) -> float:
    delta_assets:float = current_accrual_data.CurrentAssets - prev_accrual_data.CurrentAssets
    delta_cash:float = current_accrual_data.CashAndCashEquivalents - prev_accrual_data.CashAndCashEquivalents
    delta_liabilities:float = current_accrual_data.CurrentLiabilities - prev_accrual_data.CurrentLiabilities
    delta_debt:float = current_accrual_data.CurrentDebt - prev_accrual_data.CurrentDebt
    dep:float = current_accrual_data.DepreciationAndAmortization
    total_assets_prev_year:float = prev_accrual_data.TotalAssets
    
    acc:float = (delta_assets - delta_liabilities - delta_cash + delta_debt - dep) / total_assets_prev_year
    return acc
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
    self.selection_flag = True
class StockData():
def __init__(self, current_assets:float, cash_and_cash_equivalents:float, current_liabilities:float, current_debt:float, income_tax_payable:float, 
                    depreciation_and_amortization:float, total_assets:float, sales:float):
    self.CurrentAssets:float = current_assets
    self.CashAndCashEquivalents:float = cash_and_cash_equivalents
    self.CurrentLiabilities:float = current_liabilities
    self.CurrentDebt:float = current_debt
    self.IncomeTaxPayable:float = income_tax_payable
    self.DepreciationAndAmortization:float = depreciation_and_amortization
    self.TotalAssets:float = total_assets
    
    self.Sales:float = sales
def MultipleLinearRegression(x, y):
x = np.array(x).T
x = sm.add_constant(x)
result = sm.OLS(endog=y, exog=x).fit()
return result
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
