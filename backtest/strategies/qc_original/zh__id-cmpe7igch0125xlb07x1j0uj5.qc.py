# Original QuantConnect / library Python
# locale=zh slug="经典股票异常与趋势跟随过滤器相结合"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from functools import reduce
from numpy import isnan
from pandas.core.frame import DataFrame
class ClassicalEquityAnomaliesCombinedwithTrendfollowingFilter(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.financial_statement_names:List[str] = [
        'ValuationRatios.PBRatio',
        'FinancialStatements.IncomeStatement.GrossProfit.TwelveMonths',
        'FinancialStatements.IncomeStatement.TotalOperatingIncomeAsReported.TwelveMonths',
        'OperationRatios.TotalAssetsGrowth.OneYear',
        'FinancialStatements.CashFlowStatement.CapitalExpenditure.TwelveMonths',
        'EarningReports.BasicAverageShares.TwelveMonths',
        # accruals data
        'FinancialStatements.BalanceSheet.CurrentAssets.TwelveMonths',
        'FinancialStatements.BalanceSheet.CashAndCashEquivalents.TwelveMonths',
        'FinancialStatements.BalanceSheet.CurrentLiabilities.TwelveMonths',
        'FinancialStatements.BalanceSheet.CurrentDebt.TwelveMonths',
        'FinancialStatements.BalanceSheet.IncomeTaxPayable.TwelveMonths',
        'FinancialStatements.IncomeStatement.DepreciationAndAmortization.TwelveMonths',
        'FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths'
    ]
    # Daily sma data.
    self.data:Dict[Symbol, SymbolData] = {}
    self.short_period:int = 50
    self.long_period:int = 200
    self.performance_period:int = 12*21
    self.quantile:int = 10
    self.leverage:int = 5
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.BeforeMarketClose(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update SMA every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(self.Time, stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and \
        all((not isnan(self.rgetattr(x, statement_name)) and self.rgetattr(x, statement_name) != 0) for statement_name in self.financial_statement_names)
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # Ranked stocks.
    rank = {}
    current_accruals_data = {}
    acc = {}
    momentum = {}
    net_stock_issue = {}
    capex = {}
    noa = {}
    selected_stocks:List[Fundamental] = []
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.short_period, self.long_period, self.performance_period)
            history:DataFrame = self.History(symbol, self.performance_period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            
            closes:pd.Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(time, close)
        
        if self.data[symbol].is_ready():
            selected_stocks.append(stock)
            rank[symbol] = 0
            momentum[symbol] = self.data[symbol].performance()
        
            # Accural calc
            current_accruals_data = AccrualsData(stock.FinancialStatements.BalanceSheet.CurrentAssets.TwelveMonths, stock.FinancialStatements.BalanceSheet.CashAndCashEquivalents.TwelveMonths,
                                                        stock.FinancialStatements.BalanceSheet.CurrentLiabilities.TwelveMonths, stock.FinancialStatements.BalanceSheet.CurrentDebt.TwelveMonths, stock.FinancialStatements.BalanceSheet.IncomeTaxPayable.TwelveMonths,
                                                        stock.FinancialStatements.IncomeStatement.DepreciationAndAmortization.TwelveMonths, stock.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths)
            if self.data[symbol].accruals_data:
                acc[symbol] = self.CalculateAccruals(current_accruals_data, self.data[symbol].accruals_data)
        
                # Calculate NOA.
                noa[symbol] = (stock.FinancialStatements.BalanceSheet.CurrentAssets.TwelveMonths - stock.FinancialStatements.BalanceSheet.CurrentLiabilities.TwelveMonths) / self.data[symbol].accruals_data.TotalAssets
            
            # Calculate stock stock issue.
            num_of_shares = stock.EarningReports.BasicAverageShares.TwelveMonths
            if self.data[symbol].shares_outstanding:
                net_stock_issue[symbol] = num_of_shares / self.data[symbol].shares_outstanding - 1
            self.data[symbol].shares_outstanding = num_of_shares
            
            # Calculate stock capital expenditure.
            cap_expenditures = stock.FinancialStatements.CashFlowStatement.CapitalExpenditure.TwelveMonths
            if self.data[symbol].capex:
                capex[symbol] = cap_expenditures / self.data[symbol].capex - 1
            self.data[symbol].capex = cap_expenditures
            
            # Update accruals data for next year's calculation.
            self.data[symbol].accruals_data = current_accruals_data            
        
    # Ensure that consecutive accruals and shares data are available.
    for symbol in self.data:
        if symbol not in list(map(lambda x: x.Symbol, selected_stocks)):
            self.data[symbol].accruals_data = None
            self.data[symbol].shares_outstanding = None
            self.data[symbol].capex = None
    
    # Sort by book to market.
    sorted_by_bm = sorted(selected_stocks, key=lambda x: 1 / x.ValuationRatios.PBRatio)
    for index, stock in enumerate(sorted_by_bm):
        rank[stock.Symbol] += (index+1)
    
    # Sort by gross profit.
    sorted_by_gp = sorted(selected_stocks, key=lambda x: x.FinancialStatements.IncomeStatement.GrossProfit.TwelveMonths / x.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths)
    for index, stock in enumerate(sorted_by_gp):
        rank[stock.Symbol] += (index+1)
    # Sort by operating profit.
    sorted_by_op = sorted(selected_stocks, key=lambda x: x.FinancialStatements.IncomeStatement.TotalOperatingIncomeAsReported.TwelveMonths)
    for index, stock in enumerate(sorted_by_op):
        rank[stock.Symbol] += (index+1)
    # Sort by asset growth.
    sorted_by_ag = sorted(selected_stocks, key=lambda x: x.OperationRatios.TotalAssetsGrowth.OneYear, reverse = True)
    for index, stock in enumerate(sorted_by_ag):
        rank[stock.Symbol] += (index+1)
    # Sort by investments.
    sorted_by_inv = sorted(capex.items(), key=lambda x: x[1], reverse = True)
    for index, symbol_si in enumerate(sorted_by_inv):
        rank[symbol_si[0]] += (index+1)
        
    # Sort by net stock issue.
    sorted_by_si = sorted(net_stock_issue.items(), key=lambda x: x[1], reverse = True)
    for index, symbol_si in enumerate(sorted_by_si):
        rank[symbol_si[0]] += (index+1)
    # Sort by accruals.
    sorted_by_acc = sorted(acc.items(), key=lambda x: x[1])
    for index, symbol_acc in enumerate(sorted_by_acc):
        rank[symbol_acc[0]] += (index+1)
    # Sort by NOA.
    sorted_by_noa = sorted(noa.items(), key=lambda x: x[1], reverse = True)
    for index, symbol_noa in enumerate(sorted_by_noa):
        rank[symbol_noa[0]] += (index+1)
    
    if len(rank) > self.quantile:
        # Rank sorting.
        sorted_by_rank:List = sorted(rank.items(), key=lambda x: x[1], reverse = True)
        quantile:int = int(len(sorted_by_rank) / self.quantile)
        top_decile:List[Symbol] = [x[0] for x in sorted_by_rank[:quantile]]
        bottom_decile:List[Symbol] = [x[0] for x in sorted_by_rank[-quantile:]]
        
        top_decile_perf:float = np.mean([momentum[x] for x in top_decile])
        bottom_decile_perf:float = np.mean([momentum[x] for x in bottom_decile])
        
        if top_decile_perf > bottom_decile_perf:
            self.long = top_decile
            self.short = bottom_decile
        else:
            self.long = bottom_decile
            self.short = top_decile
    
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
    # Drop stocks according to trend filter.
    symbols_invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    
    for symbol in symbols_invested:
        if self.Portfolio[symbol].IsLong:
            if not self.data[symbol].is_in_uptrend():
                self.Liquidate(symbol)
        
        elif self.Portfolio[symbol].IsShort:
            if self.data[symbol].is_in_uptrend():
                self.Liquidate(symbol)
    
    if self.Time.month == 6:
        self.selection_flag = True

def CalculateAccruals(self, current_accrual_data, prev_accrual_data) -> float:
    delta_assets = current_accrual_data.CurrentAssets - prev_accrual_data.CurrentAssets
    delta_cash = current_accrual_data.CashAndCashEquivalents - prev_accrual_data.CashAndCashEquivalents
    delta_liabilities = current_accrual_data.CurrentLiabilities - prev_accrual_data.CurrentLiabilities
    delta_debt = current_accrual_data.CurrentDebt - prev_accrual_data.CurrentDebt
    delta_tax = current_accrual_data.IncomeTaxPayable - prev_accrual_data.IncomeTaxPayable
    dep = current_accrual_data.DepreciationAndAmortization
    avg_total = (current_accrual_data.TotalAssets + prev_accrual_data.TotalAssets) / 2
    
    bs_acc = ((delta_assets - delta_cash) - (delta_liabilities - delta_debt-delta_tax) - dep) / avg_total
    return bs_acc
# https://gist.github.com/wonderbeyond/d293e7a2af1de4873f2d757edd580288
def rgetattr(self, obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))
    
class AccrualsData():
def __init__(self, current_assets, cash_and_cash_equivalents, current_liabilities, current_debt, income_tax_payable, depreciation_and_amortization, total_assets):
    self.CurrentAssets = current_assets
    self.CashAndCashEquivalents = cash_and_cash_equivalents
    self.CurrentLiabilities = current_liabilities
    self.CurrentDebt = current_debt
    self.IncomeTaxPayable = income_tax_payable
    self.DepreciationAndAmortization = depreciation_and_amortization
    self.TotalAssets = total_assets
    
class SymbolData():
def __init__(self, short_sma_period, long_sma_period, performance_period):
    self.price = RollingWindow[float](performance_period)
    self.short_sma = SimpleMovingAverage(short_sma_period)
    self.long_sma = SimpleMovingAverage(long_sma_period)
    
    self.accruals_data = None
    self.shares_outstanding = None
    self.capex = None

def update(self, time: datetime, value: float):
    self.short_sma.Update(time, value)
    self.long_sma.Update(time, value)
    self.price.Add(value)

def is_ready(self) -> bool:
    return (self.short_sma.IsReady and self.long_sma.IsReady and self.price.IsReady)

def is_in_uptrend(self) -> bool:
    return (self.short_sma.Current.Value > self.long_sma.Current.Value)
    
def performance(self) -> float:
    return self.price[0] / self.price[self.price.Count - 1] - 1
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
