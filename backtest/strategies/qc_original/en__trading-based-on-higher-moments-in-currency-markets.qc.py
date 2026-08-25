# Original QuantConnect / library Python
# locale=en slug="trading-based-on-higher-moments-in-currency-markets"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
from dateutil.relativedelta import relativedelta
import data_tools
from enum import Enum
# endregion
class UniverseType(Enum):
QP_FUTURES = 1
FOREX = 2
class TradingbasedonHigherMomentsinCurrencyMarkets(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.universe_type: UniverseType = UniverseType.QP_FUTURES
    self.leverage: int = 5
    self.quantile: int = 3
    self.min_period: int = 3
    self.periods: List[int] = [12, 24, 36, 48, 60, 'all']
    self.moments: List[int] = [4, 6, 8, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    self.tickers: List[str] = [
        'CME_AD1', 'CME_BP1', 'CME_NE1',
        'CME_CD1', 'CME_SF1', 'CME_JY1'
    ]
    if self.universe_type == UniverseType.FOREX:
        self.tickers = [
            'AUDUSD', 'CHFUSD', 'EURUSD', 'GBPUSD', 'NZDUSD', 'USDCAD', 
            'USDCZK', 'USDDKK', 'USDHUF', 'USDJPY', 'USDMXN', 'USDNOK', 
            'USDPLN', 'USDSGD', 'USDZAR', 'USDSEK', 'USDTWD', 'USDTRY'
        ]
    self.data: Dict[Symbol, data_tools.SymbolData] = {}
    self.strategy_manager: data_tools.StrategyManager = data_tools.StrategyManager(self.periods, self.moments, self.min_period)
    for ticker in self.tickers:
        security = self.AddData(data_tools.QuantpediaFutures, ticker, Resolution.Daily) if self.universe_type == UniverseType.QP_FUTURES \
                else self.AddForex(ticker, Resolution.Daily, Market.Oanda)
        
        if self.universe_type == UniverseType.QP_FUTURES:
            security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        
        symbol: Symbol = security.Symbol
        self.data[symbol] = data_tools.SymbolData(symbol, self.periods, self.moments)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.recent_month: int = -1
def OnData(self, data: Slice) -> None:
    if self.universe_type == UniverseType.QP_FUTURES:
        qp_futures_last_update_date: Dict[Symbol, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()
    rebalance_flag: bool = False
    # store daily prices
    for symbol, symbol_data in self.data.items():
        if symbol in data and data[symbol]:
            symbol_data.update_price(data[symbol].Price)
    # monthly rebalance
    if self.recent_month != self.Time.month:
        self.recent_month = self.Time.month
        rebalance_flag = True
    if not rebalance_flag:
        return
    for symbol, symbol_data in self.data.items():
        if self.universe_type == UniverseType.QP_FUTURES:
            if self.Securities[symbol].GetLastData() and self.Time.date() > qp_futures_last_update_date[symbol]:
                self.Liquidate()
                return
        if symbol_data.is_ready():
            symbol_data.calculate_moments()
            symbol_data._daily_prices.clear()
        
        if symbol_data.moment_is_ready():
            symbol_data.compare_moments()
    avg_returns: List[Tuple[int, int, float]] = []
    if not all(symbol_data.strategy_is_ready() for _, symbol_data in self.data.items()):
        return
    for period in self.periods:
        for i, moment in enumerate(self.moments):
            # compare last higher moments with avereage of period
            if self.strategy_manager.is_ready():
                avg_returns.append((period, moment, self.strategy_manager.get_average_return(period, moment)))
            # sort strategies and divide into quantiles
            sorted_strategy: List[Tuple[List, List, float]] = sorted({symbol: symbol_data.get_moment(period)[i] for symbol, symbol_data in self.data.items()}.items(), key=lambda x: x[1])
            quantile: int = int(len(sorted_strategy) / self.quantile)
            long: List[Symbol] = [x[0] for x in sorted_strategy][:quantile]
            short: List[Symbol] = [x[0] for x in sorted_strategy][-quantile:]
            self.strategy_manager.update_data(period, moment, (long, short, sum([self.data[symbol].get_last_month_return() for symbol in long]) - sum([self.data[symbol].get_last_month_return() for symbol in short])))
    
    if len(avg_returns) >= len(self.periods) * len(self.moments):
        sorted_avg: List[Tuple[int, int, float]] = sorted(avg_returns, key=lambda x: x[2], reverse=True)
        period, moment, _ = sorted_avg[0]
        long: List[Symbol] = self.strategy_manager.get_long_symbols(period, moment)
        short: List[Symbol] = self.strategy_manager.get_short_symbols(period, moment)
        # order execution
        targets:List[PortfolioTarget] = []
        for i, portfolio in enumerate([long, short]):
            for symbol in portfolio:
                if symbol in data and data[symbol]:
                    targets.append(PortfolioTarget(symbol, (((-1) ** i) / len(portfolio)) * self.data[symbol].trade_direction))
        
        self.SetHoldings(targets, True)
