# Original QuantConnect / library Python
# locale=en slug="共偏态增强动量策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
from typing import List, Dict
import numpy as np
# endregion
class CoSkewnessEnhancedMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000) 
    self.market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.tickers_to_ignore:List[str] = ['KELYB']
    self.data:Dict[Symbol, SymbolData] = {}
    self.CS_wml:List[float] = []
    self.six_month_std:List[float] = []
    self.long:list[Symbol] = []
    self.short:list[Symbol] = []
    self.weight:float = 0.
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.quantile:int = 10
    self.leverage:int = 5
    self.month_period:int = 21
    self.period:int = 60
    self.six_month_period:int = 6 * self.month_period
    self.estimation_period:int = 6
    self.leverage_cap:float = 3.
    self.fundamental_count:int = 500
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)
def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetLeverage(self.leverage)
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the rolling window every day
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # store monthly price
        if symbol in self.data:
            self.data[symbol].update_data(stock.AdjustedPrice, self.Time.month)
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Symbol.Value not in self.tickers_to_ignore and x.MarketCap != 0 \
                                and x.SecurityReference.ExchangeId in self.exchange_codes]
    # selected:List[Fundamental] = [x
    #     for x in sorted([x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Symbol.Value not in self.tickers_to_ignore \
    #     and x.MarketCap != 0 \
    #     and x.SecurityReference.ExchangeId in self.exchange_codes],
    #     key = lambda x: x.DollarVolume, reverse = True)[:self.fundamental_count]]
    
    if len(selected) > self.fundamental_count:
        selected = sorted(selected, key=lambda x: x.DollarVolume, reverse=True)[:self.fundamental_count]
    selected:Dict[Symbol, Fundamental] = {x.Symbol: x for x in selected}
    # warmup price rolling windows
    for symbol in list(selected.keys()) + [self.market]:
        if symbol in self.data:
            continue
        
        self.data[symbol] = SymbolData(self.six_month_period, self.period)
        history:DataFrame = self.History(symbol, self.period * self.month_period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes:pd.Series = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].update_data(close, time.date().month)
    if len(selected) != 0:
        if self.data[self.market].is_ready():
            stock_momentum:Dict[Symbol, float] = {symbol: value.get_momentum() for symbol, value in self.data.items() if value.is_ready() and symbol in selected}
            if len(stock_momentum) >= self.quantile:
                sorted_momentum:List[Symbol] = sorted(stock_momentum, key=stock_momentum.get, reverse=True)
                quantile:int = len(sorted_momentum) // self.quantile
                self.long:List[Symbol] = sorted_momentum[:quantile]
                self.short:List[Symbol] = sorted_momentum[-quantile:]
            # mean calculation of monthly returns of selected portfolio
            winners_performance:np.ndarray = np.array([self.data[x].get_monthly_returns() for x in self.long if self.data[x].is_ready()], dtype=float)
            losers_performance:np.ndarray = np.array([self.data[x].get_monthly_returns() for x in self.short if self.data[x].is_ready()], dtype=float)
            winners_mean_performance:np.ndarray = np.mean(winners_performance, axis=0)
            losers_mean_performance:np.ndarray = np.mean(losers_performance, axis=0)
            
            market_monthly_returns:np.ndarray = np.array(self.data[self.market].get_monthly_returns(), dtype=float)
            # standard deviation calculation of daily returns over 6 months
            winners_daily_returns:np.ndarray = np.array([self.data[x].get_daily_returns() for x in self.long], dtype=float)
            losers_daily_returns:np.ndarray = np.array([self.data[x].get_daily_returns() for x in self.short], dtype=float)
            winners_daily_returns:float = np.mean(winners_daily_returns, axis=0)
            losers_daily_returns:float = np.mean(losers_daily_returns, axis=0)
            six_month_std:float = np.std(winners_daily_returns - losers_daily_returns)
            self.six_month_std.append(six_month_std)
            
            # CS WML calculation
            std_wml = np.std(winners_mean_performance - losers_mean_performance)
            std_market = np.std(market_monthly_returns)
            CS_wml = (np.cov(winners_mean_performance, market_monthly_returns ** 2)[0][1] - np.cov(losers_mean_performance, market_monthly_returns ** 2)[0][1]) / (std_wml * (std_market ** 2))
            self.CS_wml.append(CS_wml)
        
        # weight calculation
        if len(self.CS_wml) >= self.estimation_period and len(self.six_month_std) >= self.estimation_period:
            last_CS_wml:float = self.CS_wml[-1]
            last_std:float = self.six_month_std[-1]
            std_target:float = np.mean(self.six_month_std)
            CS_wml_target:float = np.mean(self.CS_wml)
            CS_range:float = max(self.CS_wml) - min(self.CS_wml)
            self.weight:float = (1 + ((CS_wml_target - last_CS_wml) / CS_range)) * (std_target / last_std)
            self.weight = min([self.leverage_cap, max([-self.leverage_cap, self.weight])])
    return self.long + self.short
def OnData(self, data:Slice) -> None:
    # monthly rebalance
    if not self.selection_flag:
        return
    self.selection_flag = False
    if self.weight > 0.:
        targets:List[PortfolioTarget] = []
        for i, portfolio in enumerate([self.long, self.short]):
            for symbol in portfolio:
                if symbol in data and data[symbol]:
                    targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio) * self.weight))
        
        self.SetHoldings(targets, True)
    else:
        self.Liquidate()
    
    self.long.clear()
    self.short.clear()
    self.weight = 0.
def Selection(self) -> None:
    self.selection_flag = True
class SymbolData():
def __init__(self, daily_period:int, monthly_period:int) -> None:
    self._month:int = -1
    self._previous_price:float|None = None
    self._daily_price:List[float] = []
    self._monthly_return:RollingWindow = RollingWindow[float](monthly_period)
    self._daily_returns:RollingWindow = RollingWindow[float](daily_period)

def update_data(self, price:float, month:int) -> None:
    if self._previous_price is None:
        self._previous_price = price
        return
    if self._month != month and len(self._daily_price) != 0:
        self.update_monthly_data()
    self._month = month
    daily_return:float = (price - self._previous_price) / self._previous_price
    self._daily_returns.Add(daily_return)
    self._previous_price = price
    self._daily_price.append(price)
def update_monthly_data(self) -> None:
    monthly_return:float = (self._daily_price[-1] - self._daily_price[0]) / self._daily_price[0]
    self._monthly_return.Add(monthly_return)
    self._daily_price.clear()
def get_momentum(self) -> float:
    if self._monthly_return[11] == 0:
        return 0.
    
    momentum:float = self._monthly_return[0] / self._monthly_return[11] - 1
    return momentum
def get_daily_returns(self) -> float:
    return list(self._daily_returns)
def get_monthly_returns(self) -> float:
    return list(self._monthly_return)
def is_ready(self) -> bool:
    return self._monthly_return.IsReady and self._daily_returns.IsReady and self._previous_price is not None
# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
