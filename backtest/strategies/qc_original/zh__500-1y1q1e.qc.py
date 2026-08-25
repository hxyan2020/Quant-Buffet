# Original QuantConnect / library Python
# locale=zh slug="隐含波动率差与标普500指数预期市场回报"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
import statsmodels.api as sm
import pandas as pd
from QuantConnect.DataSource import *
#endregion
class ImpliedVolatilitySpreadsandExpectedMarketReturnsinSP500(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100_000)
    
    self.leverage: int = 10
    self.vix: Symbol = self.AddData(CBOE, 'VIX', Resolution.Daily).Symbol
    self.put_call: Symbol = self.AddData(data_tools.PutCallRatio, "PutCallRatio", Resolution.Daily).Symbol
    
    # bond yield data
    self.us_yield_10y: Symbol = self.AddData(data_tools.BondYield, 'US10YT', Resolution.Daily).Symbol
    
    self.us_yield_3m: Symbol = self.AddData(data_tools.InterestRate3M, 'IR3TIB01USM156N', Resolution.Daily).Symbol
    self.us_yield_3m_sma: SimpleMovingAverage = SimpleMovingAverage(12)
    # warmup 3m yield history
    us_yield_3m_history: DataFrame = self.History(self.us_yield_3m, 12*30, Resolution.Daily)
    yields: Series = us_yield_3m_history.loc[self.us_yield_3m].value
    for time, _yield in yields.items():
        self.us_yield_3m_sma.Update(time, _yield)
    
    self.daaa_yield: Symbol = self.AddData(data_tools.BondYield, 'DAAA', Resolution.Daily).Symbol
    self.dbaa_yield: Symbol = self.AddData(data_tools.BondYield, 'DBAA', Resolution.Daily).Symbol
    self.last_default_spread: float|None = None
    
    # risk free etf
    symbol_data: Equity = self.AddEquity('BIL', Resolution.Daily)
    self.risk_free_asset: Symbol= symbol_data.Symbol
    symbol_data.SetLeverage(self.leverage)
    
    # SPY and SPTR data
    symbol_data: Equity = self.AddEquity('SPY', Resolution.Daily)
    symbol_data.SetLeverage(self.leverage)
    self.spy: Symbol = symbol_data.Symbol
    
    self.sptr: Symbol = self.AddData(data_tools.SPTRIndex, 'SP500TR', Resolution.Daily).Symbol
    
    self.period: int = 21
    self.SetWarmUp(self.period, Resolution.Daily)
    self.spy_history: RollingWindow = RollingWindow[float](self.period)
    self.sptr_history: RollingWindow = RollingWindow[float](self.period)
    
    self.regression_data: List = []
    self.min_regression_period: int = 12 * 21
    
def OnData(self, slice: Slice) -> None:
    # check if data is still comming in
    put_call_last_update_date: Dict[str, datetime.date] = data_tools.PutCallRatio.get_last_update_date()
    bond_yield_last_update_date: Dict[str, datetime.date] = data_tools.BondYield.get_last_update_date()
    ir_last_update_date: Dict[str, datetime.date] = data_tools.InterestRate3M.get_last_update_date()
    index_last_update_date: Dict[str, datetime.date] = data_tools.SPTRIndex.get_last_update_date()
    if not ((self.put_call.Value in put_call_last_update_date and self.Time.date() = self.min_regression_period:
                regression_df: DataFrame = pd.DataFrame(self.regression_data)
                
                x: DataFrame = regression_df.loc[:, regression_df.columns != 'spy_return'][:-1]    # offset x. Last x entry is used to get Y prediction.
                x = sm.add_constant(x)
                y: DataFrame = regression_df['spy_return'][1:]
                y = y.reset_index(drop=True)
                lm = sm.OLS(y, x).fit()
                last_x = x.tail(1).reset_index(drop=True)
                y_predicted: float = lm.predict(last_x)[0]
                
                if y_predicted > 0:
                    if self.Portfolio[self.risk_free_asset].Invested:
                        self.Liquidate(self.risk_free_asset)
                    self.SetHoldings(self.spy, 1)
                else:
                    if self.Portfolio[self.spy].Invested:
                        self.Liquidate(self.spy)
                    self.SetHoldings(self.risk_free_asset, 1)
                
        self.last_default_spread = default_spread
    else:
        self.Liquidate()
