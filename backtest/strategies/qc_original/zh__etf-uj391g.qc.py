# Original QuantConnect / library Python
# locale=zh slug="基于杠杆型etf投机情绪的交易"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import statsmodels.api as sm
from scipy import stats
# endregion
class TradingBasedonLeveredETFsSpeculationSentiment(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    self.long_etfs: List[str] = ['QLD', 'SSO', 'DDM']
    self.short_etfs: List[str] = ['QID', 'SDS', 'DXD']
    
    # previous month's SO
    self.previous_so: Dict[str, float] = {
        ticker : 0 for ticker in self.long_etfs + self.short_etfs
    }
    
    # monthly prices
    self.m_price_data: Dict[Symbol, RollingWindow] = {}
    # market data
    self.m_regression_period: int = 36 + 1
    self.market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.m_price_data[self.market]: RollingWindow = RollingWindow[float](self.m_regression_period)
    
    self.net_percent_share_change_series: RollingWindow = RollingWindow[float](self.m_regression_period)
    self.shares_out_data:Symbol = self.AddData(ETFSharesOutstanding, 'ETFSharesOutstanding', Resolution.Daily).Symbol
    self.weight: Dict[Symbol, float] = {}   # traded weight for a given month
    # universe selection
    self.quantile: int = 5
    self.leverage: int = 5
    self.leverage_cap: int = 5
    self.exchange_codes: List[str] = ['NYS']
    
    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.recent_month: int = -1
    self.rebalance_flag: bool = False
    self.selection_flag: bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    # update rolling windows every month
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        if symbol in self.m_price_data:
            self.m_price_data[symbol].Add(stock.AdjustedPrice)
    self.selection_flag = False
    
    selected: List[Fundamental] = [
        f for f in fundamental if f.HasFundamentalData 
        and f.Market == 'usa'
        and f.SecurityReference.ExchangeId in self.exchange_codes
        and f.MarketCap != 0
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    # warmup price rolling windows
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol not in self.m_price_data:
            self.m_price_data[symbol] = RollingWindow[float](self.m_regression_period)
            history: DataFrame = self.History(symbol, self.m_regression_period * 30, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            
            closes: Series = history.loc[symbol].close
            closes_len = len(closes.keys())
            # find monthly closes
            for index, time_close in enumerate(closes.items()):
                # index out of bounds check.
                if index + 1 = self.quantile:
        # sorting by SSI sensitivity
        sorted_by_sensitivity: List[Fundamental] = sorted(SSI_sensitivity, key = SSI_sensitivity.get, reverse=True)
        quantile: int = int(len(sorted_by_sensitivity) / self.quantile)
        
        long: List[Fundamental] = []
        short: List[Fundamental] = []
        if SSI[0] > 0:
            long = sorted_by_sensitivity[-quantile:]
            short = sorted_by_sensitivity[:quantile]
        else:
            long = sorted_by_sensitivity[:quantile]
            short = sorted_by_sensitivity[-quantile:]
        # value weighting
        for i, portfolio in enumerate([long, short]):
            mc_sum: float = sum(map(lambda x: x.MarketCap, portfolio))
            for stock in portfolio:
                self.weight[stock.Symbol] = ((-1) ** i) * stock.MarketCap / mc_sum
        # magnitude of SSI scales the portfolio itself; average leverage is equal to zero
        abs_ssi_values: np.ndarray = abs(SSI)
        percentile: float = stats.percentileofscore(abs_ssi_values[1:], abs_ssi_values[0]) / 100.
        leverage: float = 1 - ((0.5 - percentile) * 2) if percentile  None:
    if (self.Time.date() > ETFSharesOutstanding.get_last_update_date()):
        self.selection_flag = False
        self.Liquidate()
        return
    # SO data came in 
    if self.shares_out_data in data and data[self.shares_out_data]:
        # universe selection and rebalance is done once a month when new SO data comes
        if self.Time.month != self.recent_month:
            self.selection_flag = True
            self.recent_month = self.Time.month
            long_psc_sum: float = 0
            short_psc_sum: float = 0
            data_ready_ticker_cnt: int = 0    # n of tickers with SO data ready
            for ticker in self.long_etfs + self.short_etfs:
                so: float = data[self.shares_out_data].GetProperty(ticker)
                
                # ticker has previous month's SO data
                if self.previous_so[ticker] != 0:
                    data_ready_ticker_cnt += 1
                    percent_share_change: float = -1 + (so / self.previous_so[ticker])
                    if ticker in self.long_etfs:
                        long_psc_sum += percent_share_change
                    else:
                        short_psc_sum += percent_share_change
                
                self.previous_so[ticker] = so
            
            # every ticker had SO data ready
            if data_ready_ticker_cnt == len(self.long_etfs + self.short_etfs):
                psc_net: float = long_psc_sum - short_psc_sum
                self.net_percent_share_change_series.Add(psc_net)
                
    # rebalance once a month
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()

def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray, add_residual:bool = True):
    x:np.ndarray = np.array(x).T
    
    if add_residual:
        x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
# Custom data
class ETFSharesOutstanding(PythonData):
_last_update_date: datetime.date = datetime(1,1,1).date()
@staticmethod
def get_last_update_date() -> datetime.date:
   return ETFSharesOutstanding._last_update_date
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/equity/etf_shares_outstanding.csv", SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = ETFSharesOutstanding()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit():
        self.header_columns = line.split(';')
        return None
        
    split = line.split(';')
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    data.Value = float(split[1])
    for i, col in enumerate(self.header_columns[1:]): # skip date
        data[col] = float(split[i+1])
    # store last update date
    if data.Time.date() > ETFSharesOutstanding._last_update_date:
        ETFSharesOutstanding._last_update_date = data.Time.date()
    return data
# Custom fee model.
class CustomFeeModel():
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
