# Original QuantConnect / library Python
# locale=zh slug="参考价格与坏消息"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
import statsmodels.api as sm
import data_tools
from pandas.core.frame import DataFrame
class ReferencePricesAndBadNews(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.data:Dict[Symbol, data_tools.SymbolData] = {} # storing SymbolData objects under stocks symbols
    self.top_quintile:List[Symbol] = [] # storing stocks from top quintile by DPP
    self.bottom_quintile:List[Symbol] = [] # storing stocks from bottom quintile by DPP
    self.currently_not_traded:List[Symbol] = [] # storing symbols of currently not traded stocks
    self.currently_traded:List[Symbol] = [] # storing symbols of currently traded stocks
    self.managed_symbols:List[ManagedSymbol] = []
    
    self.short_period:int = 5 # need n of daily prices and volumes
    self.turnover_period:int = 250 # need n of weekly turnovers for DPP calculation
    self.long_period:int = 21 * 12 # need n of daily prices for market and stocks
    self.holding_period:int = 60 # stocks are held for n days
    self.traded_symbols:int = 50 # max value of currently traded stocks
    self.bad_news_ret_threshold:float = -0.02
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.quantile:int = 5
    self.leverage:int = 5
    
    self.market_prices:RollingWindow = RollingWindow[float](self.long_period) # storing daily market prices for regression
    
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update rolling windows each day
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        if symbol in self.data:
            # update stock price and volume
            self.data[symbol].update(stock.AdjustedPrice, stock.Volume)
            
            # get stock's EarningReports.BasicAverageShares.OneMonth in fine and update turnover
            if self.data[symbol].short_period_ready():
                self.data[symbol].update_turnover(stock.EarningReports.BasicAverageShares.ThreeMonths)
                self.data[symbol].update_week_performance()
        
        if symbol == self.symbol:
            # update market prices
            self.market_prices.Add(stock.AdjustedPrice)
    
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Symbol != self.symbol and \
        x.SecurityReference.ExchangeId in self.exchange_codes and not np.isnan(x.EarningReports.BasicAverageShares.ThreeMonths) and x.EarningReports.BasicAverageShares.ThreeMonths != 0]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    DPP:Dict[Symbol, float] = {}
    # warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData(self.short_period, self.long_period, self.turnover_period)
            # creating history for self.short_period,
            # because it can't perform turnover calculation without EarningReports.BasicAverageShares.OneMonth
            history:DataFrame = self.History(symbol, self.short_period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            
            closes:pd.Series = history.loc[symbol].close
            volumes:pd.Series = history.loc[symbol].volume
            
            for (_, close), (_, volume) in zip(closes.items(), volumes.items()):
                if close != 0:
                    self.data[symbol].update(close, volume)
        
        # get stock's EarningReports.BasicAverageShares.OneMonth in fine and update turnover
        if self.data[symbol].short_period_ready():
            # update stock's turnover and calculate week performance, if stock's data are ready
            self.data[symbol].update_turnover(stock.EarningReports.BasicAverageShares.ThreeMonths)
            self.data[symbol].update_week_performance()
        
        # check if stock's turnovers are ready
        if self.data[symbol].turnovers_ready() and self.selection_flag:
            DPP[symbol] = self.data[symbol].DPP_calculation()
    
    # change universe on monthly selection        
    if self.selection_flag:
        # keep monthly selection
        self.selection_flag = False
        
        if len(DPP)  None:
    # storing stock, which were hold for too long
    remove_managed_symbols:List[ManagedSymbol] = []
    
    # update holding period for each held stock and check if any of them is held for too long
    for managed_symbol in self.managed_symbols:
        # increase holding period
        managed_symbol.holding_period += 1
        
        # check if stock is held for too long
        if managed_symbol.holding_period == self.holding_period:
            remove_managed_symbols.append(managed_symbol)
            
    # liquidate stocks, which were held too long and remove them from self.managed_symbols dictionary
    for managed_symbol in remove_managed_symbols:
        if self.Portfolio[managed_symbol.symbol].Invested:
            self.MarketOrder(managed_symbol.symbol, -managed_symbol.quantity)
        self.managed_symbols.remove(managed_symbol)
    
    # market prices for regression aren't ready
    if not self.market_prices.IsReady:
        return
    
    market_prices:List[float] = list(self.market_prices)
    remove_from_curr_not_traded:List[Symbol] = []
    
    # check bad news days
    # firstly try to trade stocks, which aren't currently traded,
    # then try to trade stocks, which are currently traded, but they had bad news days 
    for symbol in self.currently_not_traded + self.currently_traded:
        # stock doesn't have data for regression or stock wasn't selected in monthly selection
        if not self.data[symbol].long_period_ready() and not self.data[symbol].short_period_ready() and (symbol in self.top_quintile or symbol in self.bottom_quintile):
            continue
        
        stock_prices:List[float] = [x for x in self.data[symbol].long_closes]
        
        # make regression
        regression_model = self.MultipleLinearRegression(market_prices, stock_prices)
        # get beta
        beta:float = regression_model.params[-1]
        
        # get daily performance
        stock_recent_perf:float = self.data[symbol].performance(2)
        market_recent_perf:float = market_prices[0] / market_prices[1] - 1 if market_prices[1] != 0 else 0
        implied_capm_return:float = market_recent_perf*beta
        # stock has bad news day and there is a space in portfolio for trading this stock
        if stock_recent_perf - implied_capm_return  None:
    self.selection_flag = True
