# Original QuantConnect / library Python
# locale=zh slug="印度的动量效应与低风险效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
#endregion
class MomentumAndLowRiskEffectsInIndia(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.data:dict = {}
    self.symbols:list[Symbol] = []
    
    self.period:int = 37 * 21 # 37 months of daily closes
    self.SetWarmUp(self.period, Resolution.Daily)
    
    self.sma:dict = {}
    self.sma_period:int = 200
    
    self.quantile:int = 5
    self.perf_period:int = 12
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    csv_string_file = self.Download('data.quantpedia.com/backtesting_data/equity/india_stocks/india_nifty_500_tickers.csv')
    line_split = csv_string_file.split(';')
    
    # NOTE: Download method is rate-limited to 100 calls (https://github.com/QuantConnect/Documentation/issues/345)
    for ticker in line_split[:99]:
        security = self.AddData(QuantpediaIndiaStocks, ticker, Resolution.Daily)
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(5)
    
        symbol:Symbol = security.Symbol
        self.symbols.append(symbol)
        self.data[symbol] = SymbolData(self.period)
        
        self.sma[symbol] = self.SMA(symbol, self.sma_period, Resolution.Daily)
    
    self.max_missing_days:int = 5
    self.recent_month:int = -1
def OnData(self, data):
    # store daily prices
    for symbol in self.symbols:
        if symbol in data and data[symbol]:
            price:float = data[symbol].Value
            if price != 0 and not np.isnan(price):
                self.data[symbol].update(price)
    
    if self.IsWarmingUp: return

    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    volatility:[Symbol, float] = {}
    performance:[Symbol, float] = {}
    # price_over_sma:[Symbol, bool] = {}
    
    for symbol in self.symbols:
        # prices are ready and data is still comming in
        if self.data[symbol].is_ready() and self.sma[symbol].IsReady:
            if self.Securities[symbol].GetLastData() and (self.Time.date() - self.Securities[symbol].GetLastData().Time.date()).days  self.sma[symbol].Current.Value)
    
    long:list[Symbol] = []
    short:list[Symbol] = []
    if len(performance) >= self.quantile and len(volatility) >= self.quantile:
        quantile:int = int(len(performance) / self.quantile)
        sorted_by_performance = sorted(performance.items(), key=lambda item: item[1], reverse=True)
        sorted_by_volatility = sorted(volatility.items(), key=lambda item: item[1], reverse=True)
        top_by_perf = [x[0] for x in sorted_by_performance[:quantile]]
        bottom_by_perf = [x[0] for x in sorted_by_performance[-quantile:]]
        
        top_by_vol = [x[0] for x in sorted_by_volatility[:quantile]]
        bottom_by_vol = [x[0] for x in sorted_by_volatility[-quantile:]]
        
        long = [x for x in top_by_perf if x in bottom_by_vol]
        short = [x for x in bottom_by_perf if x in top_by_vol]
    # trade execution
    long_count:int = len(long)
    short_count:int = len(short)
    stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in stocks_invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
    if long_count:
        self.Log(long_count)
    if short_count:
        self.Log(short_count)
    for symbol in long:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, 1 / long_count)
    
    for symbol in short:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, -1 / short_count)
    
class SymbolData():
def __init__(self, period:int) -> None:
    self.closes = RollingWindow[float](period)
    
def update(self, close:float) -> None:
    self.closes.Add(close)
    
def is_ready(self) -> bool:
    return self.closes.IsReady
def performance(self, months:int) -> float:
    return self.closes[21] / self.closes[months * 21-1] - 1
    
def volatility(self) -> float:
    closes:list[float] = [x for x in self.closes]
    closes:np.ndarray = np.array(closes)
    returns:np.ndarray = (closes[:-1] - closes[1:]) / closes[1:]
    vol:float = float(np.std(returns))
    # monthly_closes:np.array = np.array(closes[0::21])
    # monthly_returns:np.array = (monthly_closes[:-1] - monthly_closes[1:]) / monthly_closes[1:]
    # vol:float = np.std(monthly_returns)
    return vol
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
    
# Quantpedia data
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaIndiaStocks(PythonData):
def GetSource(self, config, date, isLiveMode):
    source = "data.quantpedia.com/backtesting_data/equity/india_stocks/india_nifty_500/{0}.csv".format(config.Symbol.Value)
    return SubscriptionDataSource(source, SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaIndiaStocks()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(',')
    
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    data['Price'] = float(split[1])
    data.Value = float(split[1])
        
    return data
