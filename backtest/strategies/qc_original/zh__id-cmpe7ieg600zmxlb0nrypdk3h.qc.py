# Original QuantConnect / library Python
# locale=zh slug="净情绪波动指数效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
# https://quantpedia.com/strategies/net-emotional-volatility-index-effect/
#
# Historical S&P 500 index data are used to estimate the coefficients in the GARCH (1,1) model. Once the GARCH coefficients are obtained, for each day, the investor forecasts the volatility 
# for the next 30 days, reiterating the forecast, which means that every forecast becomes the last observation for the next forecast. The average of these values is called the Average GARCH 
# Forecast (AGF). The investor then calculates the Net Emotional Volatility Index (NEVI) as the difference between the VIX and AGF. The historical NEVI index is then sorted into deciles, and 
# the current NEVI is used as a “Momentum” indicator – the investor opens long on a position when the indicator goes below the 2nd decile and short on positions when it goes above the 8th decile.
# The position is held 30 days from the day of the last long or short signal.
import numpy as np
from arch import arch_model
class NetEmotionalVolatilityIndexEffect(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2008, 1, 1)
    self.SetCash(100000)
    
    self.period:int = 21
    self.holding_period:int = 30
    self.SetWarmUp(self.period + self.holding_period)
        
    self.market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        
    self.vix:Symbol = self.AddData(QuandlVix, "CBOE/VIX", Resolution.Daily).Symbol # starts in 2004
    
    self.days_held:int = 0
    
    self.market_data:RollingWindow = RollingWindow[float](self.period)
    self.volatility:RollingWindow = RollingWindow[float](self.period)
    self.nevi_index:list[float] = []
def OnData(self, data):
    # market data are present in the algorithm
    if self.market in data and data[self.market]:
        market_price:float = data[self.market].Value
        if market_price != 0:
            # store market price data
            self.market_data.Add(market_price)
        
        if self.market_data.IsReady:
            # calcualte market daily returns
            market_prices:np.ndarray = np.array([x for x in self.market_data][::-1])
            market_returns:np.ndarray = (market_prices[:-1] / market_prices[1:] - 1) * 100
            
            # forecast market volatility
            exp_market_volatility:float = self.garch_vol_predict_volatility(market_returns, 1, 1, 30)
            self.volatility.Add(exp_market_volatility)
            
            if self.volatility.IsReady:
                agf:float = np.mean([x for x in self.volatility])
                
                # vix data are present in the algorithm
                if self.vix in data and data[self.vix]:
                    vix:float = data[self.vix].Value
                    self.Plot("Expected Market Volatility", "Expected Market Volatility", exp_market_volatility)
                    self.Plot("VIX", "VIX", vix)
                    if vix != 0:
                        nevi:float = vix - agf
                        self.nevi_index.append(nevi)
                        
                        # wait until at least 30 data points is present for NEVI
                        if len(self.nevi_index) >= self.period and not self.Portfolio[self.market].Invested and not self.IsWarmingUp:
                            low_decile:float = np.percentile(self.nevi_index[:-1], 20)
                            high_decile:float = np.percentile(self.nevi_index[:-1], 80)
                            
                            recent_nevi:float = self.nevi_index[-1]
                            if recent_nevi > high_decile:
                                self.SetHoldings(self.market, -1)
                                self.days_held = 0
                            elif recent_nevi  float:
    am = arch_model(returns, mean='Zero', vol='GARCH', p=p, q=q)
    res = am.fit(disp='off')
    forecasts = res.forecast(horizon=h)
    return np.sqrt(forecasts.variance.values[-1,:][0] * 252)
    
class QuandlVix(PythonQuandl):
def __init__(self):
    self.ValueColumnName = "close"
