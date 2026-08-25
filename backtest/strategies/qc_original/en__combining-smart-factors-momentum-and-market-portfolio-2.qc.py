# Original QuantConnect / library Python
# locale=en slug="combining-smart-factors-momentum-and-market-portfolio-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
#endregion
class CombiningSmartFactorsMomentumandMarketPortfolio(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols = {
        'momentum' : 'US_EQUAL_DECILE_1500_12_2m_L_S',
        'value' : 'US_EQUAL_DECILE_1500_B_M_L_S',
        'quality' : 'US_EQUAL_DECILE_1500_ROA_L_S',
        'size' : 'US_EQUAL_DECILE_1500_Size_L_S',
        'volatility' : 'US_EQUAL_DECILE_1500_Volatility_L_S',
        }
    
    # monthly price data
    self.data = {}
    self.long_period = 13
    self.short_period = 2
    self.max_missing_days:int = 5
    
    self.monthly_returns = {}
    self.monthly_returns_period = 12
    
    for symbol, equity_symbol in self.symbols.items():
        data = self.AddData(USEquity, equity_symbol, Resolution.Daily)
        data.SetLeverage(10)
        data.SetFeeModel(CustomFeeModel())
        self.data[symbol] = RollingWindow[float](self.long_period)
        
    self.market = self.AddEquity("IWM", Resolution.Daily).Symbol
    self.data[self.market] = RollingWindow[float](self.short_period)
    
    self.monthly_returns['smart_factors'] = RollingWindow[float](self.monthly_returns_period)
    self.monthly_returns['market'] = RollingWindow[float](self.monthly_returns_period)
    
    self.recent_month:int = -1
    
def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(5)
        
def OnData(self, data):
    # store factor monthly prices
    for symbol, equity_symbol in self.symbols.items():
        if equity_symbol in data and data[equity_symbol]:
            price = data[equity_symbol].Value
            self.data[symbol].Add(price)
    
    # store market prices
    if self.market in data and data[self.market]:
        market_price = data[self.market].Value
        self.data[self.market].Add(market_price)
    
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
        
    slow_momentum = {}
    fast_momentum = {}
    
    # calculate both momentum values
    for symbol, equity_symbol in self.symbols.items():
        if self.Securities[equity_symbol].GetLastData() and (self.Time.date() - self.Securities[equity_symbol].GetLastData().Time.date()).days  market_mean_return:
                    score['smart_factors'] += 1
                else:
                    score['market'] += 1
            
            total_score = score['market'] + score['smart_factors']
            if total_score != 0:
                traded_weight['market'] = score['market'] / total_score
                traded_weight['smart_factors'] = score['smart_factors'] / total_score
                
                # order execution
                # market
                self.SetHoldings(self.market, traded_weight['market'])
                
                # smart factors
                for symbol, equity_symbol in self.symbols.items():
                    if symbol in total_weight:
                        w = total_weight[symbol]
                        self.SetHoldings(equity_symbol, traded_weight['smart_factors'] * w)
                        
class USEquity(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/equity/us_ew_decile/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
# File example.
# date;equity
# 1992-01-31;0.98
def Reader(self, config, line, date, isLiveMode):
    data = USEquity()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    # Prevent lookahead bias.
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    data.Value = float(split[1])
    return data
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
