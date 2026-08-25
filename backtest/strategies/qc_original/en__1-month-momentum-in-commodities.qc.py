# Original QuantConnect / library Python
# locale=en slug="1-month-momentum-in-commodities"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class OneMonthMomentuminCommodities(QCAlgorithm):
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
    self.period = 21
    self.quantile = 5
    self.SetWarmUp(self.period)
    
    self.data = {}
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(5)
        
        self.data[symbol] = SymbolData(self, symbol, self.period)
    
    self.rebalance_flag: bool = False
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.At(0, 0), self.Rebalance)
    self.settings.minimum_order_margin_portfolio_percentage = 0.

def on_data(self, slice: Slice) -> None:
    if self.IsWarmingUp: return
    
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    # Return sorting
    performance = { x : self.data[x].roc.Current.Value for x in self.data if self.data[x].is_ready() and self.Securities[x].GetLastData() and self.Time.date() = self.quantile:
        sorted_by_return = sorted(performance.items(), key = lambda x: x[1], reverse = True)
        quintile = int(len(sorted_by_return) / self.quantile)
        long = [x[0] for x in sorted_by_return[:quintile]]
        short = [x[0] for x in sorted_by_return[-quintile:]]
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([long, short]):
        for symbol in portfolio:
            if symbol in slice and slice[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
def Rebalance(self):
    self.rebalance_flag = True
class SymbolData():
def __init__(self, algorithm, symbol, period:int) -> None:
    self.roc = algorithm.ROC(symbol, period, Resolution.Daily)
    self.algorithm = algorithm

def is_ready(self) -> bool:
    return self.roc.IsReady
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
