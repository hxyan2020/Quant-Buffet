# Original QuantConnect / library Python
# locale=en slug="combination-of-the-long-term-and-the-short-term-reversal-in-china"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion

class CombinationoftheLongtermandtheShorttermReversalinChina(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.data:dict = {}
    self.quantity:dict[Symbol, int] = {}
    
    # https://www.tradingview.com/markets/stocks-hong-kong/market-movers-large-cap/
    self.tickers:list[str] = [
        '0700','1299','3690','9618','0883','0388','9633','1810','2388','1876',
        '0011','0016','1024','0066','0267','1109','0688','2020','0669','0981',
        '0003','0020','0001','0960','0002','2269','1113','2015','0027','2319',
        '2328','0012','0291','0316','0788','2313','1929','2057','2331','2382',
        '1928','1038','0968','0762','6618','2618','0881','1972','0006','2688',
        '1997','0175','1821','1093','6098',
        # NOTE price data error exclusion
        # '1913','2007','6969','0151','9961',
        # '1177','0004','0017','0083','1308',
        # '0992','1378','0322','3692','6823',
        '0868','6186','3323','1209','0101','2638','0586','3800','0836','0270',
        '1179','6862','0288','1193','0019','0656','0135','2066','1099','0384',
        '3799','9889','0916','0241','1359','0144','0489','3311','1044','0268'
    ]

    # long and short term period
    self.st_period:int = 3 * 21
    self.st_period_skip:int = 1 * 21
    self.lt_period:int = 36 * 21
    self.lt_period_skip:int = 13 * 21
    self.quantile:int = 10
    self.max_missing_days = 5

    self.SetWarmup(self.lt_period, Resolution.Daily)

    for ticker in self.tickers:
        # price data
        data = self.AddData(ChineseStock, ticker, Resolution.Daily)
        data.SetLeverage(10)
        data.SetFeeModel(CustomFeeModel())

        self.data[ticker] = SymbolData(self.lt_period)
    
    self.recent_month:int = -1

def OnData(self, data:Slice):
    # store daily prices
    for ticker in self.tickers:
        if ticker in data and data[ticker]:
            self.data[ticker].update_close(data[ticker].Value)

    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month

    lt_momentum:dict = { ticker : self.data[ticker].momentum(self.lt_period, self.lt_period_skip) for ticker in self.tickers if self.data[ticker].closes_are_ready() and (self.Time.date() - self.Securities[ticker].GetLastData().Time.date()).days = self.quantile:
        # both lt and st reversal strategy sorting
        sorted_by_lt_momentum:list = sorted(lt_momentum.items(), key = lambda x: x[1], reverse=True)
        self.vw_reversal_strategy_quantity(sorted_by_lt_momentum)
        
        sorted_by_st_momentum:list = sorted(st_momentum.items(), key = lambda x: x[1], reverse=True)
        self.vw_reversal_strategy_quantity(sorted_by_st_momentum)

    # trade execution
    invested:list = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in self.quantity:
            self.Liquidate(symbol)
            
    for symbol, q in self.quantity.items():
        self.MarketOrder(symbol, q)
        
    self.quantity.clear()

def vw_reversal_strategy_quantity(self, sorted_by_momentum:dict) -> None:
    quantile:int = int(len(sorted_by_momentum) / self.quantile)

    # long and short leg
    short:list = [x[0] for x in sorted_by_momentum[:quantile]]
    long:list = [x[0] for x in sorted_by_momentum[-quantile:]]
    
    # calculate weights and quantities
    w:float = 0.5 / len(short)
    for ticker in short:
        q:int = int(np.floor(-(self.Portfolio.TotalPortfolioValue * w) / self.data[ticker].closes[0]))
        if ticker not in self.quantity:
            self.quantity[ticker] = q
        else:
            self.quantity[ticker] += q

    w:float = 0.5 / len(long)
    for ticker in long:
        q:int = int(np.floor((self.Portfolio.TotalPortfolioValue * w) / self.data[ticker].closes[0]))
        if ticker not in self.quantity:
            self.quantity[ticker] = q
        else:
            self.quantity[ticker] += q
    
class SymbolData():
def __init__(self, max_momentum_period:int) -> None:
    self.closes = RollingWindow[float](max_momentum_period)
    
def update_close(self, close:float) -> None:
    self.closes.Add(close)
    
def closes_are_ready(self) -> bool:
    return self.closes.IsReady

def momentum(self, momentum_period:int, skip_period:int) -> float:
    performance:float = self.closes[skip_period - 1] / self.closes[momentum_period - 1] - 1
    return performance
    
# Custom fee model
class CustomFeeModel():
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))

class ChineseStock(PythonData):
''' https://finance.yahoo.com/ '''

def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/equity/hong_kong_stocks/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)

def Reader(self, config, line, date, isLiveMode):
    # Example Line Format:
    # 2003-03-12;590.3811645507812

    data = ChineseStock()
    data.Symbol = config.Symbol

    if not line[0].isdigit(): return None

    split = line.split(';')
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    data.Value = float(split[1])

    return data
