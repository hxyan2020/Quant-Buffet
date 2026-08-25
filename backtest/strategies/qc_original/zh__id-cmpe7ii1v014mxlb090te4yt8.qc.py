# Original QuantConnect / library Python
# locale=zh slug="商品趋势跟随策略中的季节性"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import pandas as pd
from AlgorithmImports import *
import numpy as np
class SeasonalityWithinTrendFollowing(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(1990, 1, 1)
    self.SetCash(100000)
    
    self.symbols = ["CME_S1",   # Soybean Futures, Continuous Contract
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
                    # "CME_NG1",  # Natural Gas (Henry Hub) Physical Futures, Continuous Contract
                    "CME_PA1",  # Palladium Futures, Continuous Contract 
                    "CME_RR1",  # Rough Rice Futures, Continuous Contract
                    "ICE_RS1",  # Canola Futures, Continuous Contract
                    "ICE_GO1",  # Gas Oil Futures, Continuous Contract
                    "CME_RB2",  # Gasoline Futures, Continuous Contract
                    "CME_KW2",  # Wheat Kansas, Continuous Contract
                    "ICE_WT1",  # WTI Crude Futures, Continuous Contract
                    "ICE_CC1",  # Cocoa Futures, Continuous Contract 
                    "ICE_CT1",  # Cotton No. 2 Futures, Continuous Contract
                    "ICE_KC1",  # Coffee C Futures, Continuous Contract
                    "ICE_O1",   # Heating Oil Futures, Continuous Contract
                    "ICE_OJ1",  # Orange Juice Futures, Continuous Contract
                    "ICE_SB1"   # Sugar No. 11 Futures, Continuous Contract
                    ]
    self.period = 12 * 21
    self.quantile = 5
    self.SetWarmup(self.period)
    self.data = {}
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetLeverage(5)
        data.SetFeeModel(CustomFeeModel())
        
        self.data[symbol] = SymbolData(self.period, self)
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.At(0, 0), self.Rebalance)

def OnData(self, data):
    # Update RollingWindows in SymbolData object
    for symbol in self.symbols:
        if symbol in data and data[symbol]:
            price = data[symbol].Value
            self.data[symbol].update(price,self.Time.date())
                
def Rebalance(self):
    if self.IsWarmingUp: return

    month = self.Time.month
    
    # Thanks to this condition we make sure,
    # that montly return is stored under right month in SymbolData.months dictionary
    if month == 1:
        month = 12
    else:
        month -= 1
    
    positive_return = [] # Store futures with positive yearly return
    negative_return = [] # Store futures with negative yearly return
    for symbol in self.symbols:
        # If prices for whole year are ready, we can calculate yearly return
        if self.data[symbol].is_ready():
            # Firstly calculate, then store current monthly return in proper list
            self.MonthlyReturnStoring(symbol, month)
            
            # Based on yearly return store future symbol in proper list
            if self.data[symbol].yearly_return() > 0:
                positive_return.append(symbol)
            
            else:
                negative_return.append(symbol)
            
            
        elif self.data[symbol].are_monthly_prices_ready():
            # Firstly calculate, then store current monthly return in proper list
            self.MonthlyReturnStoring(symbol, month)
    
    # Seasonality sorting
    return_avg = {}
    custom_data_last_update_date: Dict[Symbol, datetime.date] = QuantpediaFutures.get_last_update_date()
  
    for symbol in self.symbols:
        if self.Securities[symbol].GetLastData() and self.Time.date() = self.quantile:
        # Create top and bottom list based on avg sort
        quintile = int(len(return_avg) / self.quantile)
        sorted_by_avg_return = [x[0] for x in sorted(return_avg.items(), key = lambda item: item[1], reverse = True)]
        
        top = sorted_by_avg_return[:quintile]
        bottom = sorted_by_avg_return[-quintile:]
        
        # Create long and short portfolio based on strategy description
        long = [x for x in positive_return if x not in bottom]
        short = [x for x in negative_return if x not in top]
            
    # Trade execution
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([long, short]):
        for symbol in portfolio:
            targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)

def MonthlyReturnStoring(self, symbol, month):
    # Calculate monthly return for current month
    monthly_return = self.data[symbol].monthly_return()
    
    # Store blank list under current monnth number, if it doesn't exists
    # Thanks to this list we are making history of monthly returns for each year
    if month not in self.data[symbol].months:
        self.data[symbol].months[month] = []

    # Add current monthly return into list of all montly returns in this month
    self.data[symbol].months[month].append(monthly_return)
        
class SymbolData():
def __init__(self, period, algorithm):
    self.monthly_prices = RollingWindow[float](21) # Storing prices for monthly return calculation
    self.prices = RollingWindow[float](period) # Storing daily prices of futures
    self.months = {} # Storing monthly returns in list for each month separately
    self.last_update_date = None
    self.algorithm = algorithm
    
def update(self, price, date):
    self.monthly_prices.Add(price)
    self.prices.Add(price)
    self.last_update_date = date
    
def is_ready(self):
    return self.prices.IsReady and ((self.algorithm.Time.date() - self.last_update_date).days  5:
        return True 
    else:
        return False
    
def monthly_return(self):
    prices = [x for x in self.monthly_prices]
    return (prices[0] - prices[-1]) / prices[-1]
    
def yearly_return(self):
    prices = [x for x in self.prices]
    return (prices[0] - prices[-1]) / prices[-1]
    
def get_avg_of_yield_returns(self, month):
    # Get all monthly returns for specific month
    monthly_returns = self.months[month]
    
    # We get average from max 10 values of monthly returns
    if len(monthly_returns) > 10:
        monthly_returns = monthly_returns[-11:]
        
    # The past year's same-month return is to be excluded from the seasonality calculation to avoid any correlation between the two signals
    monthly_returns = monthly_returns[:-1]
    # Return average of monthly returns in specific month
    return np.mean(monthly_returns)
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
_last_update_date:Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return QuantpediaFutures._last_update_date
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/futures/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaFutures()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['back_adjusted'] = float(split[1])
    data['spliced'] = float(split[2])
    data.Value = float(split[1])
    if config.Symbol.Value not in QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol.Value]:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = data.Time.date()
    
    return data
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
