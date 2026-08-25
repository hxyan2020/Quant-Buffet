# Original QuantConnect / library Python
# locale=en slug="结合基本面fscore和股票短期反转"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
from typing import List, Dict
from numpy import floor, isnan
from functools import reduce
from pandas.core.frame import DataFrame
import data_tools

class CombiningFSCOREShortTermReversals(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']

    self.financial_statement_names:List[str] = [
        'EarningReports.BasicAverageShares.ThreeMonths',
        'EarningReports.BasicEPS.TwelveMonths',
        'OperationRatios.ROA.ThreeMonths',
        'OperationRatios.GrossMargin.ThreeMonths',
        'FinancialStatements.CashFlowStatement.CashFlowFromContinuingOperatingActivities.ThreeMonths',
        'FinancialStatements.IncomeStatement.NormalizedIncome.ThreeMonths',
        'FinancialStatements.BalanceSheet.LongTermDebt.ThreeMonths',
        'FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths',
        'FinancialStatements.BalanceSheet.OrdinarySharesNumber.ThreeMonths',
        'FinancialStatements.IncomeStatement.TotalRevenueAsReported.ThreeMonths',
        'ValuationRatios.PERatio',
        'OperationRatios.CurrentRatio.ThreeMonths',
    ]

    self.SetSecurityInitializer(lambda x: x.SetMarketPrice(self.GetLastKnownPrice(x)))
    
    self.leverage:int = 10
    self.min_share_price:int = 5
    self.period = 21

    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    self.stock_data:Dict[Symbol, data_tools.StockData] = {}
    self.data:Dict[Symbol, data_tools.SymbolData] = {}

    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    
    self.selection_flag = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
   
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        # Store daily price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)

    if not self.selection_flag:
        return Universe.Unchanged

    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.AdjustedPrice > self.min_share_price \
        and all((not isnan(self.rgetattr(x, statement_name)) and self.rgetattr(x, statement_name) != 0) for statement_name in self.financial_statement_names) \
        and x.SecurityReference.ExchangeId in self.exchange_codes]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol

        if symbol in self.data:
            continue
        
        self.data[symbol] = data_tools.SymbolData(symbol, self.period)
        history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes:Series = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].update(close)                  

    # BM sorting
    sorted_by_market_cap:List[Fundamental] = sorted(selected, key = lambda x: x.MarketCap, reverse = True)
    lenght:int = int((len(sorted_by_market_cap) / 100) * 40)
    top_by_market_cap:List[Fundamental] = [x for x in sorted_by_market_cap[:lenght]]

    fine_symbols:List[Symbol] = [x.Symbol for x in top_by_market_cap]
    
    score_performance:Dict[Symbol, Tuple[float]] = {}
    
    for stock in top_by_market_cap:
        symbol:Symbol = stock.Symbol
        
        if not self.data[symbol].is_ready():
            continue

        if symbol not in self.stock_data:
            self.stock_data[symbol] = data_tools.StockData()   # Contains latest data.
            
        roa:float = stock.OperationRatios.ROA.ThreeMonths
        cfo:float = stock.FinancialStatements.CashFlowStatement.CashFlowFromContinuingOperatingActivities.ThreeMonths
        leverage:float = stock.FinancialStatements.BalanceSheet.LongTermDebt.ThreeMonths / stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths
        liquidity:float = stock.OperationRatios.CurrentRatio.ThreeMonths
        equity_offering:float = stock.FinancialStatements.BalanceSheet.OrdinarySharesNumber.ThreeMonths
        gross_margin:float = stock.OperationRatios.GrossMargin.ThreeMonths
        turnover:float = stock.FinancialStatements.IncomeStatement.TotalRevenueAsReported.ThreeMonths / stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths
        
        # Check if data has previous year's data ready.
        stock_data = self.stock_data[symbol]
        if (stock_data.ROA == 0) or (stock_data.Leverage == 0) or (stock_data.Liquidity == 0) or (stock_data.Equity_offering == 0) or (stock_data.Gross_margin == 0) or (stock_data.Turnover == 0):
            stock_data.Update(roa, leverage, liquidity, equity_offering, gross_margin, turnover)
            continue

        score:int = 0

        if roa > 0:
            score += 1
        if cfo > 0:
            score += 1
        if roa > stock_data.ROA:   # ROA change is positive
            score += 1
        if cfo > roa:
            score += 1
        if leverage  stock_data.Liquidity:
            score += 1
        if equity_offering  stock_data.Gross_margin:
            score += 1
        if turnover > stock_data.Turnover:
            score += 1
        
        score_performance[symbol] = (score, self.data[symbol].performance())
        
        # Update new (this year's) data.
        stock_data.Update(roa, leverage, liquidity, equity_offering, gross_margin, turnover)
    
    # Clear out not updated data.
    for symbol in self.stock_data:
        if symbol not in fine_symbols:
            self.stock_data[symbol] = data_tools.StockData()
    
    # Performance sorting and F score sorting.
    self.long = [x[0] for x in score_performance.items() if x[1][0] >= 7 and x[1][1]  0]

    return self.long + self.short

def OnData(self, data: Slice) -> None:
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
    self.selection_flag = True

# https://gist.github.com/wonderbeyond/d293e7a2af1de4873f2d757edd580288
def rgetattr(self, obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))
