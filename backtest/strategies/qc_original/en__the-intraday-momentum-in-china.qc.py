# Original QuantConnect / library Python
# locale=en slug="the-intraday-momentum-in-china"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from numpy import floor
from typing import List, Dict
from pandas.core.frame import DataFrame
from pandas.core.series import Series
#endregion
class TheIntradayMomentumInChina(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100_000)
    
    self.tickers_to_ignore: List[str] = ['EVK']
    self.period: int = 12 * 21
    self.quantile: int = 10
    self.sort_chunk: float = 0.3
    self.leverage: int = 10
    self.traded_portion: float = 0.2
    self.data: Dict[Symbol, SymbolData] = {}
    self.weight: Dict[Symbol, float] = {}
    
    symbol: Symbol = self.AddEquity("SPY", Resolution.Minute).Symbol
    time_offset: int = 16
    
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(symbol), self.TimeRules.AfterMarketOpen(symbol), self.Selection)
    self.Schedule.On(self.DateRules.EveryDay(symbol), self.TimeRules.AfterMarketOpen(symbol, -time_offset), self.BeforeOpen)
    self.Schedule.On(self.DateRules.EveryDay(symbol), self.TimeRules.BeforeMarketClose(symbol, time_offset), self.BeforeClose)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected: List[Fundamental] = [
        x for x in fundamental
        if x.HasFundamentalData 
        and x.MarketCap != 0 
        and x.CompanyReference.BusinessCountryID == 'CHN'
        and x.Symbol.Value not in self.tickers_to_ignore
    ]
    selected_stocks = [x for x in sorted(selected, key=lambda x:x.MarketCap, reverse=True)][:int(len(selected) * self.sort_chunk)]
    market_cap: Dict[Symbol, float] = {}
    cum_intraday_returns: Dict[Symbol, float] = {}
    
    for stock in selected_stocks:
        symbol: Symbol = stock.Symbol
        
        if symbol not in self.data:
            # Collect opens and closes of stock
            self.data[symbol] = SymbolData(self.period)
            history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
            
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            
            closes: Series = history.loc[symbol].close
            opens: Series = history.loc[symbol].open
            
            for (_, close_price), (_, open_price) in zip(closes.items(), opens.items()):
                self.data[symbol].update(close_price, open_price)
            
        if self.data[symbol].is_ready():
            cum_intraday_returns[symbol] = self.data[symbol].cumulative_intraday_returns()
            market_cap[symbol] = stock.MarketCap
    
    if len(cum_intraday_returns)  None:
    if (self.Time.hour == 0 and self.Time.minute == 0):
        # Updating RollingWindow each day with new open and close price.
        for symbol in self.data:
            history: History = self.History(symbol, 1, Resolution.Daily)
            
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            
            close: Series = history.loc[symbol].close
            open: Series = history.loc[symbol].open
            
            for (_, close_price), (_, open_price) in zip(close.items(), open.items()):
                self.data[symbol].update(close_price, open_price)
    
def BeforeOpen(self) -> None:
    # open new positions
    for symbol, w in self.weight.items():
        if self.Securities[symbol].Price != 0 and self.Securities[symbol].IsTradable: 
            quantity = floor((1 * self.Portfolio.TotalPortfolioValue * w) * self.traded_portion / self.data[symbol].LastPrice)
            self.MarketOnOpenOrder(symbol, quantity)
                
def BeforeClose(self) -> None:
    # liquidate
    for symbol, w in self.weight.items():
        if self.Portfolio[symbol].Invested:
            quantity: int = self.Portfolio[symbol].Quantity
            self.MarketOnCloseOrder(symbol, -quantity)
def Selection(self):
    self.selection_flag = True
    
class SymbolData():
def __init__(self, period: int) -> None:
    self.Closes: RollingWindow = RollingWindow[float](period)
    self.Opens: RollingWindow = RollingWindow[float](period)
    self.LastPrice: float = 0.
    
def update(self, close_price: float, open_price: float) -> None:
    self.Closes.Add(close_price)
    self.Opens.Add(open_price)
    self.LastPrice = close_price
    
def update_opens(self, open_price: float) -> None:
    self.Opens.Add(open_price)

def update_closes(self, close_price: float) -> None:
    self.Closes.Add(close_price)
    
def is_ready(self) -> bool:
    return self.Closes.IsReady and self.Opens.IsReady
    
def cumulative_intraday_returns(self) -> float:
    closes: List[float] = [x for x in self.Closes]
    opens: List[float] = [x for x in self.Opens]
    intraday_returns: List[float] = [(close_price - open_price) / open_price for close_price, open_price in zip(closes, opens)]
    return sum(intraday_returns)
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
