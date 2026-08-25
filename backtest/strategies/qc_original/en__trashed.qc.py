# Original QuantConnect / library Python
# locale=en slug="__trashed"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
import statsmodels.api as sm
from typing import List, Dict
from numpy import isnan
#endregion
class StockSplitsStrategyBasedOnEarningsManagement(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
  
    self.quantile: int = 3
    self.leverage: int = 5
    self.holding_period: int = 12
    self.lookback_period: int = 30
    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    
    self.invested_symbols: Dict[Symbol, float] = {}
    self.accruals_data: Dict[Symbol, StockData] = {}
    self.data: Dict[Symbol, SymbolData] = {}
    self.splits_data: Dict[Symbol, datetime.date] = {}
    self.last_year_revenue: Dict[Symbol, float] = {}
    self.last_year_receivables: Dict[Symbol, float] = {}
    self.long: List[Symbol] = []
    self.short: List[Symbol] = []
    
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/economic/splits.csv')
    lines: List[str] = csv_string_file.split('\r\n')
    for line in lines:
        line_split: List[str] = line.split(';')
        symbol: str = line_split[0]
        
        self.splits_data[symbol] = []
        
        for i in range(1, len(line_split)):
            if line_split[i] is not '':
                date: datetime.date = datetime.strptime(line_split[i], '%m/%d/%Y').date()
                self.splits_data[symbol].append(date)
    
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthEnd(symbol), self.TimeRules.AfterMarketOpen(symbol), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    # x.ValuationRatios.CFOPerShare and x.ValuationRatios.TotalAssetPerShare error:
    # Runtime Error: N7parquet38ParquetInvalidOrCorruptedFileExceptionE (message: 'Invalid: Parquet magic bytes not found in footer. 
    # Either the file is corrupted or this is not a parquet file.')
    selected: List[Fudnamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.Market == 'usa'
        and not isnan(x.FinancialStatements.BalanceSheet.CurrentAssets.Value) and x.FinancialStatements.BalanceSheet.CurrentAssets.Value > 0
        and not isnan(x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value) and x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value > 0
        and not isnan(x.FinancialStatements.BalanceSheet.CurrentLiabilities.Value) and x.FinancialStatements.BalanceSheet.CurrentLiabilities.Value > 0
        and not isnan(x.FinancialStatements.BalanceSheet.CurrentDebt.Value) and x.FinancialStatements.BalanceSheet.CurrentDebt.Value > 0
        and not isnan(x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.Value) and x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.Value > 0
        and not isnan(x.FinancialStatements.BalanceSheet.GrossPPE.Value) and x.FinancialStatements.BalanceSheet.GrossPPE.Value > 0
        and not isnan(x.ValuationRatios.CFOPerShare) and x.ValuationRatios.CFOPerShare > 0
        and not isnan(x.ValuationRatios.TotalAssetPerShare) and x.ValuationRatios.TotalAssetPerShare > 0
        and not isnan(x.FinancialStatements.BalanceSheet.AccountsReceivable.Value) and x.FinancialStatements.BalanceSheet.AccountsReceivable.Value > 0
        and not isnan(x.FinancialStatements.IncomeStatement.TotalRevenueAsReported.Value) and x.FinancialStatements.IncomeStatement.TotalRevenueAsReported.Value > 0
        and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    market_cap: Dict[Symbol, float] = {}
    ram_residual: Dict[Symbol, float] = {}
    accruals_residual: Dict[Symbol, float] = {}
    
    current_date: datetime.date = self.Time.date()
    # We have only stocks with needed values for linear regressions, because fine was filtered
    for stock in selected:
        symbol: Symbol = stock.Symbol

        market_cap[symbol] = stock.MarketCap
        if symbol not in self.data:
            # Data for linear regressions 
            self.data[symbol] = SymbolData()
        
        if symbol not in self.accruals_data:
            # Data for previous year.
            self.accruals_data[symbol] = None
                    
        # Accrual calc.
        current_accruals_data: StockData = StockData(
            stock.FinancialStatements.BalanceSheet.CurrentAssets.Value, 
            stock.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value,
            stock.FinancialStatements.BalanceSheet.CurrentLiabilities.Value, 
            stock.FinancialStatements.BalanceSheet.CurrentDebt.Value, 
            stock.FinancialStatements.BalanceSheet.IncomeTaxPayable.Value,
            stock.FinancialStatements.IncomeStatement.DepreciationAndAmortization.Value, 
            stock.FinancialStatements.BalanceSheet.TotalAssets.Value,
            stock.FinancialStatements.IncomeStatement.TotalRevenueAsReported.Value
            )
        
        current_year_receivables: float = stock.FinancialStatements.BalanceSheet.AccountsReceivable.Value
        current_year_revenue: float = stock.FinancialStatements.IncomeStatement.TotalRevenueAsReported.Value
        
        if symbol not in self.last_year_receivables: # Need for change calculation of receivables
            self.last_year_receivables[symbol] = None
            
        if symbol not in self.last_year_revenue: # Need for change calculation of revenue
            self.last_year_revenue[symbol] = None
        
        # There is not previous accruals data.
        if not self.accruals_data[symbol]:
            self.accruals_data[symbol] = current_accruals_data
            # Store current year values, which will figure as last year values next year
            self.last_year_revenue[symbol] = current_year_revenue
            self.last_year_receivables[symbol] = current_year_receivables
            continue
        
        # Calculate change
        receivables_change: float = current_year_receivables - self.last_year_receivables[symbol]
        revenue_change: float = current_year_revenue - self.last_year_revenue[symbol]
        
        # Assign current values, which will figure as last year values next year
        self.last_year_receivables[symbol] = current_year_receivables
        self.last_year_revenue[symbol] = current_year_revenue
        
        # This is Y in accruals linear regression    
        current_accruals: float = self.CalculateAccruals(current_accruals_data, self.accruals_data[symbol])
        self.data[symbol].accruals.append(current_accruals)
        
        # This is Y in RAM linear regression
        self.data[symbol].cfo_per_share.append(stock.ValuationRatios.CFOPerShare)
        
        # These are x's for linear regressions 
        self.data[symbol].total_revenue.append(stock.FinancialStatements.IncomeStatement.TotalRevenueAsReported.Value) 
        self.data[symbol].gross_ppe.append(stock.FinancialStatements.BalanceSheet.GrossPPE.Value) 
        self.data[symbol].total_asset_per_share.append(stock.ValuationRatios.TotalAssetPerShare) 
        
        # These are x's for linear regressions, which has to be calculated as a change
        self.data[symbol].total_revenue_change.append(revenue_change)
        self.data[symbol].accounts_receivable_change.append(receivables_change) 
        
        # This substraction is needed for Accruals regression
        revenues_minus_receivables: List[float] = []
        for x, y in zip(self.data[symbol].total_revenue_change, self.data[symbol].accounts_receivable_change):
            revenues_minus_receivables.append(x - y)
        
        # Accruals regression
        regression_x: List[List[float]] = [
            [1 / x for x in self.data[symbol].total_asset_per_share], # 1 / TA
            [x for x in revenues_minus_receivables],                  # delta SALES - delta REC
            [x for x in self.data[symbol].gross_ppe]                  # PPE
            ] 
        
        regression_y: List[float] = [x for x in self.data[symbol].accruals] 
             
        regression_model: RegressionResultWrapper = self.MultipleLinearRegression(regression_x, regression_y, True)
        
        accruals_residual[symbol] = regression_model.resid[-1]
        
        # RAM regression
        regression_x: List[List[float]] = [
            [1 / x for x in self.data[symbol].total_asset_per_share], # 1 / TA
            [x for x in self.data[symbol].total_revenue],             # SALES
            [x for x in self.data[symbol].total_revenue_change]       # delta SALES
            ] 
                        
        regression_y: List[float] = [x for x in self.data[symbol].cfo_per_share]
        
        regression_model: RegressionResultWrapper = self.MultipleLinearRegression(regression_x, regression_y, False)
        
        ram_residual[symbol] = regression_model.resid[-1]
    
    long: List[Symbol] = []
    short: List[Symbol] = []
    # Sort residuals from regressions into terciles
    if len(ram_residual) >= self.quantile * 2:
        sorted_by_ram: List[Symbol] = [x[0] for x in sorted(ram_residual.items(), key=lambda item: item[1])]
        sorted_by_accruals: List[Symbol] = [x[0] for x in sorted(accruals_residual.items(), key=lambda item: item[1])]
        
        quantile: int = int(len(sorted_by_ram) / self.quantile)
        
        long: List[Symbol] = [x for x in sorted_by_ram[:quantile] if x in sorted_by_accruals[-quantile:]] # Low ram and high accruals
        short: List[Symbol] = [x for x in sorted_by_ram[-quantile:] if x in sorted_by_accruals[:quantile]] # High ram and low accruals
    
    for symbol in long:
        if symbol.Value in self.splits_data and symbol not in self.invested_symbols:
            if self.CheckStockSplitDate(symbol.Value, current_date-timedelta(days=self.lookback_period), current_date):
                self.long.append(symbol)
    
    for symbol in short:
        if symbol.Value in self.splits_data and symbol not in self.invested_symbols:
            if self.CheckStockSplitDate(symbol.Value, current_date-timedelta(days=self.lookback_period), current_date):
                self.short.append(symbol)
                
    return self.long + self.short
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    for symbol in self.long + self.short:
        if symbol not in self.invested_symbols:
            self.invested_symbols[symbol] = 0
        else:
            self.invested_symbols[symbol] += 1
            # Remove stock, because we held it for 12 months
            if self.invested_symbols[symbol] == self.holding_period:
                del self.invested_symbols[symbol]
                self.Liquidate(symbol)
                
                if symbol in self.long:
                    self.long.remove(symbol)
                else:
                    self.short.remove(symbol)
            
    # trade execution
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    self.SetHoldings(targets, True)
            
def CheckStockSplitDate(self, 
                        ticker: str, 
                        date_from: datetime.date, 
                        date_to: datetime.date) -> bool:
    if len(self.splits_data[ticker]) > 0:
        for split_date in self.splits_data[ticker]:
            if date_from  None:
    self.selection_flag = True

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
    
def MultipleLinearRegression(self, x: List[List[float]], y: List[float], add_intercept: bool):
    x: np.ndarray = np.array(x).T
    if add_intercept: # One regression has intercept, the other one hasn't
        x = sm.add_constant(x)
    result: RegressionResultWrapper = sm.OLS(endog=y, exog=x).fit()
    return result        
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
class StockData():
def __init__(self, 
            current_assets: float, 
            cash_and_cash_equivalents: float, 
            current_liabilities: float, 
            current_debt: float, 
            income_tax_payable: float, 
            depreciation_and_amortization: float, 
            total_assets: float, 
            sales: float) -> None:
    self.CurrentAssets: float = current_assets
    self.CashAndCashEquivalents: float = cash_and_cash_equivalents
    self.CurrentLiabilities: float = current_liabilities
    self.CurrentDebt: float = current_debt
    self.IncomeTaxPayable: float = income_tax_payable
    self.DepreciationAndAmortization: float = depreciation_and_amortization
    self.TotalAssets: float = total_assets
    self.Sales: float = sales
    
class SymbolData():
def __init__(self) -> None:
    self.cfo_per_share: List[float] = []
    self.accruals: List[float] = []
    self.total_revenue: List[float] = []
    self.total_revenue_change: List[float] = []
    self.total_asset_per_share: List[float] = []
    self.accounts_receivable_change: List[float] = []
    self.gross_ppe: List[float] = []
