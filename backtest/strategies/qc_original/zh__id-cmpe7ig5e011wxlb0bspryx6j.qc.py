# Original QuantConnect / library Python
# locale=zh slug="认沽-认购价差预测财报公告后的收益"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from pandas.tseries.offsets import BDay
import data_tools
from typing import List, Dict, Set, Tuple
#endregion
class PutCallSpreadPredictsEarningsAnnouncementReturns(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100_000)
    
    self.leverage: int = 5
    self.min_share_price: int = 5
    self.spread_threshold: int = 5
    self.top_percentile: int = 80
    self.bottom_percentile: int = 20
    # self.min_expiry = 30
    # self.max_expiry = 60
    self.fundamental_count: int = 100
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.data: Dict[Symbol, SymbolData] = {}               # storing daily IV
    self.contracts: Dict[Symbol, data_tools.Contract] = {} # storing option contracts
    self.tickers_symbols: Dict[str, Symbol] = {}           # storing symbols under their tickers
    
    # quarterly stored volatility spread values for stocks
    self.actual_quarter_spread_values: List[float] = []
    self.prev_quarter_spread_values: List[float] = []
    
    # parse earnings data
    self.earnings_universe: List[str] = [] # stored earnings tickers
    self.earnings_by_date: Dict[datetime, str] = {}
    earnings_set: Set = set()
    # self.first_date:datetime.date|None = None
    earnings_data: str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json: List[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date: datetime.date = datetime.strptime(obj['date'], "%Y-%m-%d").date()
        self.earnings_by_date[date] = []
        
        # if not self.first_date: self.first_date = date
        for stock_data in obj['stocks']:
            ticker: str = stock_data['ticker']
            self.earnings_by_date[date].append(ticker)
            earnings_set.add(ticker)
    for ticker in earnings_set:
        self.earnings_universe.append(ticker)
    self.symbol: Symbol = self.AddEquity('SPY', Resolution.Minute).Symbol
    # equally weighted brackets for traded symbols
    self.trade_manager: data_tools.TradeManager = data_tools.TradeManager(self, 10, 10, 2)
    
    self.long: List[Symbol] = []   # long stocks with the highest implied volatility spreads on pre-announcement day
    self.short: List[Symbol] = []  # short stocks with the lowest implied volatility spreads on pre-announcement day
    
    self.selection_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # rebalance weekly
    if not self.selection_flag:
        return Universe.Unchanged
    
    # select top n stocks by dollar volume with price higher than 5
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.MarketCap != 0 
        and x.Market == 'usa' 
        and x.Price > self.min_share_price 
        and x.Symbol.Value in self.earnings_universe
        ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    self.selection_flag = False
    
    selected_symbols: List[Symbol] = [] # storing symbols of selected stocks
    selected_tickers: List[str] = [] # storing tickers of selected stocks
    
    # add new stocks to dictionaries
    for stock in selected:
        symbol: Symbol = stock.Symbol
        ticker: str = symbol.Value
        market_cap: float = stock.MarketCap
        
        # remove duplicate stocks from selected
        if ticker in selected_tickers:
            # check if symbol of duplicated ticker was stored in self.data
            if symbol in self.data and symbol in self.contracts:
                # remove stock's contracts
                for contract in self.contracts[symbol].contracts:
                    self.RemoveSecurity(contract)
                    
                del self.data[symbol]
                del self.contracts[symbol]
            
            continue
        
        # add stock symbol to list of selected stocks
        selected_symbols.append(symbol)
        # add stock ticker to list of selected tickers
        selected_tickers.append(ticker)
        
        # don't override data, if they are consecutive
        if ticker in self.tickers_symbols and symbol in self.data and symbol in self.contracts:
            # update market cap
            self.data[symbol].market_cap = market_cap
            continue
        
        self.data[symbol] = data_tools.SymbolData(market_cap, None)
        # store symbol under stock ticker            
        self.tickers_symbols[ticker] = symbol
        # create object from Contract class for stock symbol
        self.contracts[symbol] = data_tools.Contract(self.Time.date(), [])
    
    # make sure, data are consecutive
    remove_tickers_symbols:List[Tuple[str, Symbol]] = [] # storing tuple (ticker, symbol)
    
    for ticker, symbol in self.tickers_symbols.items():
        # add stocks, which weren't selected to remove list
        if symbol not in selected_symbols:
            remove_tickers_symbols.append((ticker, symbol))
            
    # remove not selected stocks from dictionaries
    for ticker, symbol in remove_tickers_symbols:
        if symbol in self.contracts:
            # remove stock's contracts
            for contract in self.contracts[symbol].contracts:
                self.RemoveSecurity(contract)
                
            del self.contracts[symbol]
            
        if symbol in self.data:   
            # delete stock from dictionaries
            del self.data[symbol]
            del self.tickers_symbols[ticker]
    
    # return symbols of selected stocks    
    return selected_symbols
def OnData(self, data: Slice) -> None:
    # each day store implied volatility for selected stocks
    if self.Time.hour == 9:
        if data.OptionChains.Count != 0:
            # there is no earnings next day
            date_to_check: datetime.date = (self.Time.date() + BDay(1)).date()
            if date_to_check not in self.earnings_by_date:
                return
            # top and bottom percentile of volatility spread values
            top_percentile: Union[None, float] = None
            bottom_percentile: Union[None, float] = None
            
            # spread values are stored for previous quarter
            if len(self.prev_quarter_spread_values) > self.spread_threshold:
                top_percentile = np.percentile(self.prev_quarter_spread_values, self.top_percentile)
                bottom_percentile = np.percentile(self.prev_quarter_spread_values, self.bottom_percentile)
            for kvp in data.OptionChains:
                chain: OptionChains = kvp.Value
                symbol: Symbol = chain.Underlying.Symbol
                
                # get option ticker from option symbol
                ticker: str = symbol.Value
                    
                # stock has earnings in one day
                if ticker not in self.earnings_by_date[date_to_check]:
                    continue
                if ticker not in self.tickers_symbols:
                    continue
                
                # based on option ticker get stock symbol
                stock_symbol: Symbol = self.tickers_symbols[ticker]
                
                # make sure, spread is updated once in a day
                if stock_symbol not in self.data or self.data[stock_symbol].updated_date == self.Time.date():
                    continue
                
                contracts: List[OptionContracts] = [x for x in chain]
                
                # make sure, there are enough contracts for stock
                if len(contracts) = top_percentile:
                            self.long.append(stock_symbol)
                        elif vol_spread  None:
    ''' get atm and atm strike for specific symbol then it filters atm call and atm put ''' 
    ''' if there are enough atm calls and atm puts this function subscribes one of their contracts based on expiry and store expiry date ''' 
    
    # get all contracts for current commodity future
    contracts: List[Symbol] = self.OptionChainProvider.GetOptionContractList(symbol, self.Time)
    # get current price for commodity future
    underlying_price: float = self.Securities[symbol].Price
    
    # get strikes from commodity future contracts
    strikes: List[float] = [i.ID.StrikePrice for i in contracts]
    
    # check if there is at least one strike    
    if len(strikes)  0 and len(atm_puts) > 0:
        # sort by expiry
        atm_call: List[Symbol] = sorted(atm_calls, key = lambda item: item.ID.Date, reverse=True)[0]
        atm_put: List[Symbol] = sorted(atm_puts, key = lambda x: x.ID.Date, reverse=True)[0]
        
        # add contracts
        for contract in [atm_call, atm_put]:
            self.AddContract(contract)
        
        # get expiry date of contracts
        expiry_date: datetime.date = atm_call.ID.Date.date()
        # create new Contract object for stock            
        self.contracts[symbol] = data_tools.Contract(expiry_date, [atm_call, atm_put])   
        
def FilterContracts(self, 
                    contracts: List[Symbol], 
                    option_right: float, 
                    strike: float) -> List[Symbol]:
    ''' filter contracts based on option_right and select only contracts with expiry in next month are selected '''
    
    # filter contracts based on option right and select only contracts with next month expiry
    filtered_contracts: List[Symbol] = [i for i in contracts if i.ID.OptionRight == option_right and 
                                             i.ID.StrikePrice == strike and 
                                             (self.Time.month + 1) == i.ID.Date.month]
                                            #  self.min_expiry  None:
    ''' subcribe to contract, set price model and normalization mode '''
    option: Option = self.AddOptionContract(contract, Resolution.Minute)
    option.PriceModel = OptionPriceModels.CrankNicolsonFD()
    option.SetDataNormalizationMode(DataNormalizationMode.Raw)
    
def Selection(self) -> None:
    self.selection_flag = True
    
    # store spread values quarterly 
    if self.Time.month % 3 == 0:
        self.prev_quarter_spread_values = self.actual_quarter_spread_values
        self.actual_quarter_spread_values = []
