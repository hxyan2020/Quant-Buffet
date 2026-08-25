# Original QuantConnect / library Python
# locale=zh slug="基本面强度与52周最高价异常现象"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from numpy import floor, isnan
from AlgorithmImports import *
from pandas.core.frame import DataFrame
import data_tools
from functools import reduce
class FundamentalStrength52WeekHigh(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.period:int = 52 * 5
    self.holding_period:int = 6
    self.quantile:int = 5
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    
    self.data:Dict[Symbol, data_tools.SymbolData] = {}
    self.last_fine:List[Symbol] = []
    self.managed_queue:List[data_tools.RebalanceQueueItem] = []
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
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.selection_flag = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
            
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the rolling window every day
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update_price(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price > self.min_share_price and \
        all((not isnan(self.rgetattr(x, statement_name)) and self.rgetattr(x, statement_name) != 0) for statement_name in self.financial_statement_names)
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    score = {}
    nearness = {}
    # warmup price rolling windows
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData(symbol, self.period)
            history = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update_price(close)
        
        if self.data[symbol].is_ready():
            nearness[symbol] = self.data[symbol].nearness()
            
            # FSCORE calc            
            roa:float = stock.OperationRatios.ROA.ThreeMonths
            cfo:float = stock.FinancialStatements.CashFlowStatement.CashFlowFromContinuingOperatingActivities.ThreeMonths
            leverage:float = stock.FinancialStatements.BalanceSheet.LongTermDebt.ThreeMonths / stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths
            liquidity:float = stock.OperationRatios.CurrentRatio.ThreeMonths
            equity_offering:float = stock.FinancialStatements.BalanceSheet.OrdinarySharesNumber.ThreeMonths
            gross_margin:float = stock.OperationRatios.GrossMargin.ThreeMonths
            turnover:float = stock.FinancialStatements.IncomeStatement.TotalRevenueAsReported.ThreeMonths / stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths
            
            symbol_data = self.data[symbol]
            # check if data has previous year's data ready and their values are consecutive
            if (not symbol_data.data_is_set()) or (symbol not in self.last_fine):
                symbol_data.update_data(roa, leverage, liquidity, equity_offering, gross_margin, turnover)
                continue
            score[symbol] = 0
            if roa > 0:
                score[symbol] += 1
            if cfo > 0:
                score[symbol] += 1
            if roa > symbol_data.ROA:   # ROA change is positive
                score[symbol] += 1
            if cfo > roa:
                score[symbol] += 1
            if leverage  symbol_data.Liquidity:
                score[symbol] += 1
            if equity_offering  symbol_data.Gross_margin:
                score[symbol] += 1
            if turnover > symbol_data.Turnover:
                score[symbol] += 1
            
            # assing new (this year's) data
            symbol_data.update_data(roa, leverage, liquidity, equity_offering, gross_margin, turnover)
    
    long:List[Symbol] = []
    short:List[Symbol] = []
        
    if len(score) != 0 and len(nearness) >= self.quantile:
        # nearness sorting and F score sorting
        sorted_by_nearness:List[Symbol] = sorted(nearness, key = nearness.get, reverse = True)
        quantile:int = int(len(sorted_by_nearness) / self.quantile)
        high_by_nearness = sorted_by_nearness[:quantile]
        low_by_nearness = sorted_by_nearness[-quantile:]
        long = [x[0] for x in score.items() if x[1] >= 7 and x[0] in high_by_nearness]
        short = [x[0] for x in score.items() if x[1]  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    remove_item = None
    # rebalancing portfolio
    for item in self.managed_queue:
        if item.holding_period == self.holding_period:
            # liquidate
            for symbol, quantity in item.symbol_q:
                self.MarketOrder(symbol, -quantity)
                        
            remove_item = item
        
        # trade execution
        if item.holding_period == 0:
            open_symbol_q = []
            
            for symbol, quantity in item.symbol_q:
                if data.ContainsKey(symbol):
                    self.MarketOrder(symbol, quantity)
                    open_symbol_q.append((symbol, quantity))
                        
            # only opened orders will be closed        
            item.symbol_q = open_symbol_q
            
        item.holding_period += 1
        
    # we need to remove closed part of portfolio after loop. Otherwise it will miss one item in self.managed_queue
    if remove_item:
        self.managed_queue.remove(remove_item)
            
def Selection(self) -> None:
    self.selection_flag = True
# https://gist.github.com/wonderbeyond/d293e7a2af1de4873f2d757edd580288
def rgetattr(self, obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))
