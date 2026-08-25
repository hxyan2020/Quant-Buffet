# Original QuantConnect / library Python
# locale=en slug="pairs-trading-on-intraday-basis"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import itertools as it
from AlgorithmImports import *
from typing import List, Dict
import numpy as np
class PairsTradingIntradayBasis(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
   
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    # Daily price data.
    self.history_price:Dict[Symbol, RollingWindow] = {}
    self.formation_period:int = 264
    self.trading_period:int = 132
    self.period:int = 22
    self.leverage:int = 5
    self.min_share_price:int = 5
    
    self.overlapping_portfolios_count:int = 6  # 132 / 22 = 6
    self.overlapping_portfolios:List[Symbol] = []
    
    # Equally weighted brackets.
    self.max_traded_pairs:int = 5
    
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.fundamental_count:int = 100
    self.selection_hours:int = 1
    self.selection_flag:bool = True
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.UniverseSettings.Resolution = Resolution.Hour
    self.AddUniverse(self.FundamentalSelectionFunction)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
    for security in changes.RemovedSecurities:
        symbol:Symbol = security.Symbol
        if symbol in self.history_price:
            del self.history_price[symbol]
        
    symbols:List[Symbol] = [x for x in self.history_price.keys() if x != self.symbol]
    self.symbol_pairs:List[Tuple[Symbol]] = list(it.combinations(symbols, 2))
    
    # minimize the sum of squared deviations
    distances:Dict[Tuple[Symbol], float] = {}
    for pair in self.symbol_pairs:
        if self.history_price[pair[0]].IsReady and self.history_price[pair[1]].IsReady:
            distances[pair] = self.Distance(self.history_price[pair[0]], self.history_price[pair[1]])
    
    new_portfolio = TradedPortfolio(self)
    
    # sorting 5 pairs with no assets repetition
    if len(distances) != 0:
        sorted_pairs:List[Tuple[Tuple[Symbol], float]] = sorted(distances.items(), key = lambda x: x[1])
        sorted_pairs:List[Tuple[Symbol]] = [x[0] for x in sorted_pairs]
        
        # self.sorted_pairs.append(sorted_pairs[0])
        new_portfolio.add_pair(sorted_pairs[0])
        
        selected_assets:List[List[Symbol]] = [sorted_pairs[0][0], sorted_pairs[0][1]]
        
        for pair in sorted_pairs:
            symbol1:Symbol = pair[0]
            symbol2:Symbol = pair[1]
            
            # symbols which has not been selected yet
            if symbol1 not in selected_assets and \
                symbol2 not in selected_assets:
                    # self.sorted_pairs.append(pair)
                    new_portfolio.add_pair(pair)
                    selected_assets.extend([symbol1, symbol2])
                    
                    if len(new_portfolio.sorted_pairs) == self.max_traded_pairs:
                        break
    
    # liquidate firstly added portfolio
    if len(self.overlapping_portfolios) == self.overlapping_portfolios_count:
        item_to_remove:Symbol = self.overlapping_portfolios[0]
        result = item_to_remove.liquidate()
        if not result:
            self.Log('Nothing to liquidate or liquidation error')
        self.overlapping_portfolios.remove(item_to_remove)
    # append new portfolio
    self.overlapping_portfolios.append(new_portfolio)
    
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and x.Market == 'usa'
    ]
        
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        
        if symbol in self.history_price:
            continue
        
        self.history_price[symbol] = RollingWindow[float](self.formation_period)
        history:DataFrame = self.History(symbol, self.formation_period, Resolution.Hour)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet")
            continue
        closes:Series = history.loc[symbol].close
        for time, close in closes.items():
            self.history_price[symbol].Add(close)
            
    return [x.Symbol for x in selected if self.history_price[x.Symbol].IsReady]

