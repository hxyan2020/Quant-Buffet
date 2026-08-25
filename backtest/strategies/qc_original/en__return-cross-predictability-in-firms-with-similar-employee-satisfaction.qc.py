# Original QuantConnect / library Python
# locale=en slug="return-cross-predictability-in-firms-with-similar-employee-satisfaction"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from typing import List, Dict
from pandas.core.frame import DataFrame
from pandas.core.series import Series
from dataclasses import dataclass, field
#endregion
class ReturnCrossPredictabilityInFirmsWithSimilarEmployeeSatisfaction(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1) # First ES data are for 2009
    self.SetCash(100000)
    
    symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.holding_period: int = 12 # Holding portfolio for 12 months 
    self.invest_count: int = 5 # Long n stocks and short n stocks
    self.period: int = 21 # Storing n daily prices
    self.leverage: int = 5
    self.min_share_price: int = 5
    
    self.selected_stock_count: int = 2 # Calculate the value-weighted average of n stock over and under current stock
    
    self.select_current_stock: bool = True # If this flag is True, calculation of value-weighted average will include current stock too
    
    self.data: Dict[Symbol, SymbolData] = {} # Storing daily prices of stocks
    self.employee_satisfaction: Dict[str, Dict[int, float]] = {} # Storing stock's ratings for specific years
    
    self.managed_queue: List[RebalanceQueueItem] = []
    
    # Download companies ratings for each year
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/index/EMPLOYEE_SATISFACTION.csv')
    lines: List[str] = csv_string_file.split('\r\n')
    for line in lines[1:]: # Skip header
        line_split: List[str] = line.split(';')
        date: datetime.date = datetime.strptime(line_split[0], "%d.%m.%Y").date()
        
        company_ticker: str = line_split[1]
        rating: str = line_split[2]
        
        # Create dictionary for each company ticker
        if company_ticker not in self.employee_satisfaction:
            self.employee_satisfaction[company_ticker] = {}
        
        # Under company ticker and year store rating
        self.employee_satisfaction[company_ticker][date.year] = rating
        
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(symbol), self.TimeRules.AfterMarketOpen(symbol), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        
        # Store stock price if it is in universe
        if symbol.Value in self.employee_satisfaction and symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    
    # Rebalance monthly
    if not self.selection_flag:
        return Universe.Unchanged
    
    # Universe will be created based on stock tickers in self.employee_satisfaction
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.MarketCap != 0 
        and x.Market == 'usa' 
        and x.Symbol.Value in self.employee_satisfaction 
        and x.Price > self.min_share_price
        ]
    stock_ratings = {} # Storing objects of StockRatings
    market_cap: Dict[Symbol, float] = {} # Storing stocks market capitalization
    
    prev_year = self.Time.year - 1 # Getting stocks ratings for previous year
    
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol not in self.data:
            # Warmup RollingWindow with History for current stock symbol
            self.data[symbol] = SymbolData(self.period)
            history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
            # Continue only if history isn't empty
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            
            # Get and store stock's closes
            closes: Series = history.loc[symbol].close
            for _, close in closes.items():
                self.data[symbol].update(close)
        if not self.data[symbol].is_ready():
            continue
        # Check if stock has rating for previous year
        if prev_year in self.employee_satisfaction[symbol.Value]:
            # Get stock's rating for last year
            rating: str = self.employee_satisfaction[symbol.Value][prev_year]
            
            if rating not in stock_ratings:
                stock_ratings[rating] = StockRatings()
                
            # Add new stock's symbol to stocks dictionary
            stock_ratings[rating].stocks[symbol] = stock.MarketCap
            
            # Store stock's market capitalization
            market_cap[symbol] = stock.MarketCap
    
    # Sort stocks by thier ES ratings and stocks with same rating sort by market capitalization
    sorted_by_rating: List[Symbol] = self.SortStocks(stock_ratings)
    
    # Storing stocks value weight average
    value_weight_avg: Dict[Symbol, float] = {}
    
    # Exclude first and last n stocks
    for i in range(self.selected_stock_count, len(sorted_by_rating) - self.selected_stock_count):
        current_stock_symbol: Symbol = sorted_by_rating[i]
        
        # Select current stock, n stocks with smaller rating and n stocks with larger rating
        selected_stocks: List[Symbol] = sorted_by_rating[i-self.selected_stock_count:i+self.selected_stock_count + 1]
        # Calculate and store current stock's value weight average
        value_weight_avg[current_stock_symbol] = self.ValueWeightAverage(current_stock_symbol, selected_stocks, market_cap)
    
    # Sort stocks by value weight average
    sorted_by_value_weight_avg: List[Symbol] = [x[0] for x in sorted(value_weight_avg.items(), key=lambda item: item[1])]
    
    # Buy stocks of n firms, which have the best performing peers over the last period
    long: List[Symbol] = sorted_by_value_weight_avg[-self.invest_count:]
    # Short stocks of n firms, which have the worst-performing peers
    short: List[Symbol] = sorted_by_value_weight_avg[:self.invest_count]
    
    if len(long) != 0 and len(short) != 0:
        # Calculate portfolio weight for long and short part
        long_w = self.Portfolio.TotalPortfolioValue / self.holding_period / len(long)
        short_w = self.Portfolio.TotalPortfolioValue / self.holding_period / len(short)
        
        long_symbol_q = [(x, np.floor(long_w / self.data[x].last_price)) for x in long]
        short_symbol_q = [(x, -np.floor(short_w / self.data[x].last_price)) for x in short]
        
        self.managed_queue.append(RebalanceQueueItem(long_symbol_q + short_symbol_q))
    
    return long + short
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    remove_item: Union[None, RebalanceQueueItem] = None
    
    # Rebalance portfolio
    for item in self.managed_queue:
        if item.holding_period == self.holding_period: # All portfolio parts are held for n months
            for symbol, quantity in item.opened_symbol_q:
                self.MarketOrder(symbol, -quantity)
                        
            remove_item = item
        
        # Trade execution    
        if item.holding_period == 0: # All portfolio parts are held for n months
            opened_symbol_q: List[Tuple[Symbol, int]] = []
            
            for symbol, quantity in item.opened_symbol_q:
                if symbol in data and data[symbol]:
                    self.MarketOrder(symbol, quantity)
                    opened_symbol_q.append((symbol, quantity))
                        
            # Only opened orders will be closed        
            item.opened_symbol_q = opened_symbol_q
            
        item.holding_period += 1
        
    # We need to remove closed part of portfolio after loop. Otherwise it will miss one item in self.managed_queue.
    if remove_item:
        self.managed_queue.remove(remove_item)
    
