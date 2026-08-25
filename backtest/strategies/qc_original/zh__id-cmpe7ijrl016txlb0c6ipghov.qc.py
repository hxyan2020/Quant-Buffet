# Original QuantConnect / library Python
# locale=zh slug="押注阿尔法"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from scipy import stats
from typing import List, Dict
class BettingAgainstAlpha(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.leverage:int = 10
    self.period:int = 5 * 12 * 21
    self.selection_month_count:int = 12
    # Market data and consolidator.
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    # Daily price data.
    self.data:Dict[Symbol, RollingWindow] = {}
    
    # Market monthly data.
    self.data[self.symbol] = RollingWindow[float](self.period)
        
    self.weight:Dict[Symbol, float] = {}
    
    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.month:int = 12
    self.selection_flag:bool = True
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].Add(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    # selected = [x.Symbol for x in fundamental if x.HasFundamentalData and x.Market == 'usa']
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0 \
                                and x.CompanyReference.IsREIT != 1 and x.SecurityReference.ExchangeId in self.exchange_codes]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            continue
        
        self.data[symbol] = RollingWindow[float](self.period)
        history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes:Series = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].Add(close)
    
    market_returns:List[float] = []
    if self.data[self.symbol].IsReady:
        market_closes:np.ndarray = np.array([x for x in self.data[self.symbol]])
        market_returns = (market_closes[:-1] - market_closes[1:]) / market_closes[1:]
    
    alpha_data:Dict[Symbol, float] = {}
    
    if len(market_returns) != 0:
        for stock in selected:
            symbol:Symbol = stock.Symbol
            if not self.data[symbol].IsReady:
                continue
            stock_closes:np.ndarray = np.array([x for x in self.data[symbol]])
            stock_returns:np.ndarray = (stock_closes[:-1] - stock_closes[1:]) / stock_closes[1:]
            
            beta, alpha, r_value, p_value, std_err = stats.linregress(market_returns, stock_returns)
            alpha_data[symbol] = alpha
    
    if len(alpha_data) != 0: 
        # Alpha diff calc.
        alpha_median:float = np.median([x[1] for x in alpha_data.items()])
        high_alpha_diff:List[List[Symbol, float]] = [[x[0], x[1] - alpha_median] for x in alpha_data.items() if x[1] > alpha_median]
        low_alpha_diff:List[List[Symbol, float]] = [[x[0], alpha_median - x[1]] for x in alpha_data.items() if x[1]  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def Selection(self) -> None:
    if self.month == self.selection_month_count:
        self.selection_flag = True
    self.month += 1
    if self.month > 12:
        self.month = 1
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
