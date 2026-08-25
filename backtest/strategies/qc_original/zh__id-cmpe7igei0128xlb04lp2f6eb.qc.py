# Original QuantConnect / library Python
# locale=zh slug="大盘股中的价值溢价"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
# endregion
class ValuePremiumInLargeCapStocks(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2011, 1, 1)       # estimize dataset starts in 2011
    self.SetCash(100_000)
    
    self.years_period: int = 3
    self.low_high_percentage: int = 30
    self.min_stocks: int = 10           # big cap part will be split in 30, 40 and 30 percent
    self.leverage: int = 5
    self.min_share_price: int = 5
    self.prices: Dict[Symbol, float] = {}
    self.weights: Dict[Symbol, float] = {}
    self.estimates: Dict[Symbol, Dict[int, List[float]]] = {}
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.already_subscribed: List[Symbol] = []
    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.rebalance_flag: bool = False
    self.selection_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.BeforeMarketClose(market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    self.rebalance_flag = True
    
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.Market == 'usa' 
        and x.Price > self.min_share_price
        and x.MarketCap != 0
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # store estimize db symbol
    for stock in selected:
        if stock.Symbol not in self.already_subscribed:
            self.AddData(EstimizeEstimate, stock.Symbol)
            self.already_subscribed.append(stock.Symbol)
    self.prices = { stock.Symbol: stock.AdjustedPrice for stock in selected }
    market_cap_median: float = np.median(list(map(lambda stock: stock.MarketCap, selected)))
    large_cap: List[Fundamental] = list(filter(lambda stock: stock.MarketCap > market_cap_median, selected))
    curr_year: int = self.Time.year
    eps_yield_by_stock: Dict[Fundamental, float] = {}
    for stock in large_cap:
        symbol: Symbol = stock.Symbol
        ticker: str = symbol.Value
        if ticker not in self.estimates or curr_year not in self.estimates[ticker]:
            continue
        eps_mean: float = self.CalcEpsMean(self.estimates[ticker], curr_year, self.years_period)
        eps_yield: float = eps_mean / self.prices[symbol]
        if eps_yield > 0:
            eps_yield_by_stock[stock] = eps_yield
    if len(eps_yield_by_stock)  bottom_percentile_eps]
    # market cap weighting
    for i, portfolio in enumerate([long_leg, short_leg]):
        mc_sum: float = sum(list(map(lambda stock: stock.MarketCap, portfolio)))
        for stock in portfolio:
            self.weights[stock.Symbol] = ((-1)**i) * stock.MarketCap / mc_sum
    
    return list(self.weights.keys())
    
def OnData(self, slice: Slice) -> None:
    estimate: Dict[Symbol, float] = slice.Get(EstimizeEstimate)
    for symbol, value in estimate.items():
        ticker: str = symbol.Value
        if ticker not in self.estimates:
            self.estimates[ticker] = {}
        fiscal_year: int = value.FiscalYear
        if fiscal_year not in self.estimates[ticker]:
            self.estimates[ticker][fiscal_year] = []
        self.estimates[ticker][fiscal_year].append(value.Eps)
    # rebalance when selection was made
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weights.items() if slice.contains_key(symbol) and slice[symbol]]
    self.SetHoldings(portfolio, True)
    self.weights.clear()
    
def CalcEpsMean(self, eps_by_years: Dict[int, List[float]], curr_year: int, years_period: int) -> float:
    eps_values: List[float] = []
    for i in range(years_period):
        year: int = curr_year + i
        if year in eps_by_years:
            eps_values += eps_by_years[year]
    return np.mean(eps_values)
def Selection(self) -> None:
    self.selection_flag = True
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