def OnData(self, data: Slice) -> None:
    for symbol in self.history_price:
        symbol_obj:Symbol = self.Symbol(symbol)
        if symbol_obj in data and data[symbol_obj]:
            price:float = data[symbol_obj].Value
            self.history_price[symbol].Add(price)
                    
    if self.selection_hours == self.period:
        self.selection_flag = True
        self.selection_hours = 1
    else:
        self.selection_hours += 1
    
    # manage overlapping portfolios
    for portfolio in self.overlapping_portfolios:
        pairs_to_remove:List[Tuple[Symbol]] = []
        
        for pair in portfolio.sorted_pairs:
            if pair[0] not in self.history_price or pair[1] not in self.history_price:
                continue
            
            if not self.history_price[pair[0]].IsReady or not self.history_price[pair[1]].IsReady:
                continue
            
            # Calculate the spread of two price series.
            price_a:List[float] = [x for x in self.history_price[pair[0]]]
            price_b:List[float] = [x for x in self.history_price[pair[1]]]
            
            norm_a:np.ndarray = np.array(price_a) / price_a[-1]
            norm_b:np.ndarray = np.array(price_b) / price_b[-1]
            
            spread:np.ndarray = norm_a - norm_b
            mean:float = np.mean(spread)
            std:float = np.std(spread)
            actual_spread:float = spread[0]
            
            # Long-short position is opened when pair prices have diverged by two standard deviations.
            traded_portfolio_value = self.Portfolio.TotalPortfolioValue / self.overlapping_portfolios_count / self.max_traded_pairs
            if actual_spread > mean + 2*std or actual_spread  b stock's price
                            if a_price_norm > b_price_norm:
                                long_q:float = traded_portfolio_value / b_price    # long b stock
                                short_q:float = -traded_portfolio_value / a_price  # short a stock
                                if self.Securities.ContainsKey(symbol_a) and self.Securities.ContainsKey(symbol_b) and \
                                    self.Securities[symbol_a].Price != 0 and self.Securities[symbol_a].IsTradable and \
                                    self.Securities[symbol_b].Price != 0 and self.Securities[symbol_b].IsTradable:
                                    self.MarketOrder(symbol_a, short_q)
                                    self.MarketOrder(symbol_b, long_q)
                                    
                                    portfolio.traded_quantity[pair] = (short_q, long_q)
                                    portfolio.traded_pairs.append(pair)
                            # b stock's price > a stock's price
                            else:
                                long_q = traded_portfolio_value / a_price
                                short_q = -traded_portfolio_value / b_price
                                if self.Securities.ContainsKey(symbol_a) and self.Securities.ContainsKey(symbol_b) and \
                                    self.Securities[symbol_a].Price != 0 and self.Securities[symbol_a].IsTradable and \
                                    self.Securities[symbol_b].Price != 0 and self.Securities[symbol_b].IsTradable:
                                    self.MarketOrder(symbol_a, long_q)
                                    self.MarketOrder(symbol_b, short_q)
    
                                    portfolio.traded_quantity[pair] = (long_q, short_q)
                                    portfolio.traded_pairs.append(pair)
            # The position is closed when prices revert back.
            else:
                portfolio.liquidate_pair(pair)
def Distance(self, price_a:List[float], price_b:List[float]):
    # Calculate the sum of squared deviations between two normalized price series.
    price_a:List[float] = [x for x in price_a]
    price_b:List[float] = [x for x in price_b]
    
    norm_a:np.ndarray = np.array(price_a) / price_a[-1]
    norm_b:np.ndarray = np.array(price_b) / price_b[-1]
    return sum((norm_a - norm_b)**2)
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
class TradedPortfolio():
def __init__(self, algorithm):
    self.traded_pairs = []
    self.traded_quantity = {}
    self.sorted_pairs = []
    
    self.algorithm = algorithm

def add_pair(self, pair) -> None:
    self.sorted_pairs.append(pair)

def liquidate(self) -> bool:
    result = False
    for pair in self.traded_pairs:
        if pair in self.traded_quantity:
            self.algorithm.MarketOrder(pair[0], -self.traded_quantity[pair][0])
            self.algorithm.MarketOrder(pair[1], -self.traded_quantity[pair][1])
            result = True
    return result
def liquidate_pair(self, pair) -> None:
    if pair in self.traded_pairs and pair in self.traded_quantity:
        self.algorithm.MarketOrder(pair[0], -self.traded_quantity[pair][0])
        self.algorithm.MarketOrder(pair[1], -self.traded_quantity[pair][1])
        self.traded_pairs.remove(pair)
        del self.traded_quantity[pair]
