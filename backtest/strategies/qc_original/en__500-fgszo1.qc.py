# Original QuantConnect / library Python
# locale=en slug="在标普500股票中反向押注相关性策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
# endregion

class BettingAgainstCorrelationInSP500Stocks(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.volatility_period:int = 12*21
    self.correlation_period:int = 5*12*21
    self.quantile:int = 4
    self.portfolio_percentage:float = 1.
    
    self.prices:Dict[Symbol, RollingWindow] = {}
    self.weight:Dict[Symbol, float] = {}

    self.exchanges:List[str] = ['NYS', 'NAS', 'ASE']

    self.market_symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.prices[self.market_symbol] = RollingWindow[float](self.correlation_period)

    self.max_cap_weight:float = .1
    self.long_leg_corr_treshold:float = 0.
    self.long_leg_corr_substitute:float = .001

    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume

    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.market_symbol), self.TimeRules.BeforeMarketClose(self.market_symbol, 0), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(10)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update daily prices
    for equity in fundamental:
        symbol:Symbol = equity.Symbol

        if symbol in self.prices:
            self.prices[symbol].Add(equity.AdjustedPrice)

    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchanges]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    volatility:Dict[Symbol, list[float, list]] = {}
    stocks_returns:Dict[Symbol, np.ndarray] = {}

    # warm up stock prices
    for stock in selected:
        symbol:Symbol = stock.Symbol
        
        if symbol not in self.prices:
            self.prices[symbol] = RollingWindow[float](self.correlation_period)
            history:DataFrame = self.History(symbol, self.volatility_period, Resolution.Daily)
            if history.empty:
                continue

            closes:pd.Series = history.loc[symbol].close

            for time, close in closes.items():
                self.prices[symbol].Add(close)
        
        # make sure SPY prices are ready
        if not self.prices[self.market_symbol].IsReady:
            continue
        
        # calculate volatility and store daily returns
        if self.prices[symbol].IsReady:
            prices:np.ndarray = np.array([x for x in self.prices[symbol]])
            returns:np.ndarray = prices[:-1] / prices[1:] - 1
            vol_value:float = np.std(returns[:self.volatility_period])

            volatility[symbol] = vol_value
            stocks_returns[symbol] = returns

    # make sure enough stocks has volatility value
    if len(volatility) = corr_median:
                short_leg.append((symbol, corr_value))
                total_short_corr += abs(corr_value)
            else:
                if corr_value  None:
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)

    self.weight.clear()
            
def Selection(self) -> None:
    self.selection_flag = True
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
