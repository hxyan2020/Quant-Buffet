# Original QuantConnect / library Python
# locale=en slug="sharpe-sentiment-cycles"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
import statsmodels.api as sm
#endregion
class MarketTimingUsingSharpeRatios(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.data = {}
    self.period = 21 # One month period
    self.regression_data = {}
    # self.regression_period = 10 * 12 + 1 # Need 10 years and one month of data, to predict Y
    self.regression_period = 5 * 12 + 1
    
    self.rf_asset = self.AddEquity('BIL', Resolution.Daily).Symbol  # 5/29/2007.
    
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.spy_monthly_return = RollingWindow[float](self.regression_period)
    self.spy_volatility = RollingWindow[float](self.regression_period)
    self.data[self.symbol] = SymbolData(self.period)
    
    self.dividend_yield = self.AddData(QuandlValue, 'MULTPL/SP500_DIV_YIELD_MONTH', Resolution.Daily).Symbol
    self.regression_data[self.dividend_yield] = RollingWindow[float](self.regression_period)
    
    self.buyback_yield = self.AddData(QuantpediaBuyBackYield, 'BUYBACK_YIELD', Resolution.Daily).Symbol
    self.regression_data[self.buyback_yield] = RollingWindow[float](self.regression_period)
    
    self.symbols = [self.symbol, self.buyback_yield, self.dividend_yield]
    
    self.threshold = 0.2
    self.selection_flag = False
    self.temp_buyback_storing = 0
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    
def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(5)
    
def OnData(self, data):
    for symbol in self.symbols:
        if symbol in data:
            if data[symbol]:
                value = data[symbol].Value
                if value != 0:
                    if symbol == self.symbol: # Storing daily SPY close
                        self.data[symbol].update(value)
                    elif symbol == self.buyback_yield: # This will secure last value of the month
                        self.temp_buyback_storing = value
                    elif symbol == self.dividend_yield: # Annoucment is at the end of month, that's why we use self.temp_buyback_storing for best synchronization
                        self.regression_data[symbol].Add(value)
    
    if not self.selection_flag:
        return
    
    # make sure data is still comming in
    if self.Securities[self.buyback_yield].GetLastData() and (self.Time.date() - self.Securities[self.buyback_yield].GetLastData().Time.date()).days > 31:
        self.Liquidate()
        return
    if self.Securities[self.dividend_yield].GetLastData() and (self.Time.date() - self.Securities[self.dividend_yield].GetLastData().Time.date()).days > 5:
        self.Liquidate()
        return
    
    # Dividend_yield is announced at the end of month, so we take the data of buyback_yield at the end of month, if those two can't be synchronized
    self.regression_data[self.buyback_yield].Add(self.temp_buyback_storing)
    self.selection_flag = False
    
    # Storing monthly return and volatility of SPY
    if self.data[self.symbol].is_ready():
        self.spy_monthly_return.Add(self.data[self.symbol].monthly_return())
        self.spy_volatility.Add(self.data[self.symbol].volatility())
    
    sharpe_ratio = None
    
    # Check if our Y's are ready
    if self.spy_monthly_return.IsReady and self.spy_volatility.IsReady:
        # Check if data for our X are ready
        if self.regression_data[self.dividend_yield].IsReady and self.regression_data[self.buyback_yield].IsReady:
            Y1 = [x  for x in self.spy_volatility][:-1] # Everything except the first data
            Y2 = [x for x in self.spy_monthly_return][:-1] # Everything except the first data
            
            dividend_yield = [x for x in self.regression_data[self.dividend_yield]]
            buyback_yield = [x for x in self.regression_data[self.buyback_yield]]
            
            X = [
              dividend_yield[1:], # Everything except the last data
              buyback_yield[1:] # Everything except the last data
            ]
            
            # beta = slope, alpha = intercept
            # Get expected volatility
            regression_model = self.MultipleLinearRegression(X, Y1) # Volatility regression
            expected_volatility = regression_model.predict([1, dividend_yield[0], buyback_yield[0]]) # 1 is needed constant
            
            # Get expected monthly return
            regression_model = self.MultipleLinearRegression(X, Y2) # Monthly return regression
            expected_return = regression_model.predict([1, dividend_yield[0], buyback_yield[0]]) # 1 is needed constant
            
            sharpe_ratio = (expected_return / expected_volatility)[0]
                
    # Trade execution
    if sharpe_ratio:
        # Liquidate risk-free asset and invest into SPY
        if sharpe_ratio > self.threshold:
            if self.Securities[self.rf_asset].Invested:
                self.Liquidate(self.rf_asset)
            self.SetHoldings(self.symbol, 1)
        else: # Liquidate SPY and invest into risk-free asset
            if self.Securities[self.symbol].Invested:
                self.Liquidate(self.symbol)
            self.SetHoldings(self.rf_asset, 1)
                
def MultipleLinearRegression(self, x, y):
    x = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result        
    
def Selection(self):
    self.selection_flag = True
class SymbolData():
def __init__(self, period):
    self.Closes = RollingWindow[float](period)
    
def update(self, close):
    self.Closes.Add(close)
    
def is_ready(self):
    return self.Closes.IsReady
    
def volatility(self):
    values = [x for x in self.Closes]
    values = np.array(values)
    returns = (values[:-1] - values[1:]) / values[1:]
    return np.std(returns) 
    
def monthly_return(self):
    values = [x for x in self.Closes]
    return (values[0] - values[-1]) / values[-1]
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
    
# Quandl "value" data
class QuandlValue(PythonQuandl):
def __init__(self):
    self.ValueColumnName = 'Value'
    
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaBuyBackYield(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/buyback_yield/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaBuyBackYield()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    buyback = float(split[1])
    SPX = float(split[2])
    data.Value = float(SPX / buyback)
    return data
