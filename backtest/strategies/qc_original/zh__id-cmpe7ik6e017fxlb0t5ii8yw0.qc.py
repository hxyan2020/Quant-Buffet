# Original QuantConnect / library Python
# locale=zh slug="分析师日"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class AnalystDays(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100_000)
    
    self.equally_weighted_flag: bool = False     # False - VW; True - EW
    self.analyst_days: Dict[str, List[datetime.date]] = {}
    self.selected: List[Fundamental] = []
    self.tickers: List[str] = []
    self.market_cap:dict[Symbol, float] = {}
   
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.spy_future_symbol: Symbol = market
    
    self.opened_long_positions_period: Dict[Symbol, int] = {}      # opened long stock postions with holding period
    self.holding_period: int = 20   # n days of holding period
    self.leverage: int = 10
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/economic/analyst_days.csv')
    lines: List[str] = csv_string_file.split('\r\n')
    
    header: List[str] = lines[0].split(';')
    
    for ticker in header[1:]: # skip first column == date
        self.tickers.append(ticker)
    for line in lines[1:]: # skip header line
        if line == '':
            continue
        
        line: List[str] = line.split(';')
        
        # convert string to date
        str_date: str = line[0]
        date: datetime.date = datetime.strptime(str_date, '%d.%m.%Y').date()
        for index in range(1, len(line)): # skip date as a first value of the row
            # retrive ticker from list created based on csv header
            ticker: str = self.tickers[index - 1]
            
            if ticker not in self.analyst_days:
                self.analyst_days[ticker] = []
            
            # if analyst_day_flag == 1, then this company had analyst days
            analyst_day_flag: str = line[index]
            
            if analyst_day_flag == '1':
                # company had analyst days
                self.analyst_days[ticker].append(date)
    self.selection_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.BeforeMarketClose(market, 0), self.Selection)
    self.Schedule.On(self.DateRules.EveryDay(market), self.TimeRules.BeforeMarketClose(market, 1), self.ManageTrade)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # rebalance monthly
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    # select S&P500 stocks from fundamental based on ticker    
    self.selected = [
        x for x in fundamental 
        if x.MarketCap != 0 
        and x.Symbol.Value in self.analyst_days
    ]
    if self.equally_weighted_flag:
        self.selected_values = list(map(lambda stock: stock.Symbol, self.selected))
        return self.selected_values
    else:
        self.market_cap = { stock.Symbol : stock.MarketCap for stock in self.selected }
        return list(self.market_cap.keys())

def ManageTrade(self):
    # liquidate opened symbols
    symbols_to_remove: List[Symbol] = []
    rebalance_flag: bool = False
    
    for symbol in self.opened_long_positions_period:
        holding_period_remaining: int = self.opened_long_positions_period[symbol]
        if holding_period_remaining == 0:
            # remove stock from holdings
            symbols_to_remove.append(symbol)
        else:
            # decrement remaining holding period
            self.opened_long_positions_period[symbol] -= 1
    
    for symbol in symbols_to_remove:
        self.Liquidate(symbol)
        del self.opened_long_positions_period[symbol]
        rebalance_flag = True   # rebalance is required
    today: datetime.date = self.Time.date()
    long: List[Symbol] = [] # storing symbols of stocks of those companies that had analyst day
    
    # check if selected companies had analyst day
    for stock in self.selected:
        symbol: Symbol = stock.Symbol
        ticker: str = symbol.Value
        # make sure selected stock has analyst days data
        if ticker not in self.analyst_days:
            continue
        
        if today in self.analyst_days[ticker]:
            # store stock in opened postions selection
            self.opened_long_positions_period[symbol] = self.holding_period
            rebalance_flag = True   # rebalance is required
    
    # rebalance is required
    if rebalance_flag:
        # rebalance whole active selection
        if self.equally_weighted_flag:
            n: int = len(self.opened_long_positions_period)
            if n != 0:
                # rebalance whole trade selection
                for symbol in self.opened_long_positions_period:
                    price = self.Securities[symbol].Price
                    if price != 0:
                        self.SetHoldings(symbol, 1/n)
        else:
            total_cap: float = sum([self.market_cap[x] for x in self.opened_long_positions_period])
            for symbol in self.opened_long_positions_period:
                if symbol in self.market_cap:
                    self.SetHoldings(symbol, self.market_cap[symbol] / total_cap)

def Selection(self) -> None:
    self.selection_flag = True
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
