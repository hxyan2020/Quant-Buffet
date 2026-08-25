# Original QuantConnect / library Python
# locale=zh slug="动量效应与高应计项目"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from numpy import isnan
from functools import reduce
#endregion
class AccuralsData():
def __init__(self, 
            current_assets: float, 
            cash_and_cash_equivalents: float, 
            current_liabilities: float, 
            current_debt: float, 
            income_tax_payable: float, 
            depreciation_and_amortization: float, 
            total_assets: float
            ):
    self.current_assets = current_assets
    self.cash_and_cash_equivalents = cash_and_cash_equivalents
    self.current_liabilities = current_liabilities
    self.current_debt = current_debt
    self.income_tax_payable = income_tax_payable
    self.depreciation_and_amortization = depreciation_and_amortization
    self.total_assets = total_assets
class MomentumAndHighAccruals(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    
    self.data: Dict[Symbol, SymbolData] = {}
    self.accural_data = {} # Latest accurals data
    self.managed_queue = []
    
    self.period: int = 6 * 21
    self.holding_period: int = 6
    self.accrual_quantile: int = 3
    self.momentum_quantile: int = 5
    self.min_share_price: float = 5.
    self.leverage: int = 5
    self.fundamental_count: int = 3_000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']
    self.financial_statement_names: List[str] = [
        'MarketCap',
        'FinancialStatements.BalanceSheet.CurrentAssets.TwelveMonths',
        'FinancialStatements.BalanceSheet.CashAndCashEquivalents.TwelveMonths',
        'FinancialStatements.BalanceSheet.CurrentLiabilities.TwelveMonths',
        'FinancialStatements.BalanceSheet.CurrentDebt.TwelveMonths',
        'FinancialStatements.BalanceSheet.IncomeTaxPayable.TwelveMonths',
        'FinancialStatements.IncomeStatement.DepreciationAndAmortization.TwelveMonths',
    ]
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.selection_flag: bool = True
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the rolling window every day
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        # store daily price
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected: List[Fundamental] = [
        x for x in fundamental if (x.CompanyReference.IsREIT != 1)
        and x.Price > self.min_share_price
        and (x.AssetClassification.MorningstarSectorCode != MorningstarSectorCode.FinancialServices)
        and all((not isnan(self.rgetattr(x, statement_name)) and self.rgetattr(x, statement_name) != 0) for statement_name in self.financial_statement_names)
        and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    bs_acc: Dict[Fundamental, float] = {}
    momentum: Dict[Fundamental, float] = {}
    current_accurals_data: Dict[Symbol, AccuralsData] = {}
    # warmup price rolling windows
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes: Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
        
        if self.data[symbol].is_ready():
            # accural calculation
            current_accurals_data[symbol] = AccuralsData(
                stock.FinancialStatements.BalanceSheet.CurrentAssets.TwelveMonths, stock.FinancialStatements.BalanceSheet.CashAndCashEquivalents.TwelveMonths,
                stock.FinancialStatements.BalanceSheet.CurrentLiabilities.TwelveMonths, stock.FinancialStatements.BalanceSheet.CurrentDebt.TwelveMonths, stock.FinancialStatements.BalanceSheet.IncomeTaxPayable.TwelveMonths,
                stock.FinancialStatements.IncomeStatement.DepreciationAndAmortization.TwelveMonths, stock.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths
            )
        
            if symbol in self.accural_data:
                bs_acc[stock] = self.CalculateAccurals(current_accurals_data[symbol], self.accural_data[symbol])
                momentum[stock] = self.data[symbol].performance()
    
    # clear old accruals and set new ones 
    self.accural_data = current_accurals_data
    winners: List[Fundamental] = []
    losers: List[Fundamental] = []
    if len(momentum) >= self.momentum_quantile * self.accrual_quantile:
        # accural sorting
        sorted_by_acc: List[Tuple] = sorted(bs_acc.items(), key = lambda x: x[1], reverse = True)
        quantile: int = int(len(sorted_by_acc) / self.accrual_quantile)
        
        first_group: Fundamental = [x[0] for x in sorted_by_acc[:quantile]]
        second_group: Fundamental = [x[0] for x in sorted_by_acc[quantile:-quantile:]]
        third_group: Fundamental = [x[0] for x in sorted_by_acc[-quantile:]]
        
        # momentum sorting
        first_sorted_by_mom: Fundamental = sorted(first_group, key = lambda x: momentum[x], reverse = True)
        second_sorted_by_mom: Fundamental = sorted(second_group, key = lambda x: momentum[x], reverse = True)
        third_sorted_by_mom: Fundamental = sorted(third_group, key = lambda x: momentum[x], reverse = True)
        
        # selecting winners and losers
        first_quintile: int = int(len(first_sorted_by_mom) / self.momentum_quantile)
        second_quintile: int = int(len(second_sorted_by_mom) / self.momentum_quantile)
        third_quintile: int = int(len(third_sorted_by_mom) / self.momentum_quantile)
        
        winners = first_sorted_by_mom[:first_quintile] + second_sorted_by_mom[:second_quintile] + third_sorted_by_mom[:third_quintile]
        losers = first_sorted_by_mom[-first_quintile:] + second_sorted_by_mom[-second_quintile:] + third_sorted_by_mom[-third_quintile:]

        symbol_q: List[Tuple] = []
        if len(winners) != 0:
            winners_market_cap: float = sum([x.MarketCap for x in winners])
            long_w: float = self.Portfolio.TotalPortfolioValue / self.holding_period
            for stock in winners:
                symbol_q.append((stock.Symbol, np.floor((long_w * (stock.MarketCap / winners_market_cap)) / self.data[stock.Symbol].last_price)))
        
        if len(losers) != 0:
            losers_market_cap: float = sum([x.MarketCap for x in losers])
            short_w: float = self.Portfolio.TotalPortfolioValue / self.holding_period
            for stock in losers:
                symbol_q.append((stock.Symbol, -np.floor((short_w * (stock.MarketCap / losers_market_cap)) / self.data[stock.Symbol].last_price)))
        
        self.managed_queue.append(RebalanceQueueItem(symbol_q))
        
    return list(map(lambda x: x.Symbol, winners + losers))
def OnData(self, slice: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # trade execution
    remove_item = None
    
    # rebalance portfolio
    for item in self.managed_queue:
        if item.holding_period == self.holding_period + 1:
            for symbol, quantity in item.symbol_q:
                self.MarketOrder(symbol, -quantity)
                        
            remove_item = item
            
        elif item.holding_period == 1:
            opened_symbol_q: List[Tuple[Symbol, float]] = []
            
            for symbol, quantity in item.symbol_q:
                if slice.ContainsKey(symbol) and slice[symbol] is not None and self.Securities[symbol].IsTradable:
                    self.MarketOrder(symbol, quantity)
                    opened_symbol_q.append((symbol, quantity))
                        
            # only opened orders will be closed        
            item.symbol_q = opened_symbol_q
            
        item.holding_period += 1
        
    if remove_item:
        self.managed_queue.remove(remove_item)
    
def Selection(self) -> None:
    self.selection_flag = True

def CalculateAccurals(
    self, 
    current_accural_data: Dict[Symbol, AccuralsData], 
    prev_accural_data: Dict[Symbol, AccuralsData]
    ) -> float:
    delta_assets: float = current_accural_data.current_assets - prev_accural_data.current_assets
    delta_cash: float = current_accural_data.cash_and_cash_equivalents - prev_accural_data.cash_and_cash_equivalents
    delta_liabilities: float = current_accural_data.current_liabilities - prev_accural_data.current_liabilities
    delta_debt: float = current_accural_data.current_debt - prev_accural_data.current_debt
    delta_tax: float = current_accural_data.income_tax_payable - prev_accural_data.income_tax_payable
    dep: float = current_accural_data.depreciation_and_amortization
    avg_total: float = (current_accural_data.total_assets + prev_accural_data.total_assets) / 2
    
    bs_acc: float = ((delta_assets - delta_cash) - (delta_liabilities - delta_debt-delta_tax) - dep) / avg_total
    return bs_acc
def rgetattr(self, obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))
    
class RebalanceQueueItem():
def __init__(self, symbol_q: Tuple[Symbol, float]) -> None:
    # symbol/quantity collections
    self.symbol_q: Tuple[Symbol, float] = symbol_q  
    self.holding_period: int = 0
    
class SymbolData():
def __init__(self, period: int):
    self.closes: RollingWindow = RollingWindow[float](period)
    self.last_price: float|None = None

def update(self, close: float) -> None:
    self.closes.Add(close)
    self.last_price = close
    
def is_ready(self) -> bool:
    return self.closes.IsReady
    
def performance(self) -> float:
    return self.closes[0] / self.closes[self.closes.Count - 1] - 1
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
