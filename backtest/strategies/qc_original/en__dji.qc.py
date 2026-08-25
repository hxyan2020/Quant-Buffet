# Original QuantConnect / library Python
# locale=en slug="使用修改后的波动率预测道琼斯工业指数（dji）回"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
import pandas as pd
import statsmodels.api as sm
# endregion

class ModifiedVolatilityPredictsDJIReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 3
    self.equity:Symbol = self.AddEquity("DIA", Resolution.Minute, leverage=self.leverage).Symbol
    self.cash:Symbol = self.AddEquity("BIL", Resolution.Minute, leverage=self.leverage).Symbol

    self.gamma:float = 3.
    self.estimation_period:int = 60
    self.std_period:int = 24
    self.months_in_year:float = 12.
    self.allocation_cap:List[float] = [-0.5, 1.5]

    self.recent_month:int = -1

def OnData(self, data: Slice) -> None:
    if not(data.ContainsKey(self.equity) and data.ContainsKey(self.cash) and data[self.equity] and data[self.cash]):
        return

    # monthly rebalance
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month

    # get monthly closes
    period:int = (self.estimation_period + self.std_period) * 2 + 1
    history:DataFrame = self.History(self.equity, period * 31, Resolution.Daily)['close'].unstack(level=0)
    history = history.groupby(pd.Grouper(freq='M')).last()[self.equity]

    if len(history) >= period:
        history = history.iloc[-period:]
        returns:DataFrame = history.pct_change().iloc[1:]

        # long-term volatility 
        lv:DataFrame = returns.rolling(self.std_period).std() * np.sqrt(self.months_in_year)
        lv = lv.dropna()
        
        # short-term volatility 
        # SVAR is stock variance as in Welch and Goyal (2008)
        svar:DataFrame = (returns ** 2).rolling(self.std_period).sum()
        svar = svar.dropna()
        sv:DataFrame = np.sqrt(svar / self.months_in_year)

        lv_mean:DataFrame = lv.rolling(self.estimation_period).mean()
        lv_mean = lv_mean.dropna()
        sv_mean:DataFrame = sv.rolling(self.estimation_period).mean()
        sv_mean = sv_mean.dropna()

        # beta estimation
        beta_factor:np.ndarray = np.array([((lv.iloc[i-self.estimation_period:i] - lv_mean.iloc[i]) * (sv.iloc[i-self.estimation_period:i] - sv_mean.iloc[i])).sum() for i in range(-1, -(len(lv_mean)+1), -1)])
        beta_devisor:np.ndarray = np.array([((sv.iloc[i-self.estimation_period:i] - sv_mean.iloc[i]) ** 2).sum() for i in range(-1, -(len(lv_mean)+1), -1)])
        beta:np.ndarray = beta_factor / beta_devisor
        adj_lv:np.ndarray = (lv.iloc[-len(beta):].values - (beta * sv.iloc[-len(beta):].values))[-self.estimation_period:]

        # regression to predict return
        model = self.multiple_linear_regression(adj_lv[:-1], returns.iloc[-len(adj_lv):].values[1:])
        ret_pred:float = model.predict(adj_lv[-1])
        variance_pred:float = svar.iloc[-1] #lv.iloc[-1] ** 2

        # allocation
        equity_allocation:float = (ret_pred / (self.gamma * variance_pred))[-1]
        equity_allocation = min(max(equity_allocation, min(self.allocation_cap)), max(self.allocation_cap))
        cash_allocation:float = 1. - equity_allocation

        # trade execution
        self.SetHoldings(self.equity, equity_allocation)
        self.SetHoldings(self.cash, cash_allocation)
    else:
        if self.Portfolio.Invested:
            self.Liquidate()

def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray):
    x:np.ndarray = np.array(x).T
    # x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
