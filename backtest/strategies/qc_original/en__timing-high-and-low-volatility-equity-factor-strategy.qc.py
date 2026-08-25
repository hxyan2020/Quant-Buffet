# Original QuantConnect / library Python
# locale=en slug="timing-high-and-low-volatility-equity-factor-strategy"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from pandas.core.frame import DataFrame
class TimingHighLowVolatility(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.period:int = 21
    self.quantile:int = 10
    self.slope_std_threshold:float = 4.
    self.long:List[Symbol] = []
    self.slopes:RollingWindow = RollingWindow[float](12)
    self.data:Dict[Symbol, RollingWindow] = {}
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
            
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].Add(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa']
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    volatility:Dict[Symbol, float] = {}
    momentum:Dict[Symbol, float] = {}
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        
        if symbol not in self.data:
            self.data[symbol] = RollingWindow[float](self.period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes:pd.Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].Add(close)
        
        if self.data[symbol].IsReady:
            closes:np.ndarray = np.array(list(self.data[symbol]))
            momentum[symbol] = closes[0] / closes[-1] - 1
            
            returns:np.ndarray = closes[:-1] / closes[1:] - 1
            volatility[symbol] = np.std(returns)
    if len(momentum) >= self.quantile:
        # Volaility sorting
        sorted_by_vol:List[Symbol] = sorted(volatility, key = volatility.get, reverse = True)
        quantile:int = int(len(sorted_by_vol) / self.quantile)
        high_by_vol:List[Symbol] = sorted_by_vol[:quantile]
        low_by_vol:List[Symbol] = sorted_by_vol[-quantile:]
        mid_by_vol:List[Symbol] = [x for x in sorted_by_vol if x not in high_by_vol and x not in low_by_vol]
    
        # Slope calc
        high_vol_return:float = sum([momentum[x] for x in high_by_vol if x in momentum])
        low_vol_return:float = sum([momentum[x] for x in low_by_vol if x in momentum])
        slope:float = high_vol_return - low_vol_return
    
        if self.slopes.IsReady: 
            slopes:List[float] = list(self.slopes)
            slopes_mean:float = np.mean(slopes)
            slopes_std:float = np.std(slopes)
            if slope > slopes_mean + self.slope_std_threshold * slopes_std:
                self.long = high_by_vol
            elif slope  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # order execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, 1. / len(self.long)) for symbol in self.long if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.long.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
