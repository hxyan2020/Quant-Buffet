# Original QuantConnect / library Python
# locale=en slug="abnormal-turnover-effect-in-the-stock-market"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import statsmodels.api as sm
from typing import List, Dict
from numpy import isnan
class AbnormalTurnoverEffectInTheStockMarket(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    self.quantile:int = 5
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']	
    self.symbol:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    self.data:Dict[Symbol, SymbolData] = {}
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    self.period:int = 21 # need n of daily volumes
    self.regression_period:int = 12 # need n of last turnovers and n * (self.turnover_period - 1) for regression
    
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.fundamental_count:int = 500 # selecting n stocks by dollar volume from fundamentalSelectionFunction
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    self.settings.daily_precise_end_time = False
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update stocks volumes every day
    for stock in fundamental:
        symbol = stock.Symbol
        
        # update stock's volume
        if symbol in self.data:
            self.data[symbol].update(stock.Volume)
    
    # rebalance monthly
    if not self.selection_flag:
        return Universe.Unchanged
    
    # select stocks, which had spin off
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and not isnan(x.EarningReports.BasicAverageShares.ThreeMonths > 0) and x.EarningReports.BasicAverageShares.ThreeMonths > 0 \
                        and x.SecurityReference.ExchangeId in self.exchange_codes]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    u_turn:Dict[Symbol, float] = {} # storing U-TURN of filtered stocks
    
    # warm up selected symbols
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period, self.regression_period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            volumes:Closes = history.loc[symbol].volume
            for _, volume in volumes.items():
                self.data[symbol].update(volume)
        
        if not self.data[symbol].is_ready():
            continue
        
        # check if there is enough data for regression
        if self.data[symbol].turnovers_ready():
            # get x and y for regression
            x, y = self.data[symbol].get_regression_data(self.regression_period)
            
            # calculate regression
            regression_model = self.MultipleLinearRegression(x, y)
            
            # get last residual
            last_resid:float = regression_model.resid[-1]
            # calculate std of all regression residuals
            resid_std:float = np.std(regression_model.resid)
            
            # calculate and store stock's U-TURN
            u_turn[symbol] = last_resid / resid_std
        
        # get stock's volumes for last month
        monthly_volume:float = self.data[symbol].monthly_volume()
        # get stock's shares oustanding
        shares_outstanding:float = stock.EarningReports.BasicAverageShares.ThreeMonths
        
        # calculate and update turnovers for current stock
        self.data[symbol].update_turnovers(monthly_volume / shares_outstanding)
        
    # check if there are enough stocks for quintile selection
    if len(u_turn)  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
        
    self.long.clear()
    self.short.clear()
    
def MultipleLinearRegression(self, x, y):
    # x = np.array(x).T
    # x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
    
def Selection(self) -> None:
    self.selection_flag = True
    
class SymbolData():
def __init__(self, period:int, regression_period:int):
    self.volumes:RollingWindow = RollingWindow[float](period)
    # storing turnovers for regression
    self.turnovers:RollingWindow = RollingWindow[float](regression_period * 2)
        
def update(self, volume:float):
    self.volumes.Add(volume)
    
def update_turnovers(self, turnover:float):
    self.turnovers.Add(turnover)
        
def is_ready(self) -> bool:
    return self.volumes.IsReady
    
def turnovers_ready(self) -> bool:
    return self.turnovers.IsReady
    
def monthly_volume(self) -> float:
    volumes = [x for x in self.volumes]
    return sum(volumes)
        
def get_regression_data(self, regression_period:int):
    # get turnovers
    turnovers:List[float] = [x for x in self.turnovers]
    # reverse list for easier implementation of storing regression data
    turnovers.reverse()
    
    x:List[float] = [] # storing one data point of regression_x in loop
    regression_y:List[float] = []
    regression_x:List[float] = []
    
    for turnover in turnovers:
        if len(x) == (regression_period - 1):
            # add intercept to current x data point
            x = [1] + x
            # add last turnover for current data point in regression to regression_y
            regression_y.append(turnover)
            # add one data point of x to regression_x
            regression_x.append(x)
            # remove intercept and firstly added turnover
            x = x[2:]
        
        # keep adding turnovers to x
        x.append(turnover)
        
    return regression_x, regression_y
    
# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
