# Original QuantConnect / library Python
# locale=en slug="earnings-quality-factor-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from typing import List, Dict
from numpy import isnan
from dataclasses import dataclass
#endregion
class EarningsQualityFactor(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']
    self.tickers_to_ignore: List[str] = ['TOPS', 'CRW']
    self.fundamental_count = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.leverage: int = 10
    self.quantile: int = 3
    self.rebalance_month: int = 7
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.accruals_data: Dict[Symbol, AcrrualsData] = {}
    
    self.long: List[Symbol] = []
    self.short: List[Symbol] = []
    
    self.data: Dict[Symbol, StockData] = {}
    
    self.selection_flag: bool = True
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.Market == 'usa'
        and x.MarketCap != 0 
        and x.SecurityReference.ExchangeId in self.exchange_codes
        and x.CompanyReference.IndustryTemplateCode != "B"
        and not isnan(x.FinancialStatements.BalanceSheet.CurrentAssets.Value) and x.FinancialStatements.BalanceSheet.CurrentAssets.Value != 0 
        and not isnan(x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value) and x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value != 0 
        and not isnan(x.FinancialStatements.BalanceSheet.CurrentLiabilities.Value) and x.FinancialStatements.BalanceSheet.CurrentLiabilities.Value != 0
        and not isnan(x.FinancialStatements.BalanceSheet.CurrentDebt.Value) and x.FinancialStatements.BalanceSheet.CurrentDebt.Value != 0
        and not isnan(x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.Value) and x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.Value != 0 
        and not isnan(x.FinancialStatements.BalanceSheet.GrossPPE.Value) and x.FinancialStatements.BalanceSheet.GrossPPE.Value != 0
        and not isnan(x.FinancialStatements.IncomeStatement.TotalRevenueAsReported.Value ) and x.FinancialStatements.IncomeStatement.TotalRevenueAsReported.Value != 0
        and not isnan(x.FinancialStatements.CashFlowStatement.OperatingCashFlow.Value) and x.FinancialStatements.CashFlowStatement.OperatingCashFlow.Value != 0
        and not isnan(x.EarningReports.BasicEPS.Value) and x.EarningReports.BasicEPS.Value != 0
        and not isnan(x.EarningReports.BasicAverageShares.Value) and x.EarningReports.BasicAverageShares.Value != 0 
        and not isnan(x.operation_ratios.debt_to_assets.Value) and x.operation_ratios.debt_to_assets.Value != 0
        and not isnan(x.OperationRatios.ROE.Value) and x.OperationRatios.ROE.Value != 0
        and x.Symbol.Value not in self.tickers_to_ignore
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    for stock in selected:
        symbol = stock.Symbol
        if symbol not in self.accruals_data:
            # Data for previous year.
            self.accruals_data[symbol] = None
            
        # Accrual calc.
        current_accruals_data: AcrrualsData = AcrrualsData(stock.FinancialStatements.BalanceSheet.CurrentAssets.Value, stock.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value,
                                            stock.FinancialStatements.BalanceSheet.CurrentLiabilities.Value, stock.FinancialStatements.BalanceSheet.CurrentDebt.Value, stock.FinancialStatements.BalanceSheet.IncomeTaxPayable.Value,
                                            stock.FinancialStatements.IncomeStatement.DepreciationAndAmortization.Value, stock.FinancialStatements.BalanceSheet.TotalAssets.Value,
                                            stock.FinancialStatements.IncomeStatement.TotalRevenueAsReported.Value)
        
        # There is not previous accruals data.
        if not self.accruals_data[symbol]:
            self.accruals_data[symbol] = current_accruals_data
            continue
        
        current_accruals: float = self.CalculateAccruals(current_accruals_data, self.accruals_data[symbol])
        
        # cash flow to assets
        CFA: float = stock.FinancialStatements.CashFlowStatement.OperatingCashFlow.Value / (stock.EarningReports.BasicEPS.Value * stock.EarningReports.BasicAverageShares.Value)
        # debt to assets
        DA: float = stock.operation_ratios.debt_to_assets.Value
        # return on equity
        ROE: float = stock.OperationRatios.ROE.Value
        
        if symbol not in self.data:
            self.data[symbol] = None
        self.data[symbol] = StockData(current_accruals, CFA, DA, ROE)
        self.accruals_data[symbol] = current_accruals_data
    # Remove not updated symbols.
    updated_symbols: List[Symbol] = [x.Symbol for x in selected]
    not_updated: List[Symbol] = [x for x in self.data if x not in updated_symbols]
    for symbol in not_updated:
        del self.data[symbol]
        del self.accruals_data[symbol]
        
    return [x[0] for x in self.data.items()]

def OnData(self, slice: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # Sort stocks by four factors respectively.
    sorted_by_accruals: List[Tuple[Symbol, float]] = sorted(self.data.items(), key=lambda x: x[1].Accruals, reverse=True) # high score with low accrual 
    sorted_by_CFA: List[Tuple[Symbol, float]] = sorted(self.data.items(), key=lambda x: x[1].CFA)                       # high score with high CFA
    sorted_by_DA: List[Tuple[Symbol, float]] = sorted(self.data.items(), key=lambda x: x[1].DA, reverse=True)           # high score with low leverage
    sorted_by_ROE: List[Tuple[Symbol, float]] = sorted(self.data.items(), key=lambda x: x[1].ROE)                       # high score with high ROE
    
    score = {}
    # Assign a score to each stock according to their rank with different factors.
    for i, obj in enumerate(sorted_by_accruals):
        score_accruals = i
        score_CFA = sorted_by_CFA.index(obj)
        score_DA = sorted_by_DA.index(obj)
        score_ROE = sorted_by_ROE.index(obj)
        score[obj[0]] = score_accruals + score_CFA + score_DA + score_ROE
            
    sorted_by_score: List[Tuple[Symbol, float]] = sorted(score.items(), key = lambda x: x[1], reverse = True)
    quantile: int = int(len(sorted_by_score) / self.quantile)
    long: List[Symbol] = [x[0] for x in sorted_by_score[:quantile]]
    short: List[Symbol] = [x[0] for x in sorted_by_score[-quantile:]]
    
    # Trade execution.
    # NOTE: Skip year 2007 due to data error.
    # if self.Time.year == 2007:
    #     self.Liquidate()
    #     return
    
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([long, short]):
        for symbol in portfolio:
            if slice.contains_key(symbol) and slice[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
# Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3188172                
def CalculateAccruals(self, current_accrual_data, prev_accrual_data) -> float:
    delta_assets: float = current_accrual_data.CurrentAssets - prev_accrual_data.CurrentAssets
    delta_cash: float = current_accrual_data.CashAndCashEquivalents - prev_accrual_data.CashAndCashEquivalents
    delta_liabilities: float = current_accrual_data.CurrentLiabilities - prev_accrual_data.CurrentLiabilities
    delta_debt: float = current_accrual_data.CurrentDebt - prev_accrual_data.CurrentDebt
    dep: float = current_accrual_data.DepreciationAndAmortization
    total_assets_prev_year: float = prev_accrual_data.TotalAssets
    
    acc: float = (delta_assets - delta_liabilities - delta_cash + delta_debt - dep) / total_assets_prev_year
    return acc

def Selection(self) -> None:
    if self.Time.month == self.rebalance_month:
        self.selection_flag = True
    
@dataclass
class AcrrualsData():
CurrentAssets: float
CashAndCashEquivalents: float
CurrentLiabilities: float
CurrentDebt: float 
IncomeTaxPayable: float 
DepreciationAndAmortization: float
TotalAssets: float 
Sales: float
@dataclass     
class StockData():
Accruals: AcrrualsData
CFA: float
DA: float 
ROE: float
def MultipleLinearRegression(x, y):
x = np.array(x).T
x = sm.add_constant(x)
result = sm.OLS(endog=y, exog=x).fit()
return result
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
