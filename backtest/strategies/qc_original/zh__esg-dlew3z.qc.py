# Original QuantConnect / library Python
# locale=zh slug="员工满意度、esg与股票回报"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
#endregion
class EmployeeSatisfactionESGAndStockReturns(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1) # First esg data are from 2016
    self.SetCash(100000)
    
    # Switching ratings from letters to number for easier sorting
    rating_switcher: Dict[str, int] = {
        'AAA': 9,
        'AA': 8,
        'A': 7,
        'BBB': 6,
        'BB': 5,
        'B': 4,
        'CCC': 3,
        'CC': 2,
        'C': 1,
    }
    
    self.leverage: int = 5
    self.latest_date_esg: Union[None, datetime.date] = None
    self.latest_emp_satisf: Union[None, datetime.date] = None
    
    self.quantile: int = 4
    self.weight: Dict[Symbol, float] = {} # Storing stocks holding weights
    
    self.esg_ratings: Dict[str, Dict[datetime.date, int]] = {}
    self.employees_satisfaction: Dict[str, Dict[datetime.date, str]] = {}
    
    # Download companies employees satisfaction ratings for each year
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/index/EMPLOYEE_SATISFACTION.csv')
    lines: List[str] = csv_string_file.split('\r\n')
    for line in lines[1:]: # Skip header
        line_split: List[str] = line.split(';')
        date: datetime.date = datetime.strptime(line_split[0], "%d.%m.%Y").date()
        if not self.latest_emp_satisf:
            self.latest_emp_satisf = date
        if date > self.latest_emp_satisf:
            self.latest_emp_satisf = date
        
        company_ticker: str = line_split[1]
        rating: str = line_split[2]
        
        # Create dictionary for each company ticker
        if company_ticker not in self.employees_satisfaction:
            self.employees_satisfaction[company_ticker] = {}
        
        # Under company ticker and year store rating
        self.employees_satisfaction[company_ticker][date.year] = rating
        
    # Download companies esg rating
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/economic/ESG.csv')
    lines: List[str] = csv_string_file.split('\r\n')
    # Skip date and get only stocks tickers 
    header: List[str] = lines[0].split(';')[1:]
    
    # For each company ticker create dictionary in self.esg_ratings
    # to store esg ratings under specific dates for specific stocks
    for ticker in header:
        self.esg_ratings[ticker] = {}
    
    for line in lines[1:]: # Skip header
        line_split: List[str] = line.split(';')
        date: datetime.date = datetime.strptime(line_split[0], "%d.%m.%Y").date()
        self.latest_date_esg = date
        
        ratings: str = line_split[1:] # Exclude date
        
        for i in range(len(ratings)):
            # Store stocks rating under specific date, if rating isn't -1
            if ratings[i] != '-1':
                # Switch rating letters to number
                switched_rating: int = rating_switcher[ratings[i]]
                # Store number rating under specific date for specific stock
                self.esg_ratings[header[i]][date] = switched_rating
                
    self.market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.long_only_flag: bool = True
    self.short_market_flag: bool = True
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)
                
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Monthly rebalance
    if not self.selection_flag:
        return Universe.Unchanged
    
    # check if we still have custom data
    if self.Time.date() > self.latest_date_esg or self.Time.date() > self.latest_emp_satisf:
        self.Liquidate()
        return Universe.Unchanged
    # Universe will be created based on stocks tickers in self.employees_satisfaction and self.esg_ratings
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.MarketCap != 0
        and x.Symbol.Value in self.employees_satisfaction 
        and x.Symbol.Value in self.esg_ratings
        ]
    
    market_cap: Dict[Symbol, float] = {}     # Storing stocks market capitalization
    esg_ratings: Dict[Symbol, float] = {}    # Storing latest stocks esg ratings
    employees_satisfaction_ratings: Dict[Symbol, float] = {} # Storing employees satisfaction ratings for each stock
    
    current_year: int = self.Time.year   # Getting latest stocks employees satisfaction ratings
    current_date: datetime.date = self.Time.date() # Getting latest actual stocks esg ratings
    
    for stock in selected:
        symbol: Symbol = stock.Symbol
        
        # Get latest esg rating
        esg_rating: float = self.GetRating(self.esg_ratings[symbol.Value], current_date)
        
        # Get latest employees satisfaction rating
        employees_satisfaction_rating: float = self.GetRating(self.employees_satisfaction[symbol.Value], current_year)
        
        # Go to next stock if esg rating or employees satisfaction rating is None
        if esg_rating == None or employees_satisfaction_rating == None:
            continue
        
        # Store market capitalization, esg rating and employees satisfaction rating for current stock
        market_cap[stock] = stock.MarketCap
        esg_ratings[stock] = esg_rating
        employees_satisfaction_ratings[stock] = employees_satisfaction_rating
    
    # Check if there are enough stocks for quartile selection
    if len(market_cap)  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution
    invested: List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in self.weight:
            self.Liquidate(symbol)
    
    # Short market, when there are enough stocks for long
    if self.short_market_flag and len(self.weight) > 0:
        if self.market in data and data[self.market]:
            self.SetHoldings(self.market, -1)
    
    # Go only long stocks
    if self.long_only_flag:
        for symbol, w in self.weight.items():
            if w > 0:
                if symbol in data and data[symbol]:
                    self.SetHoldings(symbol, w)
    # Go long and short stocks
    else: 
        for symbol, w in self.weight.items():
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, w)
        
    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    
def GetRating(self, 
            rating_dictionary: Dict[datetime.date, int], 
            lookup_date_or_year: int) -> float:
    rating: Union[None, float] = None
    
    # Go through each date or year (based on picked dictionary) and pick actual latest rating
    for date in rating_dictionary:
        # Actual latest esg rating is changed if date with rating is later than current date
        # Actual latest employees satisfaction rating is changed if year with rating is later than current year
        if date  float:
    quantile: int = int(len(market_cap) / quantile)
    
    # sort dictionary by rating and those with same values sort by thier market cap
    sorted_by_rating: List[Fundamental] = [x[0] for x in sorted(rating_dictionary.items(), key=lambda item: (item[1], market_cap[item[0]]))]
    
    # top quartile goes long 
    top: List[Fundamental] = sorted_by_rating[-quantile:]
    # bottom quartile goes short
    bottom: List[Fundamental] = sorted_by_rating[:quantile]
    
    return top, bottom
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
