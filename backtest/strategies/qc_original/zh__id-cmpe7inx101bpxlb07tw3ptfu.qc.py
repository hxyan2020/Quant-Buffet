# Original QuantConnect / library Python
# locale=zh slug="商品中的跳跃风险"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.tseries.offsets import BDay
import data_tools
from typing import List, Dict
import statsmodels.api as sm
# endregion
class JumpRiskinCommodities(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.symbols: List[str] = [
        "CME_S1",   # Soybean Futures, Continuous Contract
        "CME_W1",   # Wheat Futures, Continuous Contract
        "CME_SM1",  # Soybean Meal Futures, Continuous Contract
        "CME_BO1",  # Soybean Oil Futures, Continuous Contract
        "CME_C1",   # Corn Futures, Continuous Contract
        "CME_O1",   # Oats Futures, Continuous Contract
        "CME_LC1",  # Live Cattle Futures, Continuous Contract
        "CME_FC1",  # Feeder Cattle Futures, Continuous Contract
        "CME_LN1",  # Lean Hog Futures, Continuous Contract
        "CME_GC1",  # Gold Futures, Continuous Contract
        "CME_SI1",  # Silver Futures, Continuous Contract
        "CME_PL1",  # Platinum Futures, Continuous Contract
        "CME_CL1",  # Crude Oil Futures, Continuous Contract
        "CME_HG1",  # Copper Futures, Continuous Contract
        "CME_LB1",  # Random Length Lumber Futures, Continuous Contract
        "CME_NG1",  # Natural Gas (Henry Hub) Physical Futures, Continuous Contract
        "CME_PA1",  # Palladium Futures, Continuous Contract 
        "CME_RR1",  # Rough Rice Futures, Continuous Contract
        "CME_CU1",  # Chicago Ethanol (Platts) Futures
        "CME_DA1",  # Class III Milk Futures
        
        "ICE_CC1",  # Cocoa Futures, Continuous Contract 
        "ICE_CT1",  # Cotton No. 2 Futures, Continuous Contract
        "ICE_KC1",  # Coffee C Futures, Continuous Contract
        "ICE_O1",   # Heating Oil Futures, Continuous Contract
        "ICE_OJ1",  # Orange Juice Futures, Continuous Contract
        "ICE_SB1",  # Sugar No. 11 Futures, Continuous Contract
    ]
    self.data: Dict[Symbol, RollingWindow] = {}
    self.period: int = 12 * 21
    self.min_share_price: int = 1
    self.leverage: int = 5
    self.quantile: int = 5
    self.market: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.underlying_options_strategy: Symbol = self.AddData(data_tools.QuantpediaEquity, '530_FUTURES_MAPPED', Resolution.Daily).Symbol
    self.data[self.underlying_options_strategy] = RollingWindow[float](self.period)
    self.data[self.market] = RollingWindow[float](self.period)
    self.selection_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    for symbol in self.symbols:
        # Back adjusted and spliced data import.
        security: Security = self.AddData(data_tools.QuantpediaFutures, symbol, Resolution.Daily)
        
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        
        self.data[security.Symbol] = RollingWindow[float](self.period)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.BeforeMarketClose(self.market, 0), self.Selection)
def OnData(self, data: Slice) -> None:
    custom_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.LastDateHandler.get_last_update_date()
    # check if custom data is still coming
    if any(self.Securities[symbol].GetLastData() and self.Time.date() > custom_data_last_update_date[symbol] 
        for symbol in list(self.data.keys()) if symbol != self.market):
        self.Liquidate()
        return Universe.Unchanged
    # update the rolling window every day
    for symbol in self.data.keys():
        # store daily price
        if symbol in data and data[symbol]:
            self.data[symbol].Add(data[symbol].Price)
    
    if not self.selection_flag:
        return
    self.selection_flag = False
    # warmup price rolling windows
    for symbol in self.data.keys():
        if symbol not in self.data:
            self.data[symbol] = RollingWindow[float](self.period)
    
    if not self.data[self.underlying_options_strategy].IsReady or not self.data[self.market].IsReady:
        return
    x_prices: np.ndarray = np.vstack((list(self.data[self.underlying_options_strategy]), list(self.data[self.market]))).T
    x: np.ndarray = x_prices[:-1] / x_prices[1:] - 1
    price_data: Dict[Symbol, List[float]] = {
        symbol: np.array(list(self.data[symbol])) 
        for symbol in self.data.keys() 
        if self.data[symbol].IsReady and 
        symbol not in [self.market, self.underlying_options_strategy]
    }
    
    returns: List[np.ndarray] = [prices[:-1] / prices[1:] - 1 for symbol, prices in price_data.items()]
    y: np.ndarray =  np.array(list(zip(*[[i for i in x] for x in returns])))
    model: RegressionResultWrapper = self.multiple_linear_regression(x, y)
    beta_values: np.ndarray = model.params[1]
    equity_beta: Dict[Symbol, float] = { symbol: beta_values[i] for i, symbol in enumerate(price_data.keys()) }
    if len(equity_beta)  None:
    self.selection_flag = True
def multiple_linear_regression(self, x: np.ndarray, y: np.ndarray):
    x: np.ndarray = sm.add_constant(x, has_constant='add')
    result: RegressionResultWrapper = sm.OLS(endog=y, exog=x).fit()
    return result
