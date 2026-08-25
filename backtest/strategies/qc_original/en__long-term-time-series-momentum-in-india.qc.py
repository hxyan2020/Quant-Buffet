# Original QuantConnect / library Python
# locale=en slug="long-term-time-series-momentum-in-india"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
import pandas as pd
#endregion
class LongTermTimeSeriesMomentumInIndia(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.data = {}
    self.symbols = []
    
    self.period = 252 # Storing 252-days risk-adjusted return
    self.vol_target_period = 60
    
    self.target_volatility = 0.10 # Target risk of the allocation is 10%
    self.leverage_cap = 4
    self.max_missing_days = 5
    
    self.days_counter = 10
    self.portfolio_part = 1 / 2 # Trading 1 / 2 of portfolio, because strategy is too volatile
    
    self.vol_targeting_flag = True
    
    csv_string_file = self.Download('data.quantpedia.com/backtesting_data/equity/india_stocks/india_nifty_500_tickers.csv')
    lines = csv_string_file.split('\r\n')
    for line in lines:
        line_split = line.split(';')
        
        for ticker in line_split:
            security = self.AddData(QuantpediaIndiaStocks, ticker, Resolution.Daily)
            security.SetFeeModel(CustomFeeModel())
            security.SetLeverage(5)
        
            symbol = security.Symbol
            self.symbols.append(symbol)
            self.data[symbol] = SymbolData(self.period)
def OnData(self, data):
    # Update stock prices
    for symbol in self.symbols:
        if symbol in data and data[symbol]:
            self.data[symbol].update(data[symbol].Value)
              
    # Return from function if holding period didn't end
    if self.days_counter != 10:
        self.days_counter += 1
        return
    self.days_counter = 1
    
    long = []
    short = []
    
    for symbol in self.symbols:
        if self.Securities[symbol].GetLastData() and (self.Time.date() - self.Securities[symbol].GetLastData().Time.date()).days = 0:
                long.append(symbol)
            # If the return is negative, short the stock
            else:
                short.append(symbol)
            
    long_length = len(long)
    short_length = len(short)
    
    if self.vol_targeting_flag:
        # Portfolio volatility calc.
        df = pd.DataFrame()
        weights = []
        
        if long_length > 0:
            self.AppendWeights(df, weights, long, long_length, True)
        
        if short_length > 0:
            self.AppendWeights(df, weights, short, short_length, False)
        
        weights = np.array(weights)
        
        if len(weights) == 0:
            self.Liquidate()
            return
        
        daily_returns = df.pct_change()
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(daily_returns.cov() * 252, weights.T)))
        
        leverage = self.target_volatility / portfolio_vol
        leverage = min(self.leverage_cap, leverage) # cap max leverage
        
        # Trade Execution
        stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
        for symbol in stocks_invested:
            if symbol not in long or symbol not in short:
                self.Liquidate(symbol)
        
        for symbol in long:
            self.SetHoldings(symbol, (1 / long_length) * leverage * self.portfolio_part)
            
        for symbol in short:
            self.SetHoldings(symbol, (-1 / short_length) * leverage * self.portfolio_part)
    
    else:
        # Equally weighted trade execution
        stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
        for symbol in stocks_invested:
            if symbol not in long or symbol not in short:
                self.Liquidate(symbol)
                
        for symbol in long:
            self.SetHoldings(symbol, 1 / long_length * self.portfolio_part)
            
        for symbol in short:
            self.SetHoldings(symbol, -1 / short_length * self.portfolio_part)
            
        
def AppendWeights(self, df, weights, symbols_list, total_symbols, long_flag):
    for symbol in symbols_list:
        df[str(symbol)] = [x for x in self.data[symbol].closes][:self.vol_target_period]
        
        if long_flag:
            weights.append(1 / total_symbols)
        else:
            weights.append(-1 / total_symbols)
    
class SymbolData():
def __init__(self, period):
    self.closes = RollingWindow[float](period)
    
def update(self, close):
    self.closes.Add(close)
    
def is_ready(self):
    return self.closes.IsReady
    
def risk_adjusted_return(self):
    closes = [x for x in self.closes]
    return (closes[0] - closes[-1]) / closes[-1]
    
# Quantpedia data
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaIndiaStocks(PythonData):
def GetSource(self, config, date, isLiveMode):
    source = "data.quantpedia.com/backtesting_data/equity/india_stocks/india_nifty_500/{0}.csv".format(config.Symbol.Value)
    return SubscriptionDataSource(source, SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaIndiaStocks()
    data.Symbol = config.Symbol
    
    try:
        if not line[0].isdigit(): return None
        split = line.split(',')
        
        data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
        data['Price'] = float(split[1])
        data.Value = float(split[1])
    except:
        return None
        
    return data
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
