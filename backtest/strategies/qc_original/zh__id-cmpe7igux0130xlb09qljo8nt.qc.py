# Original QuantConnect / library Python
# locale=zh slug="股票中的趋势因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
import statsmodels.api as sm
from typing import Dict, List, Tuple
from numpy import isnan
class MomentumStockPickingRSIIndicator(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    # RSI indicators.
    self.rsi2:Dict[Symbol, RelativeStrengthIndex] = {}
    self.rsi3:Dict[Symbol, RelativeStrengthIndex] = {}
    self.rsi5:Dict[Symbol, RelativeStrengthIndex] = {}
    self.rsi10:Dict[Symbol, RelativeStrengthIndex] = {}
    
    # Normalized monthly rsi history.
    self.n_rsi2_history:Dict[Symbol, RollingWindow] = {}
    self.n_rsi3_history:Dict[Symbol, RollingWindow] = {}
    self.n_rsi5_history:Dict[Symbol, RollingWindow] = {}
    self.n_rsi10_history:Dict[Symbol, RollingWindow] = {}
    
    self.regression_period:int = 12
    self.period:int = 21
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.leverage:int = 5
    self.quantile:int = 5
    
    # Daily price data.
    self.data:Dict[Symbol, RollingWindow] = {}
    self.perf_history:Dict[Symbol, RollingWindow] = {}
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = False
    self.current_selection:List[Symbol] = []
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(symbol), self.TimeRules.AfterMarketOpen(symbol), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
            
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        price:float = stock.AdjustedPrice
        # Store monthly price.
        if symbol in self.data:  # If symbol is in self.data, then it is in other dictionaries too. So we don't need to check.
            self.data[symbol].Update(self.Time, price)
            self.rsi2[symbol].Update(self.Time, price)
            self.rsi3[symbol].Update(self.Time, price)
            self.rsi5[symbol].Update(self.Time, price)
            self.rsi10[symbol].Update(self.Time, price)
            
            if self.selection_flag and self.data[symbol].IsReady: # All indicators are ready, when indicator in self.data is.
                self.perf_history[symbol].Add(self.data[symbol].Current.Value)
                
                if self.rsi2[symbol].Current.Value == 0 or self.rsi3[symbol].Current.Value == 0 or  \
                self.rsi5[symbol].Current.Value == 0 or self.rsi10[symbol].Current.Value == 0:
                    continue
                
                self.n_rsi2_history[symbol].Add(price / self.rsi2[symbol].Current.Value)
                self.n_rsi3_history[symbol].Add(price / self.rsi3[symbol].Current.Value)
                self.n_rsi5_history[symbol].Add(price / self.rsi5[symbol].Current.Value)
                self.n_rsi10_history[symbol].Add(price / self.rsi10[symbol].Current.Value)
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and not \
            isnan(x.MarketCap) and x.MarketCap != 0 and not isnan(x.CompanyReference.IsREIT) and x.CompanyReference.IsREIT == 0 and \
            x.SecurityReference.ExchangeId in self.exchange_codes]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol in self.data: # If symbol is in self.data, then it is in other dictionaries too. So we don't need to check.
            continue
        self.data[symbol] = RateOfChange(self.period)
        self.perf_history[symbol] = RollingWindow[float](self.regression_period)
        
        self.rsi2[symbol] = RelativeStrengthIndex(2, MovingAverageType.Simple)
        self.n_rsi2_history[symbol] = RollingWindow[float](self.regression_period)
        
        self.rsi3[symbol] = RelativeStrengthIndex(3, MovingAverageType.Simple)
        self.n_rsi3_history[symbol] = RollingWindow[float](self.regression_period)
        
        self.rsi5[symbol] = RelativeStrengthIndex(5, MovingAverageType.Simple)
        self.n_rsi5_history[symbol] = RollingWindow[float](self.regression_period)
        
        self.rsi10[symbol] = RelativeStrengthIndex(10, MovingAverageType.Simple)
        self.n_rsi10_history[symbol] = RollingWindow[float](self.regression_period)
        
        history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet")
            continue
        closes:Close = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].Update(time, close)
            self.rsi2[symbol].Update(time, close)
            self.rsi3[symbol].Update(time, close)
            self.rsi5[symbol].Update(time, close)
            self.rsi10[symbol].Update(time, close)
    self.current_selection = [x.Symbol for x in selected if self.data[x.Symbol].IsReady]
    
    return self.current_selection
    
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    expected_return:Dict[Symbol, float] = {}
    for symbol in self.current_selection:
        if self.perf_history[symbol].IsReady and \
            self.n_rsi2_history[symbol].IsReady and \
            self.n_rsi3_history[symbol].IsReady and \
            self.n_rsi5_history[symbol].IsReady and \
            self.n_rsi10_history[symbol].IsReady:
                    
            monthly_returns:List[float] = [x for x in self.perf_history[symbol]][:-1]
                
            x:List[List[float]] = [
                [x for x in self.n_rsi2_history[symbol]][1:],
                [x for x in self.n_rsi3_history[symbol]][1:],
                [x for x in self.n_rsi5_history[symbol]][1:],
                [x for x in self.n_rsi10_history[symbol]][1:]
            ]
                
            # Regression.
            regression_model = MultipleLinearRegression(x, monthly_returns)
            alpha:float = regression_model.params[0]
            beta1:float = regression_model.params[1]
            beta2:float = regression_model.params[2]
            beta3:float = regression_model.params[3]
            beta4:float = regression_model.params[4]
                
            x1:float = self.n_rsi2_history[symbol][0]
            x2:float = self.n_rsi3_history[symbol][0]
            x3:float = self.n_rsi5_history[symbol][0]
            x4:float = self.n_rsi10_history[symbol][0]
                
            y:float = alpha + (beta1 * x1) + (beta2 * x2) + (beta2 * x3) + (beta3 * x4)
                
            expected_return[symbol] = y
    
    long:List[Symbol] = []
    short:List[Symbol] = []
    # Sort by expected return.
    if len(expected_return) >= self.quantile:
        sorted_by_expected_return:List[Tuple[Symbol, float]] = sorted(expected_return.items(), key = lambda x: x[1], reverse = True)
        quintile:int = int(len(sorted_by_expected_return) / self.quantile)
        long = [x[0] for x in sorted_by_expected_return[:quintile]]
        short = [x[0] for x in sorted_by_expected_return[-quintile:]]
    # Trade execution.
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([long, short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
        
def Selection(self) -> None:
    self.selection_flag = True
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
def MultipleLinearRegression(x, y):
x:np.ndarray = np.array(x).T
x = sm.add_constant(x)
result = sm.OLS(endog=y, exog=x).fit()
return result
