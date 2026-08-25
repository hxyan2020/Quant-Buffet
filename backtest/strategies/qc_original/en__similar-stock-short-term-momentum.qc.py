# Original QuantConnect / library Python
# locale=en slug="similar-stock-short-term-momentum"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class SimilarStockShortTermMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2002, 1, 1)
    self.SetCash(100000)
    
    self.data:Dict[Fundamental, SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}
    
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.nearest_const:int = 10 # selecting n nearest stocks, based on euclidean distance
    self.period:int = 21
    self.rebalance_month:int = 4
    self.quantile:int = 10
    self.leverage:int = 5
    self.min_share_price:float = 5.
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # daily updating of stock prices
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        if stock in self.data:
            self.data[stock].update(stock.AdjustedPrice)
    
    # rebalance monthly
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price > self.min_share_price and \
        not np.isnan(x.ValuationRatios.PBRatio) and x.ValuationRatios.PBRatio != 0 and \
        not np.isnan(x.FinancialStatements.IncomeStatement.EBIT.ThreeMonths) and x.FinancialStatements.IncomeStatement.EBIT.ThreeMonths != 0 and \
        not np.isnan(x.FinancialStatements.BalanceSheet.InvestmentsAndAdvances.ThreeMonths) and x.FinancialStatements.BalanceSheet.InvestmentsAndAdvances.ThreeMonths != 0 and \
        not np.isnan(x.MarketCap) and x.MarketCap != 0 and \
        x.MarketCap != 0 and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    stocks_data:List[StockData] = [] # storing stocks price, book to market, market cap, operation profit and investments
    highest_values:List[int] = [0, 0, 0, 0, 0] # storing biggest values of price, book to market, size, operation profit and investments 
    # warm up stock prices
    for stock in selected:
        symbol:Symbol = stock.Symbol
        
        if stock not in self.data:
            self.data[stock] = SymbolData(self.period)
            history = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                continue
            closes = history.loc[symbol].close
            for time, close in closes.items():
                self.data[stock].update(close)
        if self.data[stock].is_ready():
            # retrieve stock's data
            price:float = self.data[stock]._price
            book_to_market:float = 1 / stock.ValuationRatios.PBRatio
            size:float = stock.MarketCap
            operation_profit:float = stock.FinancialStatements.IncomeStatement.EBIT.ThreeMonths
            investments:float = stock.FinancialStatements.BalanceSheet.InvestmentsAndAdvances.ThreeMonths
            
            # keep storing biggest values 
            if highest_values[0] = len(stocks_data):
            break
        
        # retrieve stock's data based on index
        current_stock_data:StockData = stocks_data[index]
        curr_stock:Fundamental = current_stock_data._stock
        
        # create list for current stock euclidean distances
        if curr_stock not in euclidean_distances:
            euclidean_distances[curr_stock] = []
        
        # calculate euclidean distance with each stock, which is after current one in stocks data list
        for j in range(index + 1, len(stocks_data)):
            temp_stock_data:StockData = stocks_data[j]
            temp_stock:Fundamental = temp_stock_data._stock
            
            # create list for stocks euclidean distances
            if temp_stock not in euclidean_distances:
                euclidean_distances[temp_stock] = []
            
            # calculate stocks data difference and power them by 2
            price_diff_pow = (current_stock_data._price - temp_stock_data._price) ** 2
            book_to_market_diff_pow = (current_stock_data._book_to_market - temp_stock_data._book_to_market) ** 2
            size_diff_pow = (current_stock_data._size - temp_stock_data._size) ** 2
            operation_profit_diff_pow = (current_stock_data._operation_profit - temp_stock_data._operation_profit) ** 2
            investments_diff_pow = (current_stock_data._investments - temp_stock_data._investments) ** 2
            
            # calculate euclidean distance of differences of current stock data and temp stock data each powered by 2
            euclidean_distance_value = np.sqrt(price_diff_pow + book_to_market_diff_pow + size_diff_pow +
                                            operation_profit_diff_pow + investments_diff_pow)
            
            # append euclidean distance value and symbol of pair stock in dictionary keyed by stock symbol
            euclidean_dist_pair_symbol = [euclidean_distance_value, temp_stock]
            euclidean_distances[curr_stock].append(euclidean_dist_pair_symbol)
            
            # change symbol of temp_stock_data for symbol of current stock data in euclidean_dist_pair_symbol
            # and append it in dictionary list keyed by symbol of temp_stock_data
            euclidean_dist_pair_symbol = [euclidean_distance_value, curr_stock]
            euclidean_distances[temp_stock].append(euclidean_dist_pair_symbol)
    
    SIM:Dict[Fundamental, float] = {} # storing stock's total return of selected n nearest stocks keyed by stock's symbol
    
    # select top n nearest stocks and calculate their return
    for stock, dist_sym_list in euclidean_distances.items():  
        # create list of stock symbols sorted by euclidean distances
        sorted_by_dist_values:List = [x[1] for x in sorted(dist_sym_list, key=lambda item: item[0])]
        # select top n nearest stocks symbols
        nearest_stocks:List = sorted_by_dist_values[:self.nearest_const]
        
        total_return:float = 0.
        # calculate value weighted return of selected nearest stocks
        total_market_cap:float = sum([x.MarketCap for x in nearest_stocks])
        for temp_stock in nearest_stocks:
            total_return += (temp_stock.MarketCap / total_market_cap) * self.data[temp_stock].performance()
            
        # store stock's total return of selected n nearest stocks keyed by stock's symbol
        SIM[stock] = total_return
    
    long:List[Fundamental] = []
    short:List[Fundamental] = []
    if len(SIM) >= self.quantile:
        # sort stocks by their SIM values and perform decile selection
        quantile:int = int(len(SIM) / self.quantile)
        sorted_by_SIM:List[Fundamental] = [x[0] for x in sorted(SIM.items(), key=lambda item: item[1])]
        
        # portfolio goes long on the decile with the highest SIM and shorts the decile with the lowest SIM.
        long = sorted_by_SIM[-quantile:]
        short = sorted_by_SIM[:quantile]
        
        # calculate weights
        for i, portfolio in enumerate([long, short]):
            mc_sum:float = sum(map(lambda x: x.MarketCap, portfolio))
            for stock in portfolio:
                self.weight[stock.Symbol] = ((-1) ** i) * stock.MarketCap / mc_sum
    return list(self.weight.keys())
    
def OnData(self, data: Slice) -> None:
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    
class SymbolData():
def __init__(self, period: int):
    self._price:Union[None, float] = None
    self._closes:RollingWindow = RollingWindow[float](period)
    
def update(self, close: float) -> None:
    self._price = close
    self._closes.Add(close)
    
def is_ready(self) -> bool:
    return self._price and self._closes.IsReady
    
def performance(self) -> float:
    return self._closes[0] / self._closes[self._closes.Count - 1] - 1
    
class StockData():
def __init__(self, stock: Fundamental, price: float, book_to_market: float, size: float, operation_profit: float, investments: float):
    self._stock: float = stock
    self._price: float = price
    self._book_to_market: float = book_to_market
    self._size: float = size
    self._operation_profit: float = operation_profit
    self._investments: float = investments
            
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
