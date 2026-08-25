# Original QuantConnect / library Python
# locale=en slug="52周高点效应在股票中的应用"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from numpy import floor
from AlgoLib import *
from typing import List, Dict, Tuple

class Weeks52HighEffectinStocks(XXX):

def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.SetSecurityInitializer(lambda x: x.SetMarketPrice(self.GetLastKnownPrice(x)))
    
    self.period:int = 12 * 21

    # Tranching.
    self.holding_period:int = 3
    self.managed_queue:List[RebalanceQueueItem] = []
    self.industry_count:int = 6
    self.leverage:int = 5
    self.selection_sorting_key = lambda x:x.MarketCap

    # Daily 'high' data.
    self.data:Dict[Symbol, SymbolData] = {}
    
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.fundamental_count:int = 500
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)

def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        if symbol in self.data:
            # Store daily price.
            self.data[symbol].update(stock.AdjustedPrice)
        
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0 and \
                                ((x.SecurityReference.ExchangeId == "NYS") or (x.SecurityReference.ExchangeId == "NAS") or (x.SecurityReference.ExchangeId == "ASE"))]

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.selection_sorting_key, reverse=True)[:self.fundamental_count]]

    group:Dict[MorningstarIndustryGroupCode, float] = {}

    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(symbol, self.period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes:pd.Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
            
        if not self.data[symbol].is_ready():
            continue

        industry_group_code:MorningstarIndustryGroupCode = stock.AssetClassification.MorningstarIndustryGroupCode
        if industry_group_code == 0: continue
        
        # Adding stocks in groups.
        if industry_group_code not in group:
            group[industry_group_code] = []
        
        max_high:float = self.data[symbol].maximum()
        price:float = self.data[symbol].get_latest_price()
        
        stock_prilag:float = (stock, price / max_high)
        group[industry_group_code].append(stock_prilag)
    
    top_industries:List[MorningstarIndustryGroupCode] = []
    low_industries:List[MorningstarIndustryGroupCode] = []
    
    if len(group) != 0: 
        # Weighted average of ratios calc.
        industry_prilag_weighted_avg:Dict[int, float] = {}
        for industry_code in group:
            total_market_cap:float = sum([stock_prilag_data[0].MarketCap for stock_prilag_data in group[industry_code]])
            if total_market_cap == 0: continue
            industry_prilag_weighted_avg[industry_code] = sum([stock_prilag_data[1] * (stock_prilag_data[0].MarketCap / total_market_cap) for stock_prilag_data in group[industry_code]])
        
        if len(industry_prilag_weighted_avg) != 0:
            # Weighted average industry sorting.
            sorted_by_weighted_avg:List = sorted(industry_prilag_weighted_avg.items(), key=lambda x: x[1], reverse = True)
            top_industries = [x[0] for x in sorted_by_weighted_avg[:self.industry_count]]
            low_industries = [x[0] for x in sorted_by_weighted_avg[-self.industry_count:]]
    
    long:List[Symbol] = []
    short:List[Symbol] = []
    for industry_code in top_industries:
        for stock_prilag_data in group[industry_code]:
            symbol:Symbol = stock_prilag_data[0].Symbol
            long.append(symbol)
    
    for industry_code in low_industries:
        for stock_prilag_data in group[industry_code]:
            symbol:Symbol = stock_prilag_data[0].Symbol
            short.append(symbol)
            
    long_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period / len(long)
    short_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period / len(short)
    
    # symbol/quantity collection
    long_symbol_q:List[Tuple[Union[Symbol, int]]] = [(x, floor(long_w / self.data[x].get_latest_price())) for x in long]
    short_symbol_q:List[Tuple[Union[Symbol, int]]] = [(x, -floor(short_w / self.data[x].get_latest_price())) for x in short]
    
    self.managed_queue.append(RebalanceQueueItem(long_symbol_q + short_symbol_q))
    
    return long + short

def OnData(self, data:Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False

    remove_item:int = None
    
    # Rebalance portfolio
    for item in self.managed_queue:
        if item.holding_period == self.holding_period:
            # Liquidate
            for symbol, quantity in item.symbol_q:
                self.MarketOrder(symbol, -quantity)
            remove_item = item
        
        # Trade execution    
        if item.holding_period == 0:
            open_symbol_q:List[Tuple[Symbol, int]] = []
            
            for symbol, quantity in item.symbol_q:
                if symbol in data and data[symbol]:
                    self.MarketOrder(symbol, quantity)
                    open_symbol_q.append((symbol, quantity))
                        
            # Only opened orders will be closed        
            item.symbol_q = open_symbol_q
            
        item.holding_period += 1
        
    # We need to remove closed part of portfolio after loop. Otherwise it will miss one item in self.managed_queue.
    if remove_item:
        self.managed_queue.remove(remove_item)

def Selection(self) -> None:
    self.selection_flag = True

class RebalanceQueueItem():
def __init__(self, symbol_q:Tuple[Symbol, int]) -> None:
    # symbol/quantity collections
    self.symbol_q:Tuple[Symbol, int] = symbol_q  
    self.holding_period:int = 0

class SymbolData():
def __init__(self, symbol:Symbol, period:int) -> None:
    self.Symbol:Symbol = symbol
    self.Price:RollingWindow = RollingWindow[float](period)

def update(self, value:float) -> None:
    self.Price.Add(value)

def is_ready(self) -> bool:
    return self.Price.IsReady
 
def maximum(self) -> float:
    return max([x for x in self.Price])
    
def get_latest_price(self) -> float:
    return [x for x in self.Price][0]

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
