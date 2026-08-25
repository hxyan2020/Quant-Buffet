# Original QuantConnect / library Python
# locale=zh slug="卖空活动与动量效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from io import StringIO
from typing import List, Dict
from pandas.core.frame import DataFrame
from numpy import isnan
class ShortSellingActivityAndMomentum(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2017, 1, 1) # short interest data starts at 12-2017
    self.SetCash(100_000)
    
    self.tickers_to_ignore: List[str] = ['NE']
    self.data: Dict[Symbol, SymbolData] = {}
    
    self.weight: Dict[Symbol, float] = {} # storing symbols, with their weights for trading
    
    self.quantile: int = 4
    self.leverage: int = 5
    self.period: int = 6 * 21 # need 6 months of daily prices
    
    market: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    # source: https://www.finra.org/finra-data/browse-catalog/equity-short-interest/data
    text: str = self.Download('data.quantpedia.com/backtesting_data/economic/short_volume.csv')
    self.short_volume_df: DataFrame = pd.read_csv(StringIO(text), delimiter=';')
    self.short_volume_df['date'] = pd.to_datetime(self.short_volume_df['date']).dt.date
    self.short_volume_df.set_index('date', inplace=True)
    
    # self.fundamental_count: int = 1000
    # self.fundamental_sorting_key = lambda x: x.MarketCap
    self.selection_flag: bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the rolling window every day
    for stock in fundamental:
        symbol = stock.Symbol
        # store daily price
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    
    # monthly rebalance
    if not self.selection_flag:
        return Universe.Unchanged
    
    # check last date on custom data
    if self.Time.date() > self.short_volume_df.index[-1] or self.Time.date()  self.fundamental_count:
    #     selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    momentums: Dict[Symbol, float] = {} # storing stocks momentum
    market_cap: Dict[Symbol, float] = {} # storing stocks market capitalization
    # warmup price rolling windows
    for stock in selected:
        symbol: Symbol = stock.Symbol
        ticker: str = symbol.Value
        if symbol not in self.data:       
            # create SymbolData object for specific stock symbol
            self.data[symbol] = SymbolData(self.period)
            # get history daily prices
            history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes: Series = history.loc[symbol].close
            
            # store history daily prices into RollingWindow
            for _, close in closes.items():
                self.data[symbol].update(close)
           
        if ticker in self.short_volume_df.columns:
            if isnan(self.short_volume_df[self.short_volume_df.index  None:
    # rebalance montly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
       
def Selection(self) -> None:
    self.selection_flag = True
       
class SymbolData():
def __init__(self, period: int) -> None:
    self.closes: RollingWindow = RollingWindow[float](period)
    self.short_interest: Union[None, float] = None
    
def update(self, close: float) -> None:
    self.closes.Add(close)
    
def update_short_interest(self, short_interest_value: float) -> None:
    self.short_interest = short_interest_value
    
def is_ready(self) -> bool:
    return self.closes.IsReady and self.short_interest
    
def performance(self) -> float:
    closes: List[float] = [x for x in self.closes]
    return (closes[0] - closes[-1]) / closes[-1]
 
# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
