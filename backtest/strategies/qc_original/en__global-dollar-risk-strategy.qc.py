# Original QuantConnect / library Python
# locale=en slug="global-dollar-risk-strategy"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from scipy import stats
from AlgorithmImports import *
class GlobalDollarRiskStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols = [
                    "CME_AD1", # Australian Dollar Futures, Continuous Contract #1
                    "CME_CD1", # Canadian Dollar Futures, Continuous Contract #1
                    "CME_SF1", # Swiss Franc Futures, Continuous Contract #1
                    "CME_EC1", # Euro FX Futures, Continuous Contract #1
                    "CME_BP1", # British Pound Futures, Continuous Contract #1
                    "CME_JY1", # Japanese Yen Futures, Continuous Contract #1
                    "CME_NE1", # New Zealand Dollar Futures, Continuous Contract #1
                    "CME_MP1"  # Mexican Peso Futures, Continuous Contract #1
                    ]
    self.period = 21
    self.traded_count = 2
    self.regression_period = 24
    self.data = {}
    for symbol in self.symbols:
        # Currency futures data.
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(5)
        
        self.data[symbol] = SymbolData(self, symbol, self.period, self.regression_period)
        
        # Warmup data window.
        history = self.History(self.Symbol(symbol), self.period, Resolution.Daily)
        if not history.empty and 'back_adjusted' in history:
            # Prevent from adding the same value in the next step - OnData function.
            closes = [x for x in history.back_adjusted][:-1]
            for close in closes:
                self.data[symbol].update_price(close)   
            
    self.factor_period = 4 * 12
    self.dollar_factor_vector = RollingWindow[float](self.factor_period)
    
    self.rebalance_flag: bool = False
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.At(0, 0), self.Rebalance)

def OnData(self, data):
    for symbol in self.data:
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data.Keys:
            price = data[symbol_obj].Value
            self.data[symbol].update_price(price)

    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    dollar_factor_value = np.average([self.data[x].performance() for x in self.symbols if x in self.data and self.data[x].price_is_ready()])
    self.dollar_factor_vector.Add(dollar_factor_value)
    
    beta = {}
    
    for symbol in self.symbols:
        if self.securities[symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[symbol]:
            self.liquidate(symbol)
            self.data[symbol].Prices.reset()
            continue
        
        symbol_return = self.data[symbol].performance() if (symbol in self.data and self.data[symbol].price_is_ready()) else None
        cross_sectional_average = np.average([self.data[x].performance() for x in self.symbols if x in self.data and self.data[x].price_is_ready() and x != symbol])
        
        if symbol_return:
            self.data[symbol].update(symbol_return, cross_sectional_average)
                
            # Is dollar factor is not ready, there's no need to calculate betas yet.
            if not self.dollar_factor_vector.IsReady: continue
        
            if self.data[symbol].regression_is_ready():
                beta[symbol] = self.data[symbol].calculate_beta()
    
    # Dollar factor is ready.
    if self.dollar_factor_vector.IsReady:
        # Beta sorting.
        sorted_by_beta = sorted(beta.items(), key = lambda x: x[1], reverse = True)
        long = []
        short = []
        if len(sorted_by_beta) >= self.traded_count*2:
            high_by_beta = [x[0] for x in sorted_by_beta[:self.traded_count]]
            low_by_beta = [x[0] for x in sorted_by_beta[-self.traded_count:]]
            # Long or short decision based on dollar state.
            dollar_performances = [x for x in self.dollar_factor_vector]
            dollar_performance = dollar_performances[0]
            dollar_performance_mean = np.mean(dollar_performances[1:])
            dollar_performance_std = np.std(dollar_performances[1:])
            
            if dollar_performance  (1.5 * dollar_performance_std) + dollar_performance_mean:
                # Large fluctuation dollar state.            
                long = [x for x in low_by_beta]
                short = [x for x in high_by_beta]
            else:
                # Normal dollar state.
                long = [x for x in high_by_beta]
                short = [x for x in low_by_beta]
    
        # Trade execution.    
        targets: List[PortfolioTarget] = []
        for i, portfolio in enumerate([long, short]):
            for symbol in portfolio:
                if symbol in data and data[symbol]:
                    targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
        
        self.SetHoldings(targets, True)
def Rebalance(self):
    self.rebalance_flag = True
                
class SymbolData(object):
def __init__(self, algo, symbol, period, regression_period):
    self.algo = algo
    self.Symbol = symbol
    self.Period = period
    
    self.Prices = RollingWindow[float](period)
    
    self.SymbolReturns = RollingWindow[float](regression_period)
    self.CrossSectionalAverages = RollingWindow[float](regression_period)
def update_price(self, price):
    self.Prices.Add(price)

def price_is_ready(self):
    return self.Prices.IsReady

def performance(self):
    values = [x for x in self.Prices]
    return (values[0] / values[-1] - 1)

def update(self, symbol_return, cross_sectional_average):
    self.SymbolReturns.Add(symbol_return)
    self.CrossSectionalAverages.Add(cross_sectional_average)

def regression_is_ready(self):
    return self.SymbolReturns.IsReady and self.CrossSectionalAverages.IsReady

def calculate_beta(self):
    symbol_returns = [x for x in self.SymbolReturns][:-1]
    cross_sectional_averages = [x for x in self.CrossSectionalAverages][1:]
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(cross_sectional_averages, symbol_returns)
    return slope
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
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
