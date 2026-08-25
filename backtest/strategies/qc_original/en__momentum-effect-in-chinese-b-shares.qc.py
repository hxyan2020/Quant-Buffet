# Original QuantConnect / library Python
# locale=en slug="momentum-effect-in-chinese-b-shares"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
class MomentumeffectinChineseBshares(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    # chinese stock universe
    self.top_size_symbol_count:int = 300
    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/chinese_stocks/large_cap_500.csv')
    self.tickers:List[str] = ticker_file_str.split('\r\n')[:self.top_size_symbol_count]
    self.period:int = 21 * 7    # Storing 7 months of daily closes
    self.skip_period:int = 21   # Skip this period in performance calculation
    self.quantile:int = 3
    # trenching
    self.managed_queue:List[RebalanceQueueItem] = []
    self.holding_period:int = 6             # months
    self.value_weighted:bool = True         # True - value weighted; False - equally weighted
    self.data:dict[str, data_tools.SymbolData] = {}    # symbol data
    self.leverage:int = 5
    self.SetWarmUp(self.period, Resolution.Daily)
    for t in self.tickers:
        data = self.AddData(data_tools.ChineseStocks, t, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        self.data[data.Symbol] = data_tools.SymbolData(self.period)
    
    self.recent_month:int = -1
def OnData(self, data: Slice):
    performances:dict[Symbol, bool] = {}
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
                        mc:float = symbol_data.recent_market_cap()
                        if mc != 0:
                            performances[symbol] = symbol_data.performance(self.skip_period)
    # rebalance monthly
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    if self.IsWarmingUp:
        return
    long:List[Symbol] = []
    short:List[Symbol] = []
    if len(performances) >= self.quantile:
        # sort by performance
        tercile:int = int(len(performances) / self.quantile)
        sorted_by_perf:List[Symbol] = [x[0] for x in sorted(performances.items(), key=lambda item: item[1])]
    
        long = sorted_by_perf[-tercile:]
        short = sorted_by_perf[:tercile]
    
    if long and short:
        # calculate quantities for long and short trenche
        if self.value_weighted:
            total_market_cap_long:float = sum([self.data[x].recent_market_cap() for x in long])
            total_market_cap_short:float = sum([self.data[x].recent_market_cap() for x in short])
            
            long_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period
            short_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period
            
            long_symbol_q:List[tuple[Symbol, float]] = [(x, np.floor(long_w * (self.data[x].recent_market_cap() / total_market_cap_long) / data[x].Value)) for x in long]
            short_symbol_q:List[tuple[Symbol, float]] = [(x, -np.floor(short_w * (self.data[x].recent_market_cap() / total_market_cap_short) / data[x].Value)) for x in short]
            
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
