# Original QuantConnect / library Python
# locale=en slug="股票和债券回报预测货币回报"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import statsmodels.api as sm
from AlgorithmImports import *
import data_tools

class TheSerialDependenceoftheCommodityFuturesReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    # equity etf and 10Y bond yield symbols by currency symbol
    self.symbols = {
        "AUDUSD" : ("EWA", "AU10YT"),
        "CADUSD" : ("EWC", "CA10YT"),
        "EURUSD" : ("EWG", "DE10YT"),
        "JPYUSD" : ("EWJ", "JP10YT"),
        "NZDUSD" : ("ENZL", "NZ10YT"),
        "USDNOK" : ("ENOR", "NO10YT"),
        "CHFUSD" : ("EWL", "CH10YT"),
        "GBPUSD" : ("EWU", "GB10YT"),
        "USDINR" : ("INDA", "IN10YT"),
        "USDMXN" : ("EWW", "MX10YT"),
        "USDPLN" : ("EPOL", "PL10YT"),
        "USDSGD" : ("EWS", "SG10YT"),
        "USDTRY" : ("TUR", "TR10YT"),
        }
    
    self.us_bonds = self.AddData(data_tools.QuantpediaBondYield, "US10YT", Resolution.Daily).Symbol
    self.us_equities = self.AddEquity("VTI", Resolution.Daily).Symbol

    self.daily_period = 21
    self.period = 120 + 1
    self.SetWarmUp(self.period * self.daily_period, Resolution.Daily)
    
    self.perf_data = {}
    self.last_month_price = {}
    self.bond_yield_values = {}
    
    for currency_symbol, (equity_symbol, bond_symbol) in self.symbols.items():
        # currency
        data = self.AddForex(currency_symbol, Resolution.Daily, Market.Oanda)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(5)
        
        # equity
        self.AddEquity(equity_symbol, Resolution.Daily)
        
        # bond
        self.AddData(data_tools.QuantpediaBondYield, bond_symbol, Resolution.Daily)
        self.bond_yield_values[bond_symbol] = []
        
        # price and performance data needed
        symbols_needed = [currency_symbol, equity_symbol, bond_symbol]
        for symbol in symbols_needed:
            self.last_month_price[symbol] = None    
            self.perf_data[symbol] = RollingWindow[float](self.period)

    self.last_month_price[self.us_equities] = None    
    self.perf_data[self.us_equities] = RollingWindow[float](self.period)
    
    self.perf_data[self.us_bonds] = RollingWindow[float](self.period)
    self.bond_yield_values[self.us_bonds] = []

    self.recent_month = -1

def OnData(self, data):
    # store daily bond yields
    bond_yield_symbols = [x[1][1] for x in self.symbols.items()]
    for bond_symbol in bond_yield_symbols + [self.us_bonds]:
        if bond_symbol in data and data[bond_symbol]:
            self.bond_yield_values[bond_symbol].append(data[bond_symbol].Value)
    
    # rebalance once a month
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    
    if len(self.bond_yield_values[self.us_bonds]) == 0:
        return

    us_data_available = False
    
    # store monthly performance for us bonds and equities
    if self.Securities[self.us_equities].GetLastData() and (self.Time.date() - self.Securities[self.us_equities].GetLastData().Time.date()).days  0:
                    # reverse position if needed
                    if currency_symbol[-3:] == 'USD':
                        long.append(currency_symbol)
                    else:
                        short.append(currency_symbol)
                else:
                    # reverse position if needed
                    if currency_symbol[-3:] == 'USD':
                        short.append(currency_symbol)
                    else:
                        long.append(currency_symbol)
        
        self.bond_yield_values[bond_symbol] = []
    
    self.bond_yield_values[self.us_bonds] = []
    
    if self.IsWarmingUp:
        return
    
    # trade execution
    invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
            
    for symbol in long:
        self.SetHoldings(symbol, 1 / len(long))
    for symbol in short:
        self.SetHoldings(symbol, -1 / len(short))

def multiple_linear_regression(self, x:np.array, y:np.array):
    x = x.T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result

def bond_yield_equity_performance(self, bond_yield_values:np.array) -> float:
    x:np.array = 1+bond_yield_values[:-1]/100/250
    y:np.array = 7.7 * (bond_yield_values[:-1] - bond_yield_values[1:]) / 100
    z:np.array = x+y
    
    previous_equity:float = 1.0
    eq:list = [previous_equity]
    
    # calculate next equity value from the previous one
    for value in z:
        new_eq = value*previous_equity
        eq += [new_eq]
        previous_equity = new_eq
        
    performance:float = (eq[-1] / eq[0] - 1)
    return performance
