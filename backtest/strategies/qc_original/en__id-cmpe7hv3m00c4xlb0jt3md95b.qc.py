# Original QuantConnect / library Python
# locale=en slug="交易日午后反转策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# endregion

class AfternoonReversalTradingStrategy(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.SetTimeZone(TimeZones.NewYork)

    self.market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    self.selected_universe:List[FineFundamental] = []       # selected stock universe
    self.intraday_returns:Dict[Symbol, List[float]] = {}    # intraday returns for the most recent month
    self.recent_open_price:Dict[Symbol, float] = {}         # most recent intraday candle open price

    self.value_weighted_portfolio:bool = False              # False - EW; True - VW
    self.leverage:int = 3
    self.open_hour:int = 15                                 # taking open of this hourly candle
    self.close_hour:int = 16                                # taking close of this hourly candle
    self.min_intraday_return_period:int = 15                # minimum of intraday returns store for them most recent month
    self.quantile:int = 10
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.min_share_price:float = 5.
    self.required_exchanges:List[str] = ['NYS', 'NAS', 'ASE']
    self.tickers_to_ignore:List[str] = ['GME', 'NE']

    self.weight:Dict[Symbol, float] = {}            # traded weights by symbol

    self.selection_flag:bool = False
    self.rebalance_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Hour
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.market, 1), self.TimeRules.AfterMarketOpen(self.market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        symbol:Symbol = security.Symbol

        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

        self.intraday_returns[symbol] = []
        self.recent_open_price[symbol] = 0
    
    for security in changes.RemovedSecurities:
        symbol:Symbol = security.Symbol
        
        if symbol in self.intraday_returns:
            del self.intraday_returns[symbol]
        if symbol in self.recent_open_price:
            del self.recent_open_price[symbol]

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged

    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.AdjustedPrice >= self.min_share_price and \
        x.Symbol.Value not in self.tickers_to_ignore and not x.CompanyReference.IsREIT and x.MarketCap != 0 and x.SecurityReference.ExchangeId in self.required_exchanges]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    cumulative_perf:Dict[Symbol, float] = {}

    for stock in selected:
        symbol:Symbol = stock.Symbol

        if symbol in self.intraday_returns and len(self.intraday_returns[symbol]) >= self.min_intraday_return_period:
            cumulative_eq:np.ndarray = (1 + np.array(self.intraday_returns[symbol])).cumprod()
            cumulative_perf[stock] = cumulative_eq[-1] / cumulative_eq[0] - 1
            
            # reset intraday return monthly series
            self.intraday_returns[symbol] = []

    long:List[FineFundamental] = []
    short:List[FineFundamental] = []

    if len(cumulative_perf) >= self.quantile:
        sorted_by_returns:List = sorted(cumulative_perf.items(), key=lambda x: x[1], reverse=True)
        quantile:int = int(len(sorted_by_returns) / self.quantile)
        long = [x[0] for x in sorted_by_returns[-quantile:]]
        short = [x[0] for x in sorted_by_returns[:quantile]]

    if self.value_weighted_portfolio:
        for i, portfolio in enumerate([long, short]):
            for stock in portfolio:
                mc_sum:float = sum([x.MarketCap for x in portfolio])
                self.weight[stock.Symbol] = ((-1) ** i) * stock.MarketCap / mc_sum
    else:
        for i, portfolio in enumerate([long, short]):
            for stock in portfolio:
                self.weight[stock.Symbol] = ((-1) ** i) / len(portfolio)

    # assign symbols to currently selected universe
    self.selected_universe = list(map(lambda x: x.Symbol, selected))
    self.rebalance_flag = True

    return self.selected_universe

def OnData(self, data: Slice) -> None:
    for symbol in self.selected_universe:
        if data.ContainsKey(symbol):
            # intraday period open candle
            if self.Time.hour == self.open_hour:
                self.recent_open_price[symbol] = data[symbol].Open

            if self.Time.hour == self.close_hour:
                # calculate intraday return
                if symbol in self.recent_open_price and self.recent_open_price[symbol] != 0:
                    open_price:float = self.recent_open_price[symbol]
                    intraday_return:float = data[symbol].Close / open_price - 1
                    self.recent_open_price[symbol] = 0

                    # append intraday return to monthly series
                    if symbol in self.intraday_returns:
                        self.intraday_returns[symbol].append(intraday_return)
        
    if self.Time.hour != 10:
        return

    # monthly rebalance
    if not self.rebalance_flag:
        return
    self.selection_flag = False
    self.rebalance_flag = False

    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)

    self.weight.clear()

def Selection(self) -> None:
    # monthly rebalance
    self.selection_flag = True

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
