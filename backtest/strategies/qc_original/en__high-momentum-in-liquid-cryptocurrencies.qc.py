# Original QuantConnect / library Python
# locale=en slug="high-momentum-in-liquid-cryptocurrencies"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
import numpy as np
# endregion

class HighMomentuminLiquidCryptocurrencies(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.crypto_tickers:List[str] = ['BTCUSD', 'ETHUSD', 'SOLUSD', 'ADAUSD', 'XRPUSD', 'DOTUSD', 'DOGEUSD', 'LUNAUSD', 'AVAXUSD', 'UNIUSD',
                                    'LINKUSD', 'LTCUSD', 'BCHABCUSD', 'BSVUSD', 'FILUSD', 'XLMUSD', 'XTZUSD', 'NEOUSD', 'ATOMUSD', 'IOTAUSD', 
                                    'ETCUSD', 'DASHUSD', 'EGLDUSD', 'AAVEUSD', 'ENJUSD', 'EOSUSD', 'MKRUSD', 'MANAUSD', 'SNXUSD', 'FTTUSD', 
                                    'OMGUSD', 'SUSHIUSD', 'YFIUSD', 'WBTCUSD', 'XMRUSD', 'ZECUSD', 'ZRXUSD', 'XRAUSD', 'AMPLUSD', 'GRTUSD', 
                                    'DGBUSD', '1INCHUSD']

    self.data:Dict[Symbol, SymbolData] = {}

    self.week_periods:List[int] = [7, 14, 21]
    self.selection_flag:bool = False
    self.quantile:int = 5
    self.leverage:int = 2
    self.portion:float = .33
    self.percentage_traded:float = .2

    self.SetWarmup(self.week_periods[2], Resolution.Daily)

    # data subscription
    for ticker in self.crypto_tickers:
        data = self.AddCrypto(ticker, Resolution.Daily, Market.Bitfinex)
        data.SetLeverage(self.leverage)

        self.data[ticker] = SymbolData(self.week_periods[2])

    self.Schedule.On(self.DateRules.WeekEnd(self.market), self.TimeRules.BeforeMarketClose(self.market), self.Selection)

def OnData(self, data: Slice) -> None:
    # store daily prices
    for ticker in self.crypto_tickers:
        if ticker in self.data:
            if ticker in data and data[ticker]:
                self.data[ticker].update_price(data[ticker].Close, data[ticker].High)

    if self.IsWarmingUp: return

    if not self.selection_flag:
        return
    self.selection_flag = False
    
    hmom_by_period_long:Dict[int, List[Symbol]] = {}
    hmom_by_period_short:Dict[int, List[Symbol]] = {}

    # sort and divide into periods and quantiles
    for period in self.week_periods:
        hmom:dict[Symbol, float] = {}
        for ticker, item in self.data.items():
            if self.data[ticker].is_ready():
                hmom[ticker] = self.data[ticker].get_week_highmomentum(period)
                
        if len(hmom) >= self.quantile:
            sorted_hmom = sorted(hmom, key=hmom.get, reverse=True)
            quantile:int = len(sorted_hmom) // self.quantile
            hmom_by_period_long[period] = sorted_hmom[:quantile]
            hmom_by_period_short[period] = sorted_hmom[-quantile:]

    trade_quantities:Dict[Symbol, float] = {}

    # trade quantities calculation
    for i, hmom_lst in enumerate( [list(hmom_by_period_long.values()), list(hmom_by_period_short.values())] ):
        for lst in hmom_lst:
            for ticker in lst:
                if ticker in data and data[ticker]:
                    quantity:float = ((self.Portfolio.TotalPortfolioValue / len(lst)) * self.portion) // data[ticker].Price
                    if ticker not in trade_quantities:
                        trade_quantities[ticker] = 0

                    # long
                    if i == 0: trade_quantities[ticker] += quantity
                    # short
                    else: trade_quantities[ticker] -= quantity

    # trade execution
    stocks_invested:List[Symbol] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for ticker in stocks_invested:
        if ticker not in trade_quantities:
            self.Liquidate(ticker)

    for ticker, new_quantity in trade_quantities.items():
        if self.Portfolio[ticker].Invested:
            quantity:float = new_quantity * self.percentage_traded - self.Portfolio[ticker].Quantity
            if abs(quantity) >= 1.:
                self.MarketOrder(ticker, quantity)
        else:
            self.MarketOrder(ticker, new_quantity * self.percentage_traded)

def Selection(self) -> None:
    self.selection_flag = True

class SymbolData():
def __init__(self, period:int) -> None:
    self._period:int = period
    self._daily_price:RollingWindow = RollingWindow[float](period)
    self._high_price:RollingWindow = RollingWindow[float](period)

def update_price(self, price:float, high:float) -> None:
    self._daily_price.Add(price)
    self._high_price.Add(high)

def is_ready(self) -> bool:
    return self._daily_price.IsReady and self._high_price.IsReady

def get_week_highmomentum(self, period:int) -> float:
    prices:np.ndarray = np.array([x for x in self._daily_price])
    high:np.ndarray = np.array([x for x in self._high_price])
    return np.log(prices[0]) - np.log(max(high[:period]))
