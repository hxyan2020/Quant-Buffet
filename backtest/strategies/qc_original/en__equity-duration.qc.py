# Original QuantConnect / library Python
# locale=en slug="equity-duration"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import statsmodels.api as sm
from AlgorithmImports import *
class EquityDuration(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.period:int = 12 * 21 * 5 # need five years of daily data
    self.rebalance_month:int = 4
    self.quantile:int = 10
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.marker_cap_threshold:float = 1e9
    self.data:Dict[Symbol, RollingWindow] = {}
    self.weight:Dict[Symbol, float] = {}
    self.futures_symbols:List[Symbol] = []
    
    tickers:List[str] = ['CME_ES1', 'CME_TY1']
    
    # subscribe to futures
    for ticker in tickers:
        future_symbol:Symbol = self.AddData(QuantpediaFutures, ticker, Resolution.Daily).Symbol
        self.futures_symbols.append(future_symbol)
        
        self.data[future_symbol] = RollingWindow[float](self.period)
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.BeforeMarketClose(market), self.Selection)
    self.settings.daily_precise_end_time = False
    # warm up futures prices
    self.SetWarmUp(self.period, Resolution.Daily)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update daily prices
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            self.data[symbol].Add(stock.AdjustedPrice)
    
    # rebalance monthly
    if not self.selection_flag:
        return Universe.Unchanged
            
    # filter top n stocks by dollar volume, which has price higher than 5$
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and x.MarketCap > self.marker_cap_threshold
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    regression_x = list(map(lambda symbol: self.DailyReturns(list(self.data[symbol])), self.futures_symbols))
    last_update_date:Dict[str, datetime.date] = QuantpediaFutures.get_last_update_date()
    # make sure futures prices are ready
    for future_symbol in self.futures_symbols:
        if not self.data[future_symbol].IsReady:
            # wait until both futures contracts have price data available
            return Universe.Unchanged
        
        # futures data is no longer coming in
        if self.Securities.ContainsKey(future_symbol) and last_update_date[future_symbol.Value]  None:
    # update daily prices of futures
    for future_symbol in self.futures_symbols:
        if future_symbol in data and data[future_symbol]:
            price = data[future_symbol].Value
            self.data[future_symbol].Add(price)
    
    if self.IsWarmingUp:
        return
    
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
def DailyReturns(self, daily_prices: List[float]) -> np.ndarray:
    prices:np.ndarray = np.array(daily_prices)
    return (prices[:-1] - prices[1:]) / prices[1:]
    
def MultipleLinearRegression(self, x, y):
    x = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
    
def Selection(self) -> None:
    self.selection_flag = True
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
_last_update_date:Dict[str, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[str, datetime.date]:
   return QuantpediaFutures._last_update_date
def GetSource(self, config:SubscriptionDataConfig, date:datetime, isLiveMode:bool) -> SubscriptionDataSource:
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/futures/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config:SubscriptionDataConfig, line:str, date:datetime, isLiveMode:bool) -> BaseData:
    data = QuantpediaFutures()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['back_adjusted'] = float(split[1])
    data['spliced'] = float(split[2])
    data.Value = float(split[1])
    # store last update date
    if config.Symbol.Value not in QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol.Value]:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = data.Time.date()
    return data
   
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
