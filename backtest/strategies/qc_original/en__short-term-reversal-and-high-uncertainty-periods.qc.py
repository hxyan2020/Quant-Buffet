# Original QuantConnect / library Python
# locale=en slug="short-term-reversal-and-high-uncertainty-periods"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
from pandas.core.series import Series
from pandas.core.frame import DataFrame
#endregion
class ShortTermReversalAndHighUncertaintyPeriods(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    
    self.period: int = 21 # need n daily prices
    
    self.prices: Dict[Symbol, RollingWindow] = {}
    self.weight: Dict[Symbol, float] = {}
    self.pu_recent_values: List[float] = []
    
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.policy_uncertainty_symbol: Symbol = self.AddData(QuantpediaPolicyUncertainty, 'US_ECONOMIC_POLICY_UNCERTAINTY', Resolution.Daily).Symbol
    
    self.quantile:int = 5
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.fundamental_count:int = 1_000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.BeforeMarketClose(market, 0), self.Selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update daily prices
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        
        if symbol in self.prices:
            self.prices[symbol].Add(stock.AdjustedPrice)
            
    # rebalance monthly        
    if not self.selection_flag or len(self.pu_recent_values) == 0:
        return Universe.Unchanged
    
    if self.Time.date() >= QuantpediaPolicyUncertainty.get_last_update_date():
        return Universe.Unchanged
    policy_uncertainty_median: float = np.median(self.pu_recent_values)
    prev_month_policy_uncertainty: float = self.pu_recent_values[-1]
    
    # trade only if previous month policy uncertainty is greater than it's median
    if prev_month_policy_uncertainty  self.min_share_price
        and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    performance: Dict[Symbol, float] = {}
    # warm up stock prices
    for stock in selected:
        symbol: Symbol = stock.Symbol
        
        if symbol not in self.prices:
            self.prices[symbol] = RollingWindow[float](self.period)
            history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                continue
            
            closes: Series = history.loc[symbol].close
            
            for _, close in closes.items():
                self.prices[symbol].Add(close)
        
        if self.prices[symbol].IsReady:
            performance_value: float = self.prices[symbol][0] / self.prices[symbol][self.prices[symbol].Count - 1] - 1
            
            # store stock's performance value keyed by stock's symbol
            performance[symbol] = performance_value
        
    # there has to be enough stocks for quintile selection
    if len(performance)  None:
    # update policy uncertainty values each month
    if self.policy_uncertainty_symbol in slice and slice[self.policy_uncertainty_symbol]:
        policy_uncertainty_value: float = slice[self.policy_uncertainty_symbol].Value
        self.pu_recent_values.append(policy_uncertainty_value)
    
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in slice and slice[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaPolicyUncertainty(PythonData):
_last_update_date: datetime.date = datetime(1,1,1).date()
@staticmethod
def get_last_update_date() -> datetime.date:
   return QuantpediaPolicyUncertainty._last_update_date
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/index/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaPolicyUncertainty()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit():
        return None
    split = line.split(';')
    
    date = split[0] + '-1'
    
    data.Time = datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1) + relativedelta(months=1)
    data.Value = float(split[1])
    if data.Time.date() > QuantpediaPolicyUncertainty._last_update_date:
        QuantpediaPolicyUncertainty._last_update_date = data.Time.date()
    return data
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
