# Original QuantConnect / library Python
# locale=en slug="trendfollowing-combined-with-momentum-in-commodity-futures"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
class TrendfollowingwithMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(1991, 1, 1)
    self.SetCash(100000)
    self.symbols = [
        "CME_S1",   # Soybean Futures, Continuous Contract
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
        "CME_DA1",  # Class III Milk Futures
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
        "ICE_SB1",  # Sugar No. 11 Futures, Continuous Contract
    ]
    self.winners = []
    self.losers = []
    self.data = {}
    self.period = 12*21
    self.SetWarmUp(self.period)
 
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetLeverage(10)
        data.SetFeeModel(CustomFeeModel())
        
        ma = self.SMA(symbol, 6*21, Resolution.Daily)
        self.data[symbol] = SymbolData(symbol, 60, self.period, ma)
    
    self.rebalance_flag: bool = False
    self.Schedule.On(self.DateRules.MonthEnd(self.symbols[0]), self.TimeRules.At(0, 0), self.Rebalance)

def OnData(self, data):
    for symbol, symbol_data in self.data.items():
        if self.securities[symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[symbol]:
            self.liquidate(symbol)
            symbol_data.History.reset()
            continue
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data.Keys:
            if data[symbol_obj]:
                price = data[symbol_obj].Value
                if price != 0:
                    self.data[symbol].Update(price)
    
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.winners, self.losers]):
        for symbol_data in portfolio:
            if symbol_data[1].Weight != 0:
                if symbol_data[0] in data and data[symbol_data[0]]:
                    targets.append(PortfolioTarget(symbol_data[0], ((-1) ** i) * symbol_data[1].Weight))
    self.SetHoldings(targets, True)
    self.winners.clear()
    self.losers.clear()
def Rebalance(self):
    # Return sorting
    return_values = []
    for data in self.data.items():
        if data[1].IsReady():
            return_values.append(data[1].Return())
    
    if len(return_values) == 0: return

    high_percentile = np.percentile(return_values, 75)
    low_percentile = np.percentile(return_values, 25)
    winners_by_ret = list(data for data in self.data.items() if data[1].IsReady() and data[1].Return() > high_percentile)
    losers_by_ret = list(data for data in self.data.items() if data[1].IsReady() and data[1].Return()  data[1].MA.Current.Value)
    self.losers = list(data for data in losers_by_ret if data[1].Price  bool:
    return self.History.IsReady
        
def Update(self, value: float):
    self.Price = value
    self.History.Add(float(value))

def Return(self) -> float:
    prices = [x for x in self.History]
    return prices[0] / prices[-1] - 1

def Volatility(self) -> float:
    prices = np.array([x for x in self.History])[-self.Volatility_lookback:]
    returns = prices[:-1] / prices[1:] - 1
    return np.std(returns) * np.sqrt(252)

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
