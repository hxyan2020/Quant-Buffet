# Original QuantConnect / library Python
# locale=en slug="股票中的持久动量策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from collections import deque
# endregion
class EnduringMomentuminStocks(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.market_symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.leverage:int = 5
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.min_share_price:float = 5.
    self.data:Dict[Symbol, RollingWindow] = {}
    self.momentum_period:int = 21
    self.quantile:int = 10
    self.monthly_period:int = 60             # “enduring” probability period
    self.value_weighted:bool = False         # True - value weighted; False - equally weighted
    self.consecutive_occurance_period:int = 6
    self.traded_symbol_count:int = 10
    self.skip_monthly_period:int = 6
    
    # trenching
    self.managed_queue:List[RebalanceQueueItem] = []
    self.holding_period:int = 6             # months
    self.monthly_winners:deque[List[Symbol]] = deque(maxlen=self.monthly_period)
    self.monthly_losers:deque[List[Symbol]] = deque(maxlen=self.monthly_period)
    self.required_exchanges:List[str] = ['NYS', 'NAS', 'ASE']
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.market_symbol), self.TimeRules.BeforeMarketClose(self.market_symbol), self.Selection)
def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the rolling window every day
    for stock in fundamental:
        symbol = stock.Symbol
        # store daily price
        if symbol in self.data:
            self.data[symbol].Add(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and \
        x.AdjustedPrice >= self.min_share_price and x.SecurityReference.ExchangeId in self.required_exchanges]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    # warmup price rolling windows
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            continue
        
        self.data[symbol] = RollingWindow[float](self.momentum_period)
        history = self.History(symbol, self.momentum_period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].Add(close)
        
    monthly_perf:Dict[Fundamental, float] = {
        stock: self.data[stock.Symbol][0] / self.data[stock.Symbol][self.momentum_period-1] - 1 for stock in selected if self.data[stock.Symbol].IsReady
    }
    losers:List[Symbol] = []
    winners:List[Symbol] = []
    market_cap:Dict[Symbol, float] = {}
    # sort by monthly performance
    if len(monthly_perf) >= self.quantile:
        sorted_by_perf:List = sorted(monthly_perf.items(), key=lambda x: x[1], reverse=True)
        quantile:int = int(len(monthly_perf) / self.quantile)
        winners = [x[0].Symbol for x in sorted_by_perf[:quantile]]
        losers = [x[0].Symbol for x in sorted_by_perf[-quantile:]]
        market_cap = { stock.Symbol : stock.MarketCap for stock in monthly_perf }
    # append this month's winners and losers
    self.monthly_winners.append(winners)
    self.monthly_losers.append(losers)
    long:List[Symbol] = []
    short:List[Symbol] = []
    if len(self.monthly_winners) == self.monthly_period and len(self.monthly_losers) == self.monthly_period:
        # get relevant winners and losers groups over the time from previous sixty to six months.
        relevant_monthly_winners_group:List[Symbol] = list(self.monthly_winners)[:(len(self.monthly_winners) - self.skip_monthly_period)]
        relevant_monthly_losers_group:List[Symbol] = list(self.monthly_losers)[:(len(self.monthly_losers) - self.skip_monthly_period)]
        # calculate the “enduring” probability
        winners_enduring_prob:Dict[Symbol, float] = {}
        losers_enduring_prob:Dict[Symbol, float] = {}
        for symbol in winners:
            n_of_occurance:float = 0.
            endurance_count:float = 0.
            for i, symbol_list in enumerate(relevant_monthly_winners_group):
                if symbol in symbol_list:
                    n_of_occurance += 1.
                    
                    # look at forward groups
                    lookahead_period_index:int = i + self.consecutive_occurance_period + 1 if i + self.consecutive_occurance_period + 1 = self.traded_symbol_count: 
            winners_sorted_by_prob:List = sorted(winners_enduring_prob.items(), key=lambda x: x[1], reverse=True)
            long = [x[0] for x in winners_sorted_by_prob[:self.traded_symbol_count]]
            
        if len(losers_enduring_prob) >= self.traded_symbol_count:
            losers_sorted_by_prob:List = sorted(losers_enduring_prob.items(), key=lambda x: x[1], reverse=True)
            short = [x[0] for x in losers_sorted_by_prob[:self.traded_symbol_count]]
    if long and short:
        # calculate quantities for long and short trenche
        if self.value_weighted:
            total_market_cap_long:float = sum([market_cap[x] for x in long])
            total_market_cap_short:float = sum([market_cap[x] for x in short])
            
            long_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period
            short_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period
            
            long_symbol_q:List[Tuple[Symbol, float]] = [(x, np.floor(long_w * (market_cap[x] / total_market_cap_long) / self.data[x][0])) for x in long]
            short_symbol_q:List[Tuple[Symbol, float]] = [(x, -np.floor(short_w * (market_cap[x] / total_market_cap_short) / self.data[x][0])) for x in short]
            
            self.managed_queue.append(RebalanceQueueItem(long_symbol_q + short_symbol_q))
        else:
            long_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period / len(long)
            short_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period / len(short)
            
            long_symbol_q:List[Tuple[Symbol, float]] = [(x, np.floor(long_w / self.data[x][0])) for x in long]
            short_symbol_q:List[Tuple[Symbol, float]] = [(x, -np.floor(short_w / self.data[x][0])) for x in short]
            
            self.managed_queue.append(RebalanceQueueItem(long_symbol_q + short_symbol_q))
    return long + short
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # trade execution - rebalance portfolio
    remove_item:Union[RebalanceQueueItem, None] = None
    for item in self.managed_queue:
        # liquidate
        if item.holding_period == self.holding_period: # all portfolio parts are held for n months
            for symbol, quantity in item.opened_symbol_q:
                self.MarketOrder(symbol, -quantity)
                        
            remove_item = item
        
        # trade execution    
        if item.holding_period == 0: # all portfolio parts are held for n months
            opened_symbol_q:List[Tuple[Symbol, float]] = []
            
            for symbol, quantity in item.opened_symbol_q:
                if symbol in data and data[symbol] and self.Securities[symbol].IsTradable:
                    self.MarketOrder(symbol, quantity)
                    opened_symbol_q.append((symbol, quantity))
                        
            # only opened orders will be closed        
            item.opened_symbol_q = opened_symbol_q
            
        item.holding_period += 1
        
    # need to remove closed part of portfolio after loop. Otherwise it will miss one item in self.managed_queue
    if remove_item:
        self.managed_queue.remove(remove_item)
def Selection(self) -> None:
    self.selection_flag = True
    
class RebalanceQueueItem():
def __init__(self, symbol_q:List):
    # symbol/quantity collections
    self.opened_symbol_q:List[Tuple[Symbol, float]] = symbol_q  
    self.holding_period:int = 0
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
