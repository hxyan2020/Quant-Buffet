# Original QuantConnect / library Python
# locale=en slug="momentum-based-on-fractional-difference-filter"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
import numpy as np
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Tuple
from math import factorial, prod
from decimal import Decimal
# endregion

class MomentumBasedonFractionalDifferenceFilter(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.data:Dict[Symbol, float] = {}

    self.stocks_to_liquidate:List[data_tools.HoldingItem] = []
    self.traded_portfolio_portion:Dict[Symbol, float] = {}

    self.t:int = 252
    self.period:int = self.t * 5
    self.quantile:int = 5
    self.leverage:int = 25
    self.holding_period:int = 5
    self.fundamental_count:int = 50
    self.d:Decimal = Decimal(0.9)

    # pi and weights calculations
    self.pi_list:List[Decimal] = [ self.pi(i, self.d) for i in range(self.period) ]
    self.weights:List[Decimal] = [ self.w(np.array(list(range(self.period))), self.pi_list[i], i) for i in range(self.period) ]

    self.rebalance_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.EveryDay(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # store daily stock prices
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        if symbol in self.data:
            self.data[symbol].update_daily_return(stock.AdjustedPrice)

    selected:List[Symbol] = [x.Symbol
        for x in sorted([x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0 and \
            (x.SecurityReference.ExchangeId == 'NYS') or (x.SecurityReference.ExchangeId == 'NAS') or (x.SecurityReference.ExchangeId == 'ASE')],
            key = lambda x: x.DollarVolume, reverse = True)[:self.fundamental_count]]
    
    # price warmup and prediction
    predict_by_symbol:Dict[Symbol, float] = {}

    for symbol in selected:
        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData(self.period)

            # price warmup
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes:pd.Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update_daily_return(close)
        
        if self.data[symbol].is_ready():
            # prediction
            prices:List[float] = np.log(self.data[symbol].get_daily_prices())
            predict:float = - (self.weights[len(self.weights) - self.t] / self.t - 1) * Decimal(sum([ prices[i] - prices[len(self.weights) - self.t] for i in range(len(self.weights) - self.t + 1, len(self.weights) - 1) ])) \
                            + Decimal(sum([ (self.weights[i] + (self.weights[len(self.weights) - self.t] / (self.t - 1))) * Decimal(prices[i] - prices[len(self.weights) - 1]) for i in range(len(self.weights) - self.t + 1, len(self.weights) - 1) ]))
            predict_by_symbol[symbol] = predict

    # sort and divide into quantiles
    if len(predict_by_symbol) >= self.quantile:
        sorted_predicts:List[Symbol] = sorted(predict_by_symbol, key=predict_by_symbol.get, reverse=True)
        quantile:int = len(sorted_predicts) // self.quantile
        long = sorted_predicts[:quantile]
        short = sorted_predicts[-quantile:]

        for i, portfolio in enumerate([long, short]):
            for symbol in portfolio:
                self.traded_portfolio_portion[symbol] = ((-1) ** i) / len(portfolio) * (self.Portfolio.TotalPortfolioValue / self.holding_period)
                    
        self.rebalance_flag = True

    return selected

def OnData(self, data: Slice) -> None:
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False

    items_to_remove:List[data_tools.HoldingItem] = []

    # execute order and hold for holding period
    for item in self.stocks_to_liquidate:
        item._holding_period += 1
        if item._holding_period >= self.holding_period:
            self.MarketOrder(item._symbol, -item._quantity)
            items_to_remove.append(item)    

    # remove from collection
    for item in items_to_remove:
        self.stocks_to_liquidate.remove(item)    

    # execute order
    for price_symbol, portfolio_portion in self.traded_portfolio_portion.items():
        if price_symbol in data and data[price_symbol]:
            final_quantity:int = portfolio_portion // data[price_symbol].Price
            if portfolio_portion != 0:
                self.MarketOrder(price_symbol, final_quantity)
                self.stocks_to_liquidate.append(data_tools.HoldingItem(price_symbol, final_quantity))

    self.traded_portfolio_portion.clear()

def Selection(self) -> None:
    self.selection_flag = True

def w(self, price_dataset:np.ndarray, pi:Decimal, u:int) -> Decimal:
    result:Decimal = (np.sum((np.arange((len(price_dataset) - u - self.t + 1), len(price_dataset) - u)) * pi) / self.t) - self.pi((len(price_dataset) - u + 1), self.d) if u  Decimal:
    s_factorial:Decimal = Decimal(factorial(s))
    result:Decimal = Decimal(((-1) ** s) * (prod([ Decimal(d - i) / s_factorial for i in range(s-1) ])))
    return result
