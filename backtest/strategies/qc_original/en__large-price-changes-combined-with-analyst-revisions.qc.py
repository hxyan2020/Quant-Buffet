# Original QuantConnect / library Python
# locale=en slug="large-price-changes-combined-with-analyst-revisions"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.tseries.offsets import BDay
from typing import List, Dict
import data_tools
# endregion
class LargePriceChangesCombinedWithAnalystRevisions(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)       # estimize dataset starts in 2011
    self.SetCash(100_000)
    
    self.years_period: int = 3
    self.low_high_percentage: int = 30
    self.min_values: int = 15
    self.period: int = 45    # need n values for mean volumes calculation
    self.volume_percentage: float = 1.1
    self.return_increase: float = 0.05
    self.days_for_revision: int = 5
    self.leverage: int = 5
    self.min_share_price: int = 5
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']
    self.data: Dict[Symbol, SymbolData] = {}
    self.weights: Dict[Symbol, float] = {}
    self.already_subscribed: Dict[Symbol] = []
    self.estimates: Dict[str, Dict[datetime.date, List[str]]] = {}
    self.analysts_data: Dict[str, Dict[datetime.date, float]] = {}
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.fundamental_count: int = 500
    self.rebalance_flag: bool = False
    self.selection_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.BeforeMarketClose(market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    curr_date: datetime.date = self.Time.date()
    # daily update of prices and volumes
    for equity in fundamental:
        symbol: Symbol = equity.Symbol
        if symbol in self.data:
            self.data[symbol].update(curr_date, equity.AdjustedPrice, equity.Volume)
    # monthly selection
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    self.rebalance_flag = True
    
    selected: List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.MarketCap != 0 and x.Market == 'usa' and x.Price > self.min_share_price and \
        x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    selected_stocks: set = set()
    for stock in selected:
        symbol: Symbol = stock.Symbol
        ticker: str = symbol.Value
        # check if stock is already subscribed
        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData(self.period)
            self.AddData(EstimizeEstimate, symbol)
        if not self.data[symbol].is_ready(self.min_values):
            continue
        if ticker not in self.estimates:
            continue
        
        large_swing_dates: List[datetime.date] = self.data[symbol].get_large_swing_dates(self.volume_percentage, self.return_increase)
        # iterate through each large swing date and check if any analyst increased estimated EPS within self.days_for_revision days
        for date in large_swing_dates:
            for i in range(1, self.days_for_revision + 1, 1):
                future_date: datetime.date = (date + BDay(i)).date()
                if future_date not in self.estimates[ticker]:
                    continue
                analyst_ids: List[str] = self.estimates[ticker][future_date]
                for analyst_id in analyst_ids:
                    estimate_dates: List[datetime.date] = list(self.analysts_data[analyst_id].keys())
                    estimate_dates.reverse()
                    est_after_swing: float = self.analysts_data[analyst_id][future_date]
                    latest_date_before_swing: datetime.date = next((est_date for est_date in estimate_dates if est_date  self.analysts_data[analyst_id][latest_date_before_swing]):
                        selected_stocks.add(symbol)
                        break
                
                # stock were already selected, no need to check any more dates
                if selected_stocks in selected_stocks:
                    break
    # reset monthly data
    for symbol, symbol_obj in self.data.items():
        symbol_obj.reset_monthly_data()
    long_length: int = len(selected_stocks)
    for symbol in selected_stocks:
        self.weights[symbol] = 1 / long_length
    return list(selected_stocks)
    
def OnData(self, data: Slice) -> None:
    estimate = data.Get(EstimizeEstimate)
    for symbol, value in estimate.items():
        ticker: str = symbol.Value
        if ticker not in self.estimates:
            self.estimates[ticker] = {}
        created_at: datetime.date = value.CreatedAt.date()
        if created_at not in self.estimates[ticker]:
            self.estimates[ticker][created_at] = []
        analyst_id: str = value.AnalystId
        self.estimates[ticker][created_at].append(analyst_id)
        if analyst_id not in self.analysts_data:
            self.analysts_data[analyst_id] = {}
        self.analysts_data[analyst_id][created_at] = value.Eps
    # rebalance when selection was made
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    # reset monthly data
    for _, symbol_obj in self.data.items():
        symbol_obj.reset_monthly_data()
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weights.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    
    self.weights.clear()
def Selection(self) -> None:
    self.selection_flag = True
