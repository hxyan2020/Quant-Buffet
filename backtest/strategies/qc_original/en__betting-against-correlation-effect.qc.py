# Original QuantConnect / library Python
# locale=en slug="betting-against-correlation-effect"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from typing import Dict, List
class BettingAgainstCorrelationEffect(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.leverage:int = 5
    self.quantile:int = 5
    self.min_share_price:int = 5
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.fundamental_count:int = 500
    self.quintile_internal_count:int = 10   # Pick n low corraleted stocks and n high corraleted stocks in each quintile.
    self.data:Dict[Symbol, RollingWindow] = {} # Storing daily prices
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.period:int = 21
    self.SetWarmUp(self.period)
    
    self.market_prices:RollingWindow = RollingWindow[float](self.period)
    
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    
    self.settings.daily_precise_end_time = False
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update Prices in RollingWindow
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].Add(stock.AdjustedPrice)
    
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and x.Market == 'usa'
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            continue
        self.data[symbol] = RollingWindow[float](self.period)
        history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet")
            continue
        closes:Series = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].Add(close)
            
    if not self.market_prices.IsReady:
        return Universe.Unchanged
    
    market_prices:List[float] = [x for x in self.market_prices]
    
    correlation:Dict[Symbol, float] = {}
    volatility:Dict[Symbol, float] = {}
    
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if not self.data[symbol].IsReady:
            continue
        closes:List[float] = [x for x in self.data[symbol]]
        volatility[symbol] = self.Volatility(closes)
        correlation[symbol] = np.correlate(closes, market_prices)
    # Volatility sorting
    sorted_by_vol:List[Symbol] = [x[0] for x in sorted(volatility.items(), key=lambda item: item[1], reverse=True)]
    quantile:int = int(len(sorted_by_vol)/self.quantile)
    
    # Group splitting
    volatility_groups:List[List[Symbol]] = [sorted_by_vol[x:x+quantile] for x in range(0, len(sorted_by_vol),quantile)]
    group_count:int = len(volatility_groups)
    
    # Long = array of arrays = groups by 10 stocks to long
    # Short = array of arrays = groups by 10 stocks to short
    for vol_group in volatility_groups:
        symbols:List[Symbol] = [x for x in vol_group]
        sorted_by_correlation:List[Symbol] = sorted(symbols, key = lambda x: correlation[x], reverse = True)
        
        # Go long stocks with highest correlations and short stocks with lowest correlation
        self.long.append([x for x in sorted_by_correlation][:self.quintile_internal_count])
        self.short.append([x for x in sorted_by_correlation][-self.quintile_internal_count:])
        
    long_short:List[Symbol] = []
    for group in self.long + self.short:
        for symbol in group:
            long_short.append(symbol)
            
    return long_short
    
def OnData(self, data: Slice) -> None:
    # store daily market price
    if self.symbol in data and data[self.symbol]:
        price:float = data[self.symbol].Value
        self.market_prices.Add(price)
        
    if not self.selection_flag:
        return
    self.selection_flag = False
    # Trade execution
    self.Liquidate()
    
    if len(self.long) == 0 or len(self.short) == 0:
        self.Liquidate()
        return
    long_length:int = len(self.long)
    short_length:int = len(self.short)
    
    equity_per_long_group:float = float(1 / long_length)
    equity_per_short_group:float = float(1 / short_length)
    
    for group in self.long:
        count:int = int(len(group))
        weight_index:float = 1 / sum([x for x in range(count+1)])
        for symbol in group:
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, equity_per_long_group * (count*weight_index))
                count -= 1
    for group in self.short:
        count = int(len(group))
        weight_index = 1 / sum([x for x in range(count+1)])
        count = 1
        for symbol in group:
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, -equity_per_short_group * (count*weight_index))
                count -= 1
        
    self.long.clear()
    self.short.clear()
def Selection(self) -> None:
    # Monthly rebalance
    self.selection_flag = True
    
def Volatility(self, values) -> float:
    values = np.array(values)
    returns = (values[:-1] - values[1:]) / values[1:]
    return np.std(returns)  
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
