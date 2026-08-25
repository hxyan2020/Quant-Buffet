# Original QuantConnect / library Python
# locale=zh slug="etf成分股的选股"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from QC100UniverseSelectionModel import QC100UniverseSelectionModel
from collections import deque
from scipy import stats
class StockPickingETFConstituents(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.period:int = 21
    self.SetWarmup(self.period, Resolution.Daily)
    
    # Source: https://github.com/QuantConnect/Lean/blob/master/Algorithm.Framework/Selection/QC500UniverseSelectionModel.py
    self.UniverseSettings.Resolution = Resolution.Daily
    self.SetUniverseSelection(QC100UniverseSelectionModel(n_of_symbols = 100, select_every_n_months = 3))
    self.quantile:int = 10
    # daily price data
    self.data:dict[Symbol, deque] = {}
    self.market:Symbol = self.AddEquity('OEF', Resolution.Daily).Symbol
    
    self.day_holding_period:int = 40
    self.managed_queue:list[RebalanceQueueItem] = []
def OnSecuritiesChanged(self, changes):
    # newly added proxy S&P stocks
    for security in changes.AddedSecurities:
        symbol:Symbol = security.Symbol
        
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(10)
        if symbol not in self.data:
            self.data[symbol] = deque(maxlen = self.period)
    
    # delete removed S&P stock from data storage
    for security in changes.RemovedSecurities:
        symbol:Symbol = security.Symbol
        if symbol in self.data:
            del self.data[symbol]
def OnData(self, data) -> None:
    # store daily data for universe
    for symbol in self.data:
        if symbol in data and data[symbol]:
            price:float = data[symbol].Value
            volume:float = data[symbol].Volume
            self.data[symbol].append((price, volume))
    market_closes:list[float] = []
    trade_flag:bool = False
    
    # market etf data is ready
    if self.market in self.data and len(self.data[self.market]) == self.data[self.market].maxlen:
        market_closes = [x[0] for x in self.data[self.market]]
        volumes:list[float] = [x[1] for x in self.data[self.market]]
        volume_mean:float = np.mean(volumes)
        volume_std:float = np.std(volumes)
        
        recent_volume:float = volumes[-1]
        
        # volume spike has not occured
        if recent_volume > volume_mean + 3 * volume_std:
            # last day's return was negative
            last_day_return:float = market_closes[-1] / market_closes[-2] - 1
            if last_day_return = self.quantile:
            # beta sorting
            sorted_by_beta:list = sorted(stock_beta.items(), key = lambda x: x[1], reverse = True)
            quantile:int = int(len(sorted_by_beta) / self.quantile)
            long:list[Symbol] = [x[0] for x in sorted_by_beta[-quantile:]]
            
            long_w:float = self.Portfolio.TotalPortfolioValue / self.day_holding_period / len(long)
            long_symbol_q:list[tuple[Symbol, float]] = [(x, np.floor(long_w / self.data[x][-1][0])) for x in long]
            
            # append long portfolio to managed queue
            self.managed_queue.append(RebalanceQueueItem(long_symbol_q))
    
    # rebalance portfolio
    remove_item:RebalanceQueueItem = None
    for item in self.managed_queue:
        if item.holding_period == self.day_holding_period:
            for symbol, quantity in item.symbol_q:
                self.MarketOrder(symbol, -quantity)
                        
            remove_item = item
            
        elif item.holding_period == 0:
            open_symbol_q:list[tuple[Symbol, float]] = []
            
            for symbol, quantity in item.symbol_q:
                if symbol in data and data[symbol]:
                    self.MarketOrder(symbol, quantity)
                    open_symbol_q.append((symbol, quantity))
                        
            # only opened orders will be closed
            item.symbol_q = open_symbol_q
            
        item.holding_period += 1
        
    # we need to remove closed part of portfolio after loop. Otherwise it will miss one item in self.managed_queue
    if remove_item:
        self.managed_queue.remove(remove_item)
class RebalanceQueueItem():
def __init__(self, symbol_q:list) -> None:
    # symbol/quantity collections
    self.symbol_q:list[tuple[Symbol, float]] = symbol_q  
    self.holding_period:int = 0
    
# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
