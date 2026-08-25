# Original QuantConnect / library Python
# locale=en slug="利用默顿规则进行收益率计算的市场时机选择"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
import data_tools
# endregion
class MarketTimingWithMertonRuleForEarningsYield(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1) 
    self.SetCash(100000)
    self.risk_aversion_coefficient: int = 2
    self.long_period: int = 10 * 12 + 1      # 10 years of daily data
    self.short_period: int = 2 * 12 + 1      # 2 years of daily data
    self.SetWarmup(self.long_period, Resolution.Daily)
    self.long_term_weight: float = 0.75
    self.short_term_weight: float = 0.25
    self.min_market_allocation: int = 0
    self.max_market_allocation: int = 1
    self.leverage: int = 5
    self.market_prices: RollingWindow = RollingWindow[float](self.long_period)
    self.sp_earnings_yield_value: Union[None, float] = None
    self.real_yield_value: Union[None, float] = None
    # traded symbols
    security: Securities = self.AddEquity('SPY', Resolution.Daily)
    security.SetLeverage(self.leverage)
    self.market:Symbol = security.Symbol
    
    security: Securities = self.AddEquity('TIP', Resolution.Daily)
    security.SetLeverage(self.leverage)
    self.bonds:Symbol = security.Symbol
    self.sp_earnings_yield: Symbol = self.AddData(data_tools.MonthlyCustomData, 'SP500_EARNINGS_YIELD_MONTH', Resolution.Daily).Symbol
    
    us_treasury_long_term: bool = True
    if us_treasury_long_term:
        self.real_yield: Symbol = self.AddData(data_tools.DailyCustomData, 'DLTIIT', Resolution.Daily).Symbol
        self.real_yield_property = 'LT Real Average (>10Yrs)'
    else:
        self.real_yield: Symbol = self.AddData(data_tools.DailyCustomData, 'DFII10', Resolution.Daily).Symbol
        self.real_yield_property = '10 YR'
    self.custom_data: List[Symbol] = [self.sp_earnings_yield, self.real_yield]
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.recent_month: int = -1
def OnData(self, data: Slice) -> None:
    custom_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.LastDateHandler.get_last_update_date()
    # rebalance monthly
    if self.recent_month != self.Time.month:
        self.recent_month = self.Time.month
        if all(self.Securities[symbol].GetLastData() for symbol in self.custom_data) and any(self.Time.date() > custom_data_last_update_date[symbol] for symbol in self.custom_data):
            self.Liquidate()
            return
        # update market prices
        if self.market in data and data[self.market]:
            price:float = data[self.market].Value
            self.market_prices.Add(price)
        if self.IsWarmingUp:
            return
        if self.sp_earnings_yield_value != None and self.real_yield_value != None and self.market_prices.IsReady \
            and self.market in data and self.bonds in data and data[self.market] and data[self.bonds]:
            excess_yield: float = self.sp_earnings_yield_value - self.real_yield_value
            vollatility_forecast: float = self.VolatilityForecast()
            
            # Merton Rule calculation
            market_allocation: float = excess_yield / (self.risk_aversion_coefficient * vollatility_forecast)
            
            # cap market allocation
            market_allocation: float = min(max(market_allocation, self.min_market_allocation), self.max_market_allocation)
            self.SetHoldings(self.market, market_allocation)
            self.SetHoldings(self.bonds, 1 - market_allocation)
        else:
            self.Liquidate()
        # reset data collected from previous month
        self.sp_earnings_yield_value = None
        self.real_yield_value = None
    if self.sp_earnings_yield in data and data[self.sp_earnings_yield] and data[self.sp_earnings_yield].Value != 0:
        self.sp_earnings_yield_value = data[self.sp_earnings_yield].Value / 100
    if self.real_yield in data and data[self.real_yield] and data[self.real_yield].Price != 0:
        self.real_yield_value = data[self.real_yield].Value / 100
def VolatilityForecast(self) -> float:
    # volatility measures, both expressed as variances, and then take the square root of that weighted average to arrive at the spot estimate of equity volatility
    prices: List[float] = list(self.market_prices)
    long_term_prices: np.ndarray = np.array(prices[:self.long_period])
    short_term_prices: np.ndarray = np.array(prices[:self.short_period])
    long_term_variance: float = self.Variance(long_term_prices)
    short_term_variance: float = self.Variance(short_term_prices)
    
    weighted_average: float = (self.long_term_weight * long_term_variance + self.short_term_weight * short_term_variance) / (self.long_term_weight + self.short_term_weight)
    
    # take the square root of the weighted average
    return np.sqrt(weighted_average)
def Variance(self, prices: np.ndarray) -> float:
    returns: np.ndarray = (prices[:-1] - prices[1:]) / prices[1:]
    ann_volatility: float = np.std(returns) * np.sqrt(12)
    variance: float = ann_volatility ** 2
    return variance
