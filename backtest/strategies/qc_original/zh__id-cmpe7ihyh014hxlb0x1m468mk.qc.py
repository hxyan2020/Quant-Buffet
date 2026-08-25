# Original QuantConnect / library Python
# locale=zh slug="结合商品市场中的动量、期限结构和特有波动性"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from collections import deque
class MomentumTermStructureIdiosyncraticVolatility(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.symbols = {
        "CME_S1"  : Futures.Grains.Soybeans,        # Soybean Futures, Continuous Contract #1
        "CME_W1"  : Futures.Grains.Wheat,           # Wheat Futures, Continuous Contract #1
        "CME_SM1" : Futures.Grains.SoybeanMeal,     # Soybean Meal Futures, Continuous Contract #1
        "CME_BO1" : Futures.Grains.SoybeanOil,      # Soybean Oil Futures, Continuous Contract #1
        "CME_C1"  : Futures.Grains.Corn,            # Corn Futures, Continuous Contract #1
        "CME_O1"  : Futures.Grains.Oats,            # Oats Futures, Continuous Contract #1
        
        "CME_LC1" : Futures.Meats.LiveCattle,       # Live Cattle Futures, Continuous Contract #1 
        "CME_FC1" : Futures.Meats.FeederCattle,     # Feeder Cattle Futures, Continuous Contract #1
        "CME_LN1" : Futures.Meats.LeanHogs,         # Lean Hog Futures, Continuous Contract #1 
        
        "CME_GC1" : Futures.Metals.Gold,            # Gold Futures, Continuous Contract #1 
        "CME_SI1" : Futures.Metals.Silver,          # Silver Futures, Continuous Contract #1 
        "CME_PL1" : Futures.Metals.Platinum,        # Platinum Futures, Continuous Contract #1 
        "CME_PA1" : Futures.Metals.Palladium,       # Palladium Futures, Continuous Contract 
        "CME_HG1" : Futures.Metals.Copper,          # Copper Futures, Continuous Contract
        # "CME_NG1" : Futures.Energies.NaturalGas,    # Natural Gas (Henry Hub) Physical Futures, Continuous Contract
        "CME_CL1" : Futures.Energies.CrudeOilWTI,   # Crude Oil Futures, Continuous Contract
        "ICE_O1"  : Futures.Energies.HeatingOil,    # Heating Oil Futures, Continuous Contract #1
        
        # "ICE_CC1" : Futures.Softs.Cocoa,            # Cocoa Futures, Continuous Contract 
        # "ICE_CT1" : Futures.Softs.Cotton2,          # Cotton No. 2 Futures, Continuous Contract
        # "ICE_KC1" : Futures.Softs.Coffee,           # Coffee C Futures, Continuous Contract
        # "ICE_OJ1" : Futures.Softs.OrangeJuice,      # Orange Juice Futures, Continuous Contract
        # "ICE_SB1" : Futures.Softs.Sugar11           # Sugar No. 11 Futures, Continuous Contract
    }
    
    self.data = {}
    self.chains = {}
    R = [1,3,6,12]
    self.period = R[2] * 21
    self.SetWarmUp(self.period)
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetLeverage(8)
        data.SetFeeModel(CustomFeeModel())
        future = self.AddFuture(self.symbols[symbol], Resolution.Minute)
        future.SetFilter(timedelta(0), timedelta(days = self.period))
        self.data[symbol] = SymbolData(symbol, str(self.symbols[symbol]), self.period)
    
    symbols = [x for x in self.symbols]      
    self.rebalance_flag: bool = False                  
    self.Schedule.On(self.DateRules.MonthStart(symbols[0]), self.TimeRules.At(0, 0), self.Rebalance)
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
def OnData(self, slice):
    for symbol in self.symbols:
        if self.securities[symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[symbol]:
            self.liquidate(symbol)
            self.data[symbol].History.clear()
            continue
        
        if symbol in slice and slice[symbol]:
            price = slice[symbol].Value
            self.data[symbol].Update(price)
    # Get futures chains 
    for chain in slice.FutureChains:
        if chain.Value.Contracts.Count  0 else 0.5 * float(near_contract.AskPrice + near_contract.BidPrice)
        price_distant = distant_contract.LastPrice if distant_contract.LastPrice > 0 else 0.5 * float(distant_contract.AskPrice + distant_contract.BidPrice)
        if distant_contract.Expiry == near_contract.Expiry:
            self.Debug("ERROR: Near and distant contracts have the same expiry!" + str(near_contract))
            return
        
        expire_range = 365 / (distant_contract.Expiry - near_contract.Expiry).days
        roll_returns[symbol] = (np.log(float(price_near)) - np.log(float(price_distant))) * expire_range

        for data in self.data.items():
            if data[1].Future == symbol:
                data[1].Roll_return = (np.log(float(price_near)) - np.log(float(price_distant))) * expire_range
    max_score = len(self.symbols)
    score = max_score
    # Return Sorting
    sorted_by_ret = sorted([x for x in self.data.items() if x[1].IsReady()], key=lambda x: x[1].Return(), reverse = True)
    sorted_by_ret = [x[0] for x in sorted_by_ret]
    for symbol in sorted_by_ret:
        self.data[symbol].Score += score
        score -= 1
    # Volatility Sorting
    sorted_by_vol = sorted([x for x in self.data.items() if x[1].IsReady()], key=lambda x: x[1].Volatility(), reverse = True)
    sorted_by_vol = [x[0] for x in sorted_by_vol]
    score = max_score
    for symbol in sorted_by_vol:
        self.data[symbol].Score += score
        score -= 1
    # Volatility Sorting
    sorted_by_roll = sorted([x for x in self.data.items() if x[1].IsReady()], key=lambda x: x[1].Roll_return, reverse = True)
    sorted_by_roll = [x[0] for x in sorted_by_roll]
    score = max_score
    for symbol in sorted_by_roll:
        self.data[symbol].Score += score
        score -= 1
    
    # Orders
    sorted_by_score = sorted([x for x in self.data.items() if x[1].IsReady()], key=lambda x: x[1].Score, reverse = True)
    top = sorted_by_score[:int(0.2 * len(self.symbols))]
    low = sorted_by_score[int(-0.2 * len(self.symbols)):]
    
    top = [x[0] for x in top]
    low = [x[0] for x in low]
    
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([top, low]):
        for symbol in portfolio:
            if slice.contains_key(symbol) and slice[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / (len(top) + len(low))))
    
    self.SetHoldings(targets, True)
def Rebalance(self):
    self.rebalance_flag = True
class SymbolData():
def __init__(self, symbol, future, lookback):
    self.Symbol = symbol
    self.Future = future
    self.History = deque(maxlen=lookback)
    self.Close = 0.0
    self.Roll_return = 0.0
    self.Score = 0
    
def IsReady(self):
    return len(self.History) == self.History.maxlen

def Update(self, value):
    self.Close = float(value)
    self.History.append(float(value))
def Return(self):
    prices = np.array(self.History)
    return (prices[-1]-prices[0])/prices[0]
    
def Volatility(self):
    prices = np.array(self.History)
    returns = (prices[1:]-prices[:-1])/prices[:-1]
    return np.std(returns)

def __str__(self):
    return self.Symbol + " " + self.Future + " Ret: " + str(self.Return()) + " Vol: " + str(self.Volatility()) + " Roll Ret: " + str(self.Roll_return)
# Quantpedia data
class QuantpediaFutures(PythonData):
_last_update_date:Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return QuantpediaFutures._last_update_date
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("http://data.quantpedia.com/backtesting_data/futures/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaFutures()
    data.Symbol = config.Symbol
    
    try:
        if not line[0].isdigit(): return None
        split = line.split(';')
        
        data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
        data['settle'] = float(split[1])
        data.Value = float(split[1])
    except:
        return None
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
