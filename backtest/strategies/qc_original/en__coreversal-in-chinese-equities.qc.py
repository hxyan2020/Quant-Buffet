# Original QuantConnect / library Python
# locale=en slug="coreversal-in-chinese-equities"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import SymbolData, CustomFeeModel, ChineseStocks
import numpy as np
from scipy import stats
# endregion

class CoreversalinChineseEquities(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    
    # chinese stock universe
    self.top_size_symbol_count:int = 500
    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/chinese_stocks/large_cap_500.csv')
    self.tickers:List[str] = ticker_file_str.split('\r\n')[:self.top_size_symbol_count]

    # trenching
    self.managed_queue:List[RebalanceQueueItem] = []
    self.holding_period:int = 12            # months

    # CoREV
    self.CoREV_period:int = 12
    self.CoREV_values:List[float] = []
    self.CoREV_quantile:int = 5
    self.quantile:int = 10

    self.period = 52 * 5                    # daily period
    self.data:dict[str, SymbolData] = {}    # symbol data
    self.value_weighted:bool = False        # True - value weighted; False - equally weighted
    self.leverage:int = 5

    self.SetWarmUp(self.period, Resolution.Daily)

    for t in self.tickers:
        data = self.AddData(ChineseStocks, t, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage)

        self.data[data.Symbol] = SymbolData(self.period)
    
    self.recent_month:int = -1

def OnData(self, data: Slice):
    performance:dict[Symbol, bool] = {}

    # store daily data
    for symbol, symbol_data in self.data.items():
        if data.ContainsKey(symbol):
            price_data:dict[str, str] = data[symbol].GetProperty('price_data')
            # valid price data
            if data[symbol].Value != 0. and price_data:
                # update price and market cap
                close:float = float(data[symbol].Value)
                symbol_data.update_price(close)

                mc:float = float(price_data['marketValue'])
                symbol_data.update_market_cap(mc)

                if symbol_data.is_ready():
                    if self.recent_month != self.Time.month and not self.IsWarmingUp:
                        perf:float = symbol_data.performance()
                        performance[symbol] = perf

    # rebalance monthly
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month

    if self.IsWarmingUp:
        return

    long:List[Symbol] = []
    short:List[Symbol] = []

    if len(performance) >= self.quantile:
        # sort by performance
        sorted_by_performance:List = sorted(performance.items(), key=lambda x: x[1], reverse=True)
        quantile:int = int(len(sorted_by_performance) / self.quantile)
        top_quantile:List[Symbol] = [x[0] for x in sorted_by_performance[:quantile]]
        bottom_quantile:List[Symbol] = [x[0] for x in sorted_by_performance[-quantile:]]

        total_pairwise_abnormal_correlations:float = 0
        for quantile in [top_quantile, bottom_quantile]:
            total_quantile_correlation:float = 0

            for symbol in quantile:
                # excess return of each stock
                stock_weekly_returns:np.ndarray = self.data[symbol].returns_for_period_n()

                # equal-weighted average excess return of the bottom (top) decile excluding stock i
                relevant_symbols:List[Symbol] = [x for x in quantile if x != symbol]
                if len(relevant_symbols) != 0:
                    quantile_ew_perf:float = np.mean(np.array([self.data[x].returns_for_period_n() for x in relevant_symbols]), axis=0)

                symbol_corr:float = np.corrcoef(stock_weekly_returns, quantile_ew_perf)[0, 1]

                total_quantile_correlation += symbol_corr
            
            # take the average of this sum
            total_quantile_correlation /= len(quantile)
            total_pairwise_abnormal_correlations += total_quantile_correlation
        
        # simple average of the average pairwise abnormal correlations in the loser decile and winner decile
        CoREV:float = total_pairwise_abnormal_correlations / 2
        if len(self.CoREV_values) >= self.CoREV_period:
            # if CoREV is at the month-end within its top quintile, buy the standard long-short reversal portfolio over the next year
            percentile:float = stats.percentileofscore(self.CoREV_values, CoREV) / 100
            top_percentile:float = 1 - (1 / self.CoREV_quantile)
            if percentile >= top_percentile:
                long = bottom_quantile
                short = top_quantile

        # append this month's corev value
        if CoREV != 0:
            # append this month's corev value
            self.CoREV_values.append(CoREV)
    
    if long and short:
        # calculate quantities for long and short trenche
        if self.value_weighted:
            total_market_cap_long:float = sum([self.data[x].recent_market_cap() for x in long])
            total_market_cap_short:float = sum([self.data[x].recent_market_cap() for x in short])
            
            long_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period
            short_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period
            
            long_symbol_q:List[tuple[Symbol, float]] = [(x, np.floor(long_w * (self.data[x].recent_market_cap() / total_market_cap_long) / data[symbol].Value)) for x in long]
            short_symbol_q:List[tuple[Symbol, float]] = [(x, -np.floor(short_w * (self.data[x].recent_market_cap() / total_market_cap_short) / data[symbol].Value)) for x in short]
            
            self.managed_queue.append(RebalanceQueueItem(long_symbol_q + short_symbol_q))
        else:
            long_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period / len(long)
            short_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period / len(short)
            
            long_symbol_q:List[tuple[Symbol, float]] = [(x, np.floor(long_w / data[x].Value)) for x in long]
            short_symbol_q:List[tuple[Symbol, float]] = [(x, -np.floor(short_w / data[x].Value)) for x in short]
            
            self.managed_queue.append(RebalanceQueueItem(long_symbol_q + short_symbol_q))
        
    # trade execution - rebalance portfolio
    remove_item:RebalanceQueueItem|None = None

    for item in self.managed_queue:
        # liquidate
        if item.holding_period == self.holding_period: # all portfolio parts are held for n months
            for symbol, quantity in item.opened_symbol_q:
                self.MarketOrder(symbol, -quantity)
                        
            remove_item = item
        
        # trade execution    
        if item.holding_period == 0: # all portfolio parts are held for n months
            opened_symbol_q:List[tuple[Symbol, float]] = []
            
            for symbol, quantity in item.opened_symbol_q:
                self.MarketOrder(symbol, quantity)
                opened_symbol_q.append((symbol, quantity))
                        
            # only opened orders will be closed        
            item.opened_symbol_q = opened_symbol_q
            
        item.holding_period += 1
        
    # need to remove closed part of portfolio after loop. Otherwise it will miss one item in self.managed_queue
    if remove_item:
        self.managed_queue.remove(remove_item)

class RebalanceQueueItem():
def __init__(self, symbol_q:List):
    # symbol/quantity collections
    self.opened_symbol_q:List[tuple[Symbol, float]] = symbol_q  
    self.holding_period:int = 0