def Selection(self) -> None:
    self.selection_flag = True
    
def SortStocks(self, stocks_ratings) -> List[Symbol]:
    sorting_result: List[Symbol] = []
    
    # Sort dictionary by key values
    sorted_by_rating: List[StockRatings] = [x[1] for x in sorted(stocks_ratings.items(), key=lambda item: item[0], reverse=True)]
    
    # Sort stocks with same rating by market capitalizations
    for value in sorted_by_rating:
        # Sort dictionary of stocks with same ratings by their market capitalization
        sorted_by_cap = [x[0] for x in sorted(value.stocks.items(), key=lambda item: item[1], reverse=True)]
        
        sorting_result += sorted_by_cap
        
    return sorting_result
    
def ValueWeightAverage(self, 
                    current_stock_symbol: Symbol, 
                    stocks: List[Symbol], 
                    market_cap: Dict[Symbol, float]) -> float:
    value_weights: List[float] = []
    # Sum total market capitalization of needed stocks
    total_cap: float = sum([market_cap[x] for x in stocks if x != current_stock_symbol or self.select_current_stock])
    
    for symbol in stocks:
        if symbol != current_stock_symbol or self.select_current_stock:
            # Calculate stock performance on whole period
            performance: float = self.data[symbol].performance()
            # Calculate current stock weight
            weight: float = market_cap[symbol] / total_cap
            # Calculate value weight return
            value_weights.append(weight * performance)
    
    # Return value-weighted average    
    return np.mean(value_weights)
    
@dataclass
class RebalanceQueueItem():
# symbol/quantity collections
opened_symbol_q: Symbol 
holding_period: float = 0
class StockRatings():
def __init__(self) -> None:
    self.stocks: Dict[str, int] = {}
    
class SymbolData():
def __init__(self, period: int) -> None:
    self.closes: RollingWindow = RollingWindow[float](period)
    self.last_price: Union[None, float] = None
    
def update(self, close: float) -> None:
    self.closes.Add(close)
    self.last_price = close
    
def is_ready(self) -> None:
    return self.closes.IsReady
    
def performance(self) -> float:
    closes: List[float] = [x for x in self.closes]
    return (closes[0] - closes[-1]) / closes[-1]
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
