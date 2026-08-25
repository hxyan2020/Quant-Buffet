# Original QuantConnect / library Python
# locale=en slug="vix-beta-factor-in-chinese-equities"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from statsmodels.tsa.arima.model import ARIMA
import numpy as np
from typing import List, Dict
from pandas.core.frame import DataFrame as DF
# endregion

class VIXBetaFactorinChineseEquities(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    
    self.quantile:int = 10
    self.leverage:int = 10
    self.period:int = 1 * 21
    self.max_missing_days:int = 5
    self.SetWarmUp(self.period, Resolution.Daily)

    # market cap filtering
    self.exclusion_flag:bool = True
    self.market_cap_cutoff:float = .5
    
    self.data:dict[str, data_tools.SymbolData] = {}
    self.weights:dict[Symbol, float] = {}
    
    # cboe data
    self.cboe_volatility:Symbol = self.AddData(data_tools.CBOEData, 'CBOE_china_etf_volatility', Resolution.Daily).Symbol
    self.cboe_volatility_data:RollingWindow = RollingWindow[float](self.period)

    self.spy:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.spy), self.TimeRules.AfterMarketOpen(self.spy), self.Selection)

def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    if not self.cboe_volatility_data.IsReady:
        return Universe.Unchanged
    else:
        # custom data is still comming in
        if self.Securities[self.cboe_volatility].GetLastData() and (self.Time.date() - self.Securities[self.cboe_volatility].GetLastData().Time.date()).days > self.max_missing_days:
            return Universe.Unchanged

    selected:List[Symbol] = [x.Symbol for x in coarse if x.HasFundamentalData and x.Price > 5]

    return selected

def FineSelectionFunction(self, fine:List[FineFundamental]) -> List[Symbol]:
    # filter chinese stocks by BusinessCountryID 
    fine:List[FineFundamental] = list(filter(lambda stock: stock.MarketCap != 0 and stock.CompanyReference.BusinessCountryID == 'CHN', fine))

    if self.exclusion_flag:
        # exclude 30% of lowest stocks by MarketCap
        sorted_by_market_cap:List[FineFundamental] = sorted(fine, key = lambda x: x.MarketCap)
        fine = sorted_by_market_cap[int(len(sorted_by_market_cap) * self.market_cap_cutoff):]

    # calculate vix beta
    vix_beta:Dict[FineFundamental, float] = {}

    # VIX innovations
    vix:np.ndarray = np.array(list(self.cboe_volatility_data))
    arma_model = ARIMA(vix, order=(1,0,1))
    model_fit = arma_model.fit()
    innovations:np.ndarray = model_fit.resid[::-1]

    for stock in fine:
        symbol:Symbol = stock.Symbol
        market_cap:float = stock.MarketCap

        history:DF = self.History(symbol, self.period, Resolution.Daily)
        if history.empty or history.loc[symbol].close.size != self.period:
            continue

        closes:np.ndarray = history['close'].values
        stock_returns:np.array = (closes[1:] - closes[:-1]) / closes[:-1]

        model_fit = data_tools.multiple_linear_regression(innovations[2:], stock_returns[:-1])
        vix_beta[stock] = model_fit.params[1]

    if len(vix_beta)  None:
    # store CBOE data
    if self.cboe_volatility in data and data[self.cboe_volatility]:
        close:float = data[self.cboe_volatility].Value
        self.cboe_volatility_data.Add(close)

    if self.IsWarmingUp:
        return

    # monthly rebalance
    if not self.selection_flag:
        return
    self.selection_flag = False

    # trade execution
    stocks_invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in stocks_invested:
        if symbol not in self.weights:
            self.Liquidate(symbol)

    for symbol, w in self.weights.items():
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, w)
    
    self.weights.clear()

def Selection(self):
    self.selection_flag = True
