# Original QuantConnect / library Python
# locale=zh slug="中国a股市场的波动率效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import SymbolData, CustomFeeModel, ChineseStocks
import numpy as np
# endregion
class VolatilityEffectInTheChineseAShareMarket(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.data:dict[Symbol, SymbolData] = {}
    self.traded_weights:dict[Symbol, float] = {}
    
    self.value_weighted:bool = False    # True - value weighted; False - equally weighted
    self.period:int = 12 * 21 * 3       # Need three years of daily returns
    self.quantile:int = 10
    self.leverage:int = 5
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    
def OnSecuritiesChanged(self, changes) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    for stock in coarse:
        symbol:Symbol = stock.Symbol
        
        # updating RollingWindow every day
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Symbol] = [x.Symbol for x in coarse if x.HasFundamentalData and x.Symbol.Value not in ['SNP', 'KBSF', 'LLL']]
    
    return selected
def FineSelectionFunction(self, fine:List[FineFundamental]) -> List[Symbol]:
    # filter only chinese stocks with market capitalization
    fine = [x for x in fine if x.CompanyReference.BusinessCountryID == 'CHN' and x.MarketCap != 0]
    
    # exclude 80% of lowest stocks by MarketCap
    sorted_by_market_cap:List = sorted(fine, key = lambda x: x.MarketCap)
    top_by_market_cap:List[FineFundamental] = sorted_by_market_cap[int(len(sorted_by_market_cap) * 0.8):]
    
    volatility:dict[Symbol, float] = {}
    
    for stock in fine:
        symbol = stock.Symbol
        
        # NOTE: Due to time and memory complexity we put history in FineSelectionFunction.
        # We can filter chinese stocks only in this function. 
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history:pd.DataFrame = self.History(symbol, self.period, Resolution.Daily)
                
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
                
            closes = history.loc[symbol].close
            for time, close in closes.iteritems():
                self.data[symbol].update(close)
            
        if self.data[symbol].is_ready():
            volatility[stock] = self.data[symbol].volatility()
    long:List[FineFundamental] = []
    short:List[FineFundamental] = []
    if len(volatility) >= self.quantile:
        quantile:int = int(len(volatility) / self.quantile)
        sorted_by_volatility:List[FineFundamental] = [x[0] for x in sorted(volatility.items(), key = lambda item: item[1])]
        
        # The strategy takes a long position in the lowest decile and a short position in portfolios within the highest decile.
        long = sorted_by_volatility[:quantile]
        short = sorted_by_volatility[-quantile:]
    # weight calculation
    if self.value_weighted:
        total_market_cap_long:float = sum([x.MarketCap for x in long])
        total_market_cap_short:float = sum([x.MarketCap for x in short])
        for stock in long:
            self.traded_weights[stock.Symbol] = stock.MarketCap / total_market_cap_long
        for stock in short:
            self.traded_weights[stock.Symbol] = -stock.MarketCap / total_market_cap_short
    else:
        long_c:int = len(long)
        short_c:int = len(short)
        for stock in long:
            self.traded_weights[stock.Symbol] = 1 / long_c
        for stock in short:
            self.traded_weights[stock.Symbol] = -1 / short_c
    return list(self.traded_weights.keys())
def OnData(self, data:Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in stocks_invested:
        if symbol not in self.traded_weights:
            self.Liquidate(symbol)
    
    for symbol, w in self.traded_weights.items():
        self.SetHoldings(symbol, w)
    
    self.traded_weights.clear()
    
def Selection(self):
    self.selection_flag = True
    
class SymbolData():
def __init__(self, period):
    self.price = RollingWindow[float](period)

def update(self, value):
    self.price.Add(value)

def is_ready(self) -> bool:
    return self.price.IsReady
    
def volatility(self) -> float:
    closes = [x for x in self.price]
    
    # Monthly volatility calc.
    separete_months = [closes[x:x+21] for x in range(0, len(closes), 21)]
    monthly_returns = [(x[0] - x[-1]) / x[-1] for x in separete_months]
    return np.std(monthly_returns)  
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
