# Original QuantConnect / library Python
# locale=en slug="日内vix贝塔预测股票回报策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from scipy import stats
# endregion

class IntradayVIXBetasPredictStocksReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)

    self.daily_return_data:dict[Symbol, List[float]] = {}

    self.vix = self.AddData(CBOE, 'VIX', Resolution.Daily).Symbol
    self.daily_return_data[self.vix] = []

    self.active_universe:List[Symbol] = []

    self.market_symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.min_return_period:int = 15
    self.quantile:int = 10
    self.leverage:int = 5
    self.min_share_price:float = 5.

    self.SetWarmup(self.min_return_period, Resolution.Daily)
    
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    
    self.selection_flag:bool = False
    self.rebalance_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0
    self.Schedule.On(self.DateRules.MonthStart(self.market_symbol), self.TimeRules.BeforeMarketClose(self.market_symbol), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

        self.daily_return_data[security.Symbol] = []

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    selected:List[CoarseFundamental] = sorted([x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and \
        x.AdjustedPrice >= self.min_share_price and x.SecurityReference.ExchangeId == "NAS"],
        key=lambda x: x.DollarVolume, reverse=True)

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    self.active_universe = list(map(lambda stock: stock.Symbol, selected))
    
    return self.active_universe

def OnData(self, data: Slice) -> None:
    beta:dict[Symbol, float] = {}

    # store daily returns
    if self.vix in data and data[self.vix]:
        vix_return:float = data[self.vix].Close / data[self.vix].Open - 1
        self.daily_return_data[self.vix].append(vix_return)
        
        for symbol in self.active_universe:
            if symbol in data and data[symbol]:
                daily_return:float = data[symbol].Close / data[symbol].Open - 1
                self.daily_return_data[symbol].append(daily_return)
            
            # calculate VIX beta if rebalance flag is set
            if not self.IsWarmingUp and self.rebalance_flag:
                vix_hist_len:int = int(len(self.daily_return_data[self.vix]))
                if vix_hist_len >= self.min_return_period:
                    # both return series have equall lenghts
                    if len(self.daily_return_data[symbol]) == vix_hist_len:
                        # calculate VIX beta
                        slope, _, _, _, _ = stats.linregress(self.daily_return_data[self.vix], self.daily_return_data[symbol])
                        beta[symbol] = slope
            
                # reset daily prices for a given month
                self.daily_return_data[symbol].clear()

    if self.IsWarmingUp:
        return

    if not self.rebalance_flag:
        return
    self.rebalance_flag = False

    self.daily_return_data[self.vix].clear()

    long:List[Symbol] = []
    short:List[Symbol] = []

    if len(beta) >= self.quantile:
        # sort by intraday beta
        sorted_by_beta:List = sorted(beta.items(), key=lambda x: x[1], reverse=True)
        quantile:int = int(len(beta) / self.quantile)
        long = [x[0] for x in sorted_by_beta[-quantile:]]
        short = [x[0] for x in sorted_by_beta[:quantile]]
    
    # order execution
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([long, short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)

def Selection(self) -> None:
    # quarterly universe selection
    if self.Time.month % 3 == 0:
        self.selection_flag = True
    
    # monthly rebalance
    self.rebalance_flag = True

class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
