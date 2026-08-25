# Original QuantConnect / library Python
# locale=en slug="esg-premium-in-options"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
#endregion
class ESGPremiumInOptions(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2016, 1, 1) # First esg data are from 2016
    self.SetCash(1_000_000)
    
    # switching ratings from letters to number for easier sorting
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
    
    self.min_expiry: int = 20
    self.max_expiry: int = 30
    
    self.leverage: int = 40
    self.quantile: int = 5
    self.percentage_traded: int = .1
    self.esg_ratings: Dict[str, Dict[datetime.date, float]] = {}
    self.subscribed_contracts: Dict[str, Symbol] = {}
    self.selected_symbols: List[Symbol] = []
        
    self.long_stock_options: List[Symbol] = []
    self.short_stock_options: List[Symbol] = []
    
    # download companies esg rating
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/economic/ESG.csv')
    lines: List[str] = csv_string_file.split('\r\n')
    # skip date and get only stocks tickers 
    header: List[str] = lines[0].split(';')[1:]
    
    # for each company ticker create dictionary in self.esg_ratings
    # to store esg ratings under specific dates for specific stocks
    for ticker in header:
        self.esg_ratings[ticker] = {}
    
    for line in lines[1:]: # Skip header
        line_split: List[str] = line.split(';')
        date: datetime.date = datetime.strptime(line_split[0], "%d.%m.%Y").date()
        
        ratings: float = line_split[1:] # exclude date
        
        for i in range(len(ratings)):
            # store stocks rating under specific date, if rating isn't -1
            if ratings[i] != '-1':
                # switch rating letters to number
                switched_rating: float = rating_switcher[ratings[i]]
                # store number rating under specific date for specific stock
                self.esg_ratings[header[i]][date] = switched_rating
                
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.recent_stock_price: Dict[Symbol, float] = {}    # currently selected universe stock adjusted prices
    
    self.last_expiration_date: Union[None, datetime.date] = None     # last expiry date of currently selected traded option universe 
    
    self.trade_flag: bool = False
    self.selection_flag: bool = False   
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
    self.Schedule.On(self.DateRules.EveryDay(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # store daily recent currently selected universe prices and SPY market price
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        if symbol in self.selected_symbols:
            self.recent_stock_price[symbol] = stock.AdjustedPrice
    
    # monthly rebalance
    if not self.selection_flag:
        return Universe.Unchanged
    
    # universe will be created based on stock tickers which have ESG data
    self.selected_symbols = [
        x.Symbol for x in fundamental 
        if x.HasFundamentalData 
        and x.Symbol.Value in self.esg_ratings
    ]
    return self.selected_symbols
def OnData(self, slice: Slice) -> None:
    if self.trade_flag:
        long_length: int = len(self.long_stock_options)
        short_length: int = len(self.short_stock_options)
        
        long_w: float = self.Portfolio.TotalPortfolioValue / long_length
        short_w: float = self.Portfolio.TotalPortfolioValue / short_length
    
        # trade execution
        for stock_symbol in self.short_stock_options + self.long_stock_options:
            if self.securities[stock_symbol].is_delisted:
                continue
            ticker: str = stock_symbol.Value
            
            # atm call option contract of current stock might not be subscribed
            if ticker not in self.subscribed_contracts:
                continue
            
            # get atm call contract based on ticker
            atm_call: Symbol = self.subscribed_contracts[ticker]
            
            # make sure subscribed atm call option has data
            # if self.Securities.ContainsKey(atm_call) and self.Securities[atm_call].Price != 0 and \
            #     self.Securities.ContainsKey(stock_symbol) and self.Securities[stock_symbol].Price != 0:
            if slice.contains_key(atm_call) and slice[atm_call] and slice.contains_key(stock_symbol) and slice[stock_symbol]:
                stock_price: float = self.recent_stock_price[stock_symbol] if stock_symbol in self.recent_stock_price else 0
                
                if stock_price != 0:
                    if stock_symbol in self.short_stock_options:
                        # calculate atm call quantity
                        option_quantity: float = short_w * self.percentage_traded / (stock_price*100)
                        if option_quantity  self.last_expiration_date else self.last_expiration_date) if self.last_expiration_date is not None else expiry
        
        self.trade_flag = False   
    
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False        
    
    self.subscribed_contracts.clear()
    
    current_date: datetime.date = self.Time.date()
    esg_ratings: Dict[Symbol, float] = {} # storing latest stocks esg ratings
    
    for symbol in self.selected_symbols:
        esg_rating_value: float = self.GetRating(symbol, current_date)
        
        if esg_rating_value != None:
            esg_ratings[symbol] = esg_rating_value
    
    # there has to be enough stocks for quintile selection        
    if len(esg_ratings)  0:
            # sort by expiry
            atm_call: Symbol = sorted(atm_calls, key = lambda item: item.ID.Date, reverse=True)[0]
            
            # add contract
            option: Option = self.AddOptionContract(atm_call, Resolution.Daily)
            option.PriceModel = OptionPriceModels.CrankNicolsonFD()
            
            # store subscribed atm call contract keyed by it's ticker
            self.subscribed_contracts[atm_call.Underlying.Value] = atm_call
        
    self.trade_flag = True
def GetRating(self, 
            symbol: Symbol, 
            current_date: datetime.date) -> float:
    rating: Union[None, float] = None
    ticker: str = symbol.Value
    
    rating_dictionary: Dict[datetime.date, float] = self.esg_ratings[ticker]
    
    # go through each date or year and pick latest rating
    for date in list(rating_dictionary.keys()):
        # latest esg rating is changed if date with rating is later than current date
        if date  None:
    if self.last_expiration_date is not None and not self.trade_flag:
        # rebalance after every already traded option expired
        if self.last_expiration_date  OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
