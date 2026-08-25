# Original QuantConnect / library Python
# locale=en slug="jump-risk-in-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.tseries.offsets import BDay
from typing import List, Dict
import statsmodels.api as sm
# endregion
class JumpRiskinStocks(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.required_exchanges: List[str] = ['NYS', 'NAS', 'ASE']
    self.tickers_to_ignore: List[str] = ['KELYB']
    market: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    self.period: int = 12 * 21
    self.min_share_price: int = 1
    self.leverage: int = 5
    self.quantile: int = 5
    self.price_data: Dict[Symbol, RollingWindow] = {}
    self.weight: Dict[Symbol, float] = {}
    self.underlying_options_strategy: Symbol = self.AddData(QuantpediaEquity, '530_NYSE_MAPPED', Resolution.Daily).Symbol
    self.price_data[self.underlying_options_strategy] = RollingWindow[float](self.period)
    self.fundamental_count: int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.BeforeMarketClose(market, 0), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    QP_equity_last_update_date: Dict[Symbol, datetime.date] = QuantpediaEquity.get_last_update_date()
    # check if custom data is still coming
    if self.Securities[self.underlying_options_strategy].GetLastData() and self.Time.date() > QP_equity_last_update_date[self.underlying_options_strategy]:
        self.Liquidate()
        return Universe.Unchanged
    # update the rolling window every day
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        # store daily price
        if symbol in self.price_data:
            self.price_data[symbol].Add(stock.AdjustedPrice)
    
    if not self.selection_flag:
        return Universe.Unchanged
    selected: List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price > self.min_share_price and \
        x.MarketCap != 0 and x.SecurityReference.ExchangeId in self.required_exchanges and x.Symbol.Value not in self.tickers_to_ignore
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    # warmup price rolling windows
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol not in self.price_data:
            self.price_data[symbol] = RollingWindow[float](self.period)
    
    if not self.price_data[self.underlying_options_strategy].IsReady:
        return Universe.Unchanged
    x_prices: np.ndarray = np.array(list(self.price_data[self.underlying_options_strategy])[:-1])
    x: np.ndarray = x_prices[:-1] / x_prices[1:] - 1
    price_data: Dict[Symbol, List[float]] = {
        stock.Symbol: np.array(list(self.price_data[stock.Symbol])[1:]) 
        for stock in selected 
        if self.price_data[stock.Symbol].IsReady 
        and stock.Symbol != self.underlying_options_strategy
    }
    returns: Dict[Symbol, float] = {symbol : prices[:-1] / prices[1:] - 1 for symbol, prices in price_data.items()}
    y: np.ndarray = np.array(list(zip(*[[i for i in x] for x in returns.values()])))
    model: RegressionResultWrapper = self.multiple_linear_regression(x, y)
    beta_values: np.ndarray = model.params[1]
    equity_beta: Dict[Symbol, float] = { symbol: beta_values[i] for i, symbol in enumerate(price_data.keys()) }
    if len(equity_beta)  None:
    # store underlying strategy price - causing one day lag behind FundamentalSelectionFunction
    if self.underlying_options_strategy in data and data[self.underlying_options_strategy]:
        self.price_data[self.underlying_options_strategy].Add(data[self.underlying_options_strategy].Value)
        
    if not self.selection_flag:
        return
    self.selection_flag = False
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    
    self.weight.clear()
def Selection(self) -> None:
    self.selection_flag = True
def multiple_linear_regression(self, x: np.ndarray, y: np.ndarray):
    x: np.ndarray = sm.add_constant(x, has_constant='add')
    result: RegressionResultWrapper = sm.OLS(endog=y, exog=x).fit()
    return result
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaEquity(PythonData):
_last_update_date:Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return QuantpediaEquity._last_update_date
def GetSource(self, config: SubscriptionDataConfig, date: datetime, isLiveMode: bool) -> SubscriptionDataSource:
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/equity/quantpedia_strategies/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:
    data = QuantpediaEquity()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split: str = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days = 1)
    data['price'] = float(split[1])
    data.Value = float(split[1])
    if config.Symbol not in QuantpediaEquity._last_update_date:
        QuantpediaEquity._last_update_date[config.Symbol] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaEquity._last_update_date[config.Symbol]:
        QuantpediaEquity._last_update_date[config.Symbol] = data.Time.date()
    return data
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
