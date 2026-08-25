# Original QuantConnect / library Python
# locale=en slug="股票的动量波动率转换策略-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import pandas as pd
import numpy as np
from collections import deque
import data_tools
from numpy import isnan
from pandas.core.frame import DataFrame
from pandas.core.series import Series

class SwitchingbetweenValueMomentum(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']	
    self.ticker_to_ignore: List[str] = ['TOPS', 'SSCC']

    self.data: Dict[Symbol, SymbolData] = {}
    self.performance_data: DataFrame = pd.DataFrame()

    self.period: int = 120
    self.data_period: int = 12
    self.month_period: int = 21
    self.leverage: int = 5
    self.quantile: int = 10
    self.min_traded_weight: float = 0.00001
    self.short_momentum_period: int = 3
    self.long_momentum_period: int = 12

    self.short_term_long: List[Symbol] = []
    self.short_term_short: List[Symbol] = []
    self.long_term_long: List[Symbol] = []
    self.long_term_short: List[Symbol] = []

    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume

    self.selection_flag: bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged

    # update the rolling window every month
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        
        # store monthly price
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)

    selected: List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' \
                                and x.SecurityReference.ExchangeId in self.exchange_codes and x.Symbol.Value not in self.ticker_to_ignore]

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    short_term_momentum: Dict[Symbol, float] = {}
    long_term_momentum: Dict[Symbol, float] = {}

    # warmup price rolling windows
    for stock in selected:
        symbol: Symbol = stock.Symbol

        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData(self.data_period)
            history: DataFrame = self.History(symbol, self.data_period * self.month_period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            data: Series = history.loc[symbol]
            monthly_data: Series = data.groupby(pd.Grouper(freq='MS')).last()
            for time, row in monthly_data.iterrows():
                self.data[symbol].update(row.close)
        
        if self.data[symbol].is_ready():
            short_term_momentum[symbol] = self.data[symbol].momentum(self.short_momentum_period)
            long_term_momentum[symbol] = self.data[symbol].momentum(self.long_momentum_period)
    
    if len(short_term_momentum) >= self.quantile and len(long_term_momentum) >= self.quantile:
        # sorting by long term and short term momentum
        sorted_short_term_momentum: List[Symbol] = sorted(short_term_momentum, key = short_term_momentum.get, reverse=True)
        sorted_long_term_momentum: List[Symbol] = sorted(long_term_momentum, key = long_term_momentum.get, reverse=True)
        quantile: int = int(len(sorted_short_term_momentum) / self.quantile)

        self.short_term_long = sorted_short_term_momentum[:quantile]
        self.short_term_short = sorted_short_term_momentum[-quantile:]
        self.long_term_long = sorted_long_term_momentum[:quantile]
        self.long_term_short = sorted_long_term_momentum[-quantile:]
    
    return self.short_term_long + self.short_term_short + self.long_term_long + self.long_term_short

def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    if len(set(self.short_term_long + self.short_term_short)) == 0 or len(set(self.long_term_long + self.long_term_short)) == 0: 
        return

    portfolio_list: List[List[Symbol]] = [self.short_term_long, self.short_term_short, self.long_term_long, self.long_term_short]
    
    # optimization process
    price_data: List[Dict[Symbol, List[float]]] = [{ symbol : self.data[symbol].get_prices() for symbol in portfolio if symbol in data and data[symbol]} for portfolio in portfolio_list]
    returns_df_list: List[DataFrame] = [pd.DataFrame(portfolio_prices, columns=portfolio_prices.keys()).pct_change().dropna() for portfolio_prices in price_data]

    # store factors' performance
    df_returns: DataFrame = pd.concat([(returns_df_list[0].sum(axis=1) - returns_df_list[1].sum(axis=1)), (returns_df_list[2].sum(axis=1) - returns_df_list[3].sum(axis=1))], axis=1)
    self.performance_data = pd.concat([self.performance_data, df_returns], axis=0)
    
    if len(self.performance_data.index)  self.min_traded_weight:
                    if symbol in data and data[symbol]:
                        quantity: float = ((self.Portfolio.TotalPortfolioValue / len(portfolio)) * w) // data[symbol].Price
                        if symbol not in trade_quantities:
                            trade_quantities[symbol] = 0
                        trade_quantities[symbol] += ((-1) ** n) * quantity

    # trade execution
    stocks_invested: List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in stocks_invested:
        if symbol not in trade_quantities:
            self.Liquidate(symbol)

    for symbol, new_quantity in trade_quantities.items():
        quantity:float = new_quantity - self.Portfolio[symbol].Quantity
        if abs(quantity) >= 1.:
            self.MarketOrder(symbol, quantity)

def Selection(self) -> None:
    self.selection_flag = True
