# Original QuantConnect / library Python
# locale=en slug="lame-duck-ceos"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from scipy import stats
from typing import List, Dict
from pandas.core.frame import DataFrame
from pandas.core.series import Series
# endregion
class LameDuckCEOs(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    
    # Source: https://zenodo.org/record/4543893#.YwNo1xxBw2w
    self.ceo_departure_dates: Symbol = self.AddData(CEODepartureDates, "CEODepartureDates", Resolution.Daily).Symbol
    self.departure_company_tickers: List[str] = []           # recent month CEO departures
    self.departure_company_ticker_universe: set = set()      # ticker universe from the whole dataset
    self.selected_universe: List[Symbol] = []                # currently monthly selected stock universe
    
    self.price_data: Dict[Symbol, RollingWindow] = {}        # daily price data
    self.period: int = 12 * 21
    self.leverage: int = 10
    self.min_share_price: int = 5
    self.market: Symbol = self.AddEquity("SPY", Resolution.Daily, leverage=self.leverage).Symbol
    self.price_data[self.market] = RollingWindow[float](self.period)
    self.selection_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the rolling window every day
    for stock in fundamental:
        symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.price_data:
            self.price_data[symbol].Add(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
            
    selected: List[Symbol] = [
        x.Symbol for x in fundamental 
        if x.Market == 'usa' 
        and x.Price > self.min_share_price 
        and x.Symbol.Value in self.departure_company_tickers
    ]
    for symbol in selected:
        if symbol in self.price_data:
            continue
        
        self.price_data[symbol] = RollingWindow[float](self.period)
        history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes: Series = history.loc[symbol].close
        for time, close in closes.items():
            self.price_data[symbol].Add(close)
    
    if self.price_data[self.market].IsReady:
        self.selected_universe = [x for x in selected if self.price_data[x].IsReady]
    
    return self.selected_universe
def OnData(self, data: Slice) -> None:
    custom_data_last_update_date: Dict[Symbol, datetime.date] = CEODepartureDates.get_last_update_date()
    if self.Securities[self.ceo_departure_dates].GetLastData() and self.Time.date() > custom_data_last_update_date[self.ceo_departure_dates]:
        self.Liquidate()
        return Universe.Unchanged
    # store new ceo departure data
    if data.ContainsKey(self.ceo_departure_dates):
        # store whole ticker universe
        if len(self.departure_company_ticker_universe) == 0:
            self.departure_company_ticker_universe = CEODepartureDates._ticker_universe
        departure_tickers:str = data[self.ceo_departure_dates].GetProperty('stocks')
        for t in departure_tickers:
            self.departure_company_tickers.append(t)
    # monthly rebalance
    if not self.selection_flag:
        return
    self.selection_flag = False
    # select long leg
    long: List[Symbol] = []
    for symbol in self.selected_universe:
        if symbol.Value in self.departure_company_tickers:
            long.append(symbol)
    # reset ceo departure for the recent month
    self.departure_company_tickers.clear()
    if len(long) == 0:
        if self.Portfolio.Invested:
            self.Liquidate()
        return
    # order execution
    total_beta: float = 0.
    market_prices: np.ndarray = np.array(list(self.price_data[self.market]))
    market_perf_data: np.ndarray = market_prices[:-1] / market_prices[1:] - 1
    targets: List[PortfolioTarget] = []
    for symbol in long:
        # calculate beta to market for each stock
        stocks_prices: np.ndarray = np.array(list(self.price_data[symbol]))
        stock_perf_data: np.ndarray = stocks_prices[:-1] / stocks_prices[1:] - 1
        slope, intercept, r_value, p_value, std_err = stats.linregress(market_perf_data, stock_perf_data)
        total_beta += slope
        if data.contains_key(symbol) and data[symbol]:
            targets.append(PortfolioTarget(symbol, 1 / len(long)))
    self.SetHoldings(targets, True)
    avg_beta_to_market: float = total_beta / len(long)
    # market hedge
    self.SetHoldings(self.market, -avg_beta_to_market)
def Selection(self) -> None:
    if len(self.departure_company_ticker_universe) != 0:
        self.selection_flag = True
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
# CEO departure dates.
# SOURCE: https://zenodo.org/record/4543893#.YwNo1xxBw2w
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class CEODepartureDates(PythonData):
_ticker_universe:Set[str] = set()
_last_update_date:Dict[Symbol, datetime.date] = {}
def GetSource(self, config:SubscriptionDataConfig, date:datetime, isLiveMode:bool) -> SubscriptionDataSource:
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/economic/ceo_departure_dates.json", SubscriptionTransportMedium.RemoteFile, FileFormat.UnfoldingCollection)
   
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return CEODepartureDates._last_update_date
@staticmethod
def get_ticker_universe() -> list:
   return list(CEODepartureDates._ticker_universe)
def Reader(self, config:SubscriptionDataConfig, line:str, date:datetime, isLiveMode:bool) -> BaseData:
    objects:list[CEODepartureDates] = []
    data:list[dict] = json.loads(line)
    end_time:datetime.date|None = None
    for index, sample in enumerate(data):
        custom_data:CEODepartureDates = CEODepartureDates()
        custom_data.Symbol = config.Symbol
        
        departure_date:datetime.date = datetime.strptime(sample['departure_date'], '%Y-%m-%d')
        custom_data.Time = departure_date
        custom_data.EndTime = custom_data.Time + timedelta(days=1)
        custom_data['stocks'] = sample['stocks']
        custom_data.Value = 1
        end_time = custom_data.EndTime
        # store last date of the symbol
        if config.Symbol not in CEODepartureDates._last_update_date:
            CEODepartureDates._last_update_date[config.Symbol] = datetime(1,1,1).date()
        if custom_data.Time.date() > CEODepartureDates._last_update_date[config.Symbol]:
            CEODepartureDates._last_update_date[config.Symbol] = custom_data.Time.date()
        for ticker in sample['stocks']:
            CEODepartureDates._ticker_universe.add(ticker)
        objects.append(custom_data)
    return BaseDataCollection(end_time, config.Symbol, objects)
