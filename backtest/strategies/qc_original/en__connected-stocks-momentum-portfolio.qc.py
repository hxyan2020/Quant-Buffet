# Original QuantConnect / library Python
# locale=en slug="connected-stocks-momentum-portfolio"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
from pandas.core.series import Series
from pandas.core.frame import DataFrame
class ConnectedStocksMomentumPortfolio(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100_000)
    self.weight: Dict[Symbol, float] = {}
    self.quantile: int = 5
    self.price_data: Dict[Symbol, RollingWindow] = {}
    self.m_period: int = 12
    self.d_period: int = 21
    self.universe_selection_period: int = 1
    self.recent_estimate_date_by_analyst: Dict[str, Dict[str, datetime.date]] = {}
    
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.required_exchanges: List[str] = ['NYS', 'ASE', 'NAS']
    self.already_subscribed: List[Symbol] = []
    self.leverage: int = 10
    self.min_share_price: float = 5.
    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    self.rebalance_flag: bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
    
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the rolling window every day
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        # store daily price
        if symbol in self.price_data:
            self.price_data[symbol.Value].Add(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    # select new universe once a period
    if self.Time.month % self.universe_selection_period != 0:
        self.rebalance_flag = True
        return Universe.Unchanged
    selected: List[Fundamental] = [x for x in fundamental if x.HasFundamentalData 
        and x.Market == 'usa' 
        and x.MarketCap != 0
        and x.Price >= self.min_share_price 
        and x.SecurityReference.ExchangeId in self.required_exchanges
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    min_date: datetime.date = self.Time.date() - relativedelta(months=self.m_period)
    cf_ret: Dict[Fundamental, float] = {}
    
    for stock in selected:
        symbol: Symbol = stock.Symbol
        i_ticker: str = stock.Symbol.Value
        # subscribe Estimize data
        if symbol not in self.already_subscribed:
            self.AddData(EstimizeEstimate, symbol)
            self.already_subscribed.append(symbol)
        # warmup price rolling windows
        if symbol.Value not in self.price_data:
            self.price_data[symbol.Value] = RollingWindow[float](self.d_period)
            history: DataFrame = self.History(symbol, self.d_period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes: Series = history.loc[symbol].close
            for time, close in closes.items():
                self.price_data[symbol.Value].Add(close)
        
        if self.price_data[symbol.Value].IsReady:
            # nij indexed by j
            n_ij: Dict[str, int] = {}
            
            for analyst, ticker_estimate_dates in self.recent_estimate_date_by_analyst.items():
                # i was covered by analyst
                if i_ticker in ticker_estimate_dates:
                    # check period of the last coverage
                    if ticker_estimate_dates[i_ticker] >= min_date:
                        for j_ticker, date_list in ticker_estimate_dates.items():
                            if j_ticker != i_ticker:
                                # price data for j is ready
                                if j_ticker in self.price_data and self.price_data[j_ticker].IsReady:
                                    # check period of the last coverage
                                    if ticker_estimate_dates[j_ticker] >= min_date:
                                        # found connected stocks covered by an analyst
                                        ticker_pair:tuple[str, str] = (i_ticker, j_ticker)
                                        
                                        # increment of analysts who cover both tickers i and j
                                        if j_ticker not in n_ij:
                                            n_ij[j_ticker] = 0
                                        n_ij[j_ticker] += 1
        
            # calculate CF RET
            N:int = len(n_ij)
            if N != 0:
                cf_ret[stock] = (1 / sum(list(n_ij.values())) * sum([nij * (self.price_data[j_t][0] / self.price_data[j_t][self.d_period - 1] - 1) for j_t, nij in n_ij.items()]))
    self.rebalance_flag = True
    if len(cf_ret) >= self.quantile:
        # CF RET sorting
        sorted_by_cf_ret: List = sorted(cf_ret.items(), key = lambda x:x[1], reverse=True)
        quantile: int = int(len(sorted_by_cf_ret) / self.quantile)
        long: List[Fundamental] = [x[0] for x in sorted_by_cf_ret[:quantile]]
        short: List[Fundamental] = [x[0] for x in sorted_by_cf_ret[-quantile:]]
        # market cap weighting
        for i, portfolio in enumerate([long, short]):
            mc_sum:float = sum(map(lambda x: x.MarketCap, portfolio))
            for stock in portfolio:
                self.weight[stock.Symbol] = ((-1) ** i) * stock.MarketCap / mc_sum
    
    return list(self.weight.keys())
    
def OnData(self, slice: Slice) -> None:
    # store latest EPS Estimize estimate
    estimize = slice.Get(EstimizeEstimate)
    for symbol, value in estimize.items():
        ticker: str = symbol.Value
        if value.AnalystId not in self.recent_estimate_date_by_analyst:
            self.recent_estimate_date_by_analyst[value.AnalystId] = {}
        
        if ticker not in self.recent_estimate_date_by_analyst[value.AnalystId]:
            self.recent_estimate_date_by_analyst[value.AnalystId][ticker] = datetime.min
        
        self.recent_estimate_date_by_analyst[value.AnalystId][ticker] = value.CreatedAt.date()
    if not self.rebalance_flag:
        return
    if not self.selection_flag:
        return
    self.selection_flag = False
    self.rebalance_flag = False
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in slice and slice[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()

def Selection(self) -> None:
    self.selection_flag = True
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
