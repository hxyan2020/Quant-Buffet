# Original QuantConnect / library Python
# locale=en slug="institutional-ownership-effect"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class InstitutionalOwnershipEffect(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100_000)
    
    self.dates: List[datetime.date] = []
    self.institutional_ownership: Dict[Symbol, Dict] = {}
    
    self.data: Dict[Symbol, SymbolData] = {}
    self.period: int = 3 * 8 * 21 # Eight quarter period
    self.one_quarter_data: Dict[Symbol, List[float]] = {} # Storing one quarter data about each stock from our universe
    self.eight_quarter_data: Dict[Symbol, RollingWindow] = {} # Storing eight quarter data about each stock from our universe
    
    self.quantile: int = 10
    self.leverage: int = 5
    self.last_investment_date = None
    self.symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.sp100_stocks: List[Symbol] = [] # 'AGN', 'UTX', 'BRKB' # No data about institutional ownership
    
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/economic/institutional_ownership/institutional_ownership_in_millions.csv')
    lines: List[str] = csv_string_file.split('\r\n')
    for i in range(len(lines)):
        line_split: List[str] = lines[i].split(',')
        if i == 0: # First row are headers of columns
            for j in range(1, len(line_split)): # Take all headers, which are stock tickers
                ticker: str = line_split[j]
                symbol: Symbol = self.AddEquity(ticker, Resolution.Daily).Symbol
                
                # Warmup volume data.
                self.data[symbol] = SymbolData(self.period)
                history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
                if history.empty:
                    self.Log(f"Not enough data for {symbol} yet")
                    continue
                volumes: Series = history.loc[symbol].volume
                for time, volume in volumes.items():
                    self.data[symbol].update(volume)
                
                self.one_quarter_data[symbol] = []
                self.eight_quarter_data[symbol] = RollingWindow[float](8)
                self.institutional_ownership[symbol] = {} # Create dictionary for all institutional ownership data
                
                # Subscript current stock and append symbol to universe, which we will use for this strategy 
                self.sp100_stocks.append(symbol)
        else:
            date: datetime.date = datetime.strptime(line_split[0], "%Y-%m-%d").date()
            
            self.dates.append(date) # Create list of dates for institutional annoucements
            
            for j, symbol in zip(range(1, len(line_split)), self.sp100_stocks):
                # Based on symbol store date and institutional ownership value as a nested dictionary
                # In nested dictionary date figures as a key and institutional ownership as a value
                self.institutional_ownership[symbol][date] = (line_split[j]) 
    
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.count_month: int = 1
    self.selection_flag: bool = False
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def OnData(self, slice: Slice) -> None:
    date = None
    inst_turn_in_div: Dict[Symbol, float] = {}
    
    current_date: datetime.date = self.Time.date()
    day_before: datetime.date = (self.Time - timedelta(days=1)).date()
    two_days_before: datetime.date = (self.Time - timedelta(days=2)).date()
    three_days_before: datetime.date = (self.Time - timedelta(days=3)).date()
    
    for symbol in self.sp100_stocks:
        # Update daily volume data.
        if symbol in slice:
            if slice[symbol]:
                self.data[symbol].update(slice[symbol].Volume)
        
        # Institutional ownership could be annouced on weekend. This prevents missing it.
        # Without three days look ahead it was missing some annoucements
        if (current_date in self.dates) and (current_date != self.last_investment_date):
            self.last_investment_date = current_date
            date = current_date
        elif (day_before in self.dates) and (day_before != self.last_investment_date):
            self.last_investment_date = day_before
            date = day_before
        elif (two_days_before in self.dates) and (two_days_before != self.last_investment_date):
            self.last_investment_date = two_days_before
            date = two_days_before
        elif (three_days_before in self.dates) and (three_days_before != self.last_investment_date):
            self.last_investment_date = three_days_before
            date = three_days_before
            
        # If institutional ownership was announced store institutional_ownership value about each stock from our universe
        if date in self.dates:
            if self.institutional_ownership[symbol][date] != '':
                self.one_quarter_data[symbol].append(float(self.institutional_ownership[symbol][date]))
    
        if not self.selection_flag:
            continue
        absolute_change = None
        if len(self.one_quarter_data[symbol]) >= 2:
            absolute_change: float = self.one_quarter_data[symbol][-1] - self.one_quarter_data[symbol][0]
            total_one_quarter: float = sum(self.one_quarter_data[symbol])
            self.eight_quarter_data[symbol].Add(total_one_quarter)
    
            # If eight quarter institutional ownership data are ready for chosen stock, then trade
            if self.data[symbol].is_ready() and self.eight_quarter_data[symbol].IsReady:  
                if symbol != 'ADP':
                    inst_turn_in_div_num: float = absolute_change / self.data[symbol].total_volume()
                    
                    total_inst_shares: float = sum([x for x in self.eight_quarter_data[symbol]])
                    inst_turn_in_div_num: float = inst_turn_in_div_num / total_inst_shares
                    
                    inst_turn_in_div[symbol] = inst_turn_in_div_num
        
        self.one_quarter_data[symbol].clear()
    
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    long: List[Symbol] = []
    short: List[Symbol] = []
    if len(inst_turn_in_div) >= self.quantile:
        quantile: int = int(len(inst_turn_in_div) / self.quantile)
        sorted_by_inst_turn_in_div = [x[0] for x in sorted(inst_turn_in_div.items(), key=lambda item: item[1])]
        # long the lowest ‘InstTurnIndiv’ decile
        long = sorted_by_inst_turn_in_div[:quantile]
        # short the highest ‘InstTurnIndiv’ decile
        short = sorted_by_inst_turn_in_div[-quantile:]
    
    # Trade execution.
    invested: List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
        
    for symbol in long:
        self.SetHoldings(symbol, 1 / len(long))
            
    for symbol in short:
        self.SetHoldings(symbol, -1 / len(short))
def Selection(self) -> None:
    if self.count_month == 3: # The portfolio is rebalance quarterly
        self.selection_flag = True
        self.count_month = 1
    else:
        self.count_month += 1
        
class SymbolData():
def __init__(self, period: int) -> None:
    self._volumes: RollingWindow = RollingWindow[float](period)
    
def update(self, volume) -> None:
    self._volumes.Add(volume)
    
def is_ready(self) -> bool:
    return self._volumes.IsReady
    
def total_volume(self) -> float:
    return sum(list(self._volumes))
    
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
