# Original QuantConnect / library Python
# locale=zh slug="etf的创建-赎回活动与收益可预测性"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
#endregion
class ETFCreationRedemptionActivityAndReturnPredictability(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2006, 1, 1) # etf data starts since 2006
    self.SetCash(100_000)
    
    self.spread_period: int = 21 # need n bid ask spread values for each ETF
    self.leverage: int = 5
    self.quantile: int = 5
    
    self.data: Dict[Symbol, SymbolData] = {}
    self.shares_outstanding: Dict[str, float] = {} 
    
    self.long: List[Symbol] = []
    self.short: List[Symbol] = []
    
    self.last_custom_data_date: datetime.date = datetime(1, 1, 1).date()
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/equity/etf_shares_outstanding.csv')
    lines: List[str] = csv_string_file.split('\r\n')
    
    # retrieve tickers from csv header
    self.etf_tickers: List[str] = lines[0].split(';')[1:]
    
    for etf_ticker in self.etf_tickers:
        self.shares_outstanding[etf_ticker] = {}
    
    for line in lines[1:]: # iterate through each line except header
        if line == '':
            continue
        
        split: List[str] = line.split(';')
        date: datetime.date = datetime.strptime(split[0], "%Y-%m-%d").date()
        shares_outstanding_values: float = split[1:]
        total_shares_outstanding_values: int = len(shares_outstanding_values)
        
        if date > self.last_custom_data_date:
            self.last_custom_data_date = date
        # load share outstanding data and index them by year, month then day
        for index in range(1, total_shares_outstanding_values, 1):
            # get share outstanding value for specific ticker
            shares_outstanding_value: float = float(shares_outstanding_values[index])
            
            # make sure stored value won't be zero
            if shares_outstanding_value == 0:
                continue
            
            # get etf ticker, which belongs to current share outstanding value
            etf_ticker: str = self.etf_tickers[index]
            
            if date not in self.shares_outstanding[etf_ticker]:
                self.shares_outstanding[etf_ticker][date] = shares_outstanding_value
    
    self.selection_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.BeforeMarketClose(market, 0), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # rebalance monthly    
    if not self.selection_flag:
        return Universe.Unchanged
    
    # filter ETFs universe
    selected: List[Fundamental] = [x for x in fundamental if x.Symbol.Value in self.etf_tickers]
    
    share_spread: Dict[Symbol, float] = {}
    bid_ask_avg_spread: Dict[Symbol, float] = {}
    
    for etf in selected:
        etf_symbol: Symbol = etf.Symbol
        
        # initialize SymbolData object for new etf symbol in data
        if etf_symbol not in self.data:
            self.data[etf_symbol] = SymbolData(self.spread_period)
        
        # make sure, data are ready    
        if not self.data[etf_symbol].are_data_ready():
            continue
        
        share_spread_value: float = self.GetShareSpread(etf_symbol.Value)
        
        # make sure there is valid share spread value
        if share_spread_value == None:
            continue
        
        bid_ask_avg_spread_value: float = self.data[etf_symbol].bid_ask_avg_spread()
        
        # store spreads
        share_spread[etf_symbol] = share_spread_value
        bid_ask_avg_spread[etf_symbol] = bid_ask_avg_spread_value
        
    # there has to be enough ETFs for quintile selections   
    if len(share_spread)  None:
    if self.time.date() > self.last_custom_data_date:
        self.liquidate()
        return
        
    for etf_symbol in self.data:
        if slice.contains_key(etf_symbol) and slice[etf_symbol]:
            bid: float = self.Securities[etf_symbol].BidPrice
            ask: float = self.Securities[etf_symbol].AskPrice
            
            self.data[etf_symbol].update_bid_ask_spread(bid, ask)
    
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if slice.contains_key(symbol) and slice[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()
    
def GetShareSpread(self, etf_ticker: str) -> float:
    current_date: datetime.date = self.Time.date()
    prev_month_date: datetime.date = current_date - relativedelta(months=1)
    
    # get indexed ETF's share oustanding from dictionary
    etf_shares_outstanding: float = self.shares_outstanding[etf_ticker]
    
    # make sure share outstanding values are ready for each day
    if current_date not in etf_shares_outstanding or prev_month_date not in etf_shares_outstanding:
        return None
        
    # get current share oustanding value
    curr_shares_outstanding: float = etf_shares_outstanding[current_date]
    
    # get prev month share outstanding value
    prev_shares_outstanding: float = etf_shares_outstanding[prev_month_date]
    
    # return share spread
    return (curr_shares_outstanding / prev_shares_outstanding) - 1
    
def Selection(self) -> None:
    self.selection_flag = True
    
class SymbolData():
def __init__(self, spread_period: int) -> None:
    self.bid_ask_spread: RollingWindow = RollingWindow[float](spread_period)
    
def update_bid_ask_spread(self, bid: float, ask: float) -> None:
    midpoint: float = (bid + ask) / 2
    spread: float = (ask - bid) / midpoint
    self.bid_ask_spread.Add(spread)
    
def are_data_ready(self) -> bool:
    return self.bid_ask_spread.IsReady
    
def bid_ask_avg_spread(self) -> float:
    bid_ask_spreads: List[float] = [x for x in self.bid_ask_spread]
    bid_ask_avg_spread: float = sum(bid_ask_spreads) / len(bid_ask_spreads)
    return bid_ask_avg_spread
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
