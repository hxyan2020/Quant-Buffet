# Original QuantConnect / library Python
# locale=zh slug="波动率的波动效应在股票中的表现"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from typing import List, Dict
#endregion
class VolatilityOfVolatilityEffectinStocks(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    # self.min_expiry = 30
    # self.max_expiry = 60
    
    self.tickers_to_ignore: List[str] = ['XOM', 'AAPL', 'AMZN']
    self.period: int = 20   # need n of daily implied volatility values
    self.leverage: int = 5
    self.min_share_price: int = 5
    self.quantile: int = 5
    
    self.data: Dict[Symbol, SymbolData] = {}       # storing daily IV
    self.contracts: Dict[Symbol, Contract] = {}    # storing option contracts
    self.tickers_symbols: Dict[str, Symbol] = {}   # storing symbols under their tickers
    
    symbol: Symbol = self.AddEquity('SPY', Resolution.Minute).Symbol
    
    self.day: int = -1
    self.fundamental_count: int = 100
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Minute
    self.settings.daily_precise_end_time = False
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
    self.Schedule.On(self.DateRules.MonthStart(symbol), self.TimeRules.BeforeMarketClose(symbol), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # rebalance weekly
    if not self.selection_flag:
        return Universe.Unchanged
    
    # select top n stocks by dollar volume with price higher than 5
    selected: List[Fundamental] = sorted([
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0 and x.Price > self.min_share_price and x.Symbol.Value not in self.tickers_to_ignore
    ], key=lambda x: x.DollarVolume, reverse=True)[:self.fundamental_count]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
            
    selected_symbols: List[Symbol] = [] # storing symbols of selected stocks
    selected_tickers: List[str] = [] # storing tickers of selected stocks
    
    # add new stocks to dictionaries
    for stock in selected:
        symbol: Symbol = stock.Symbol
        ticker: str = symbol.Value
        market_cap: float = stock.MarketCap
        
        # remove duplicate stocks from fine
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
            self.data[symbol].update_market_cap(market_cap)
            continue
        
        # store stock market cap and create RollingWindwow for IV values
        self.data[symbol] = SymbolData(self.period, market_cap)
        # store symbol under stock ticker            
        self.tickers_symbols[ticker] = symbol
        # create object from Contracts class for stock symbol
        self.contracts[symbol] = Contract(self.Time.date(), [])
    
    # make sure, data are consecutive
    remove_tickers_symbols: List[Tuple[str, Symbol]] = [] # storing tuple (ticker, symbol)
    
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
            for kvp in data.OptionChains:
                chain: OptionChain = kvp.Value
                symbol: Symbol = chain.Underlying.Symbol
                
                # get option ticker from option symbol
                ticker: str = symbol.Value
                
                if ticker not in self.tickers_symbols:
                    continue
                
                # based on option ticker get stock symbol
                stock_symbol: Symbol = self.tickers_symbols[ticker]
                
                # make sure, IV is updated once in a day
                if stock_symbol not in self.data or self.data[stock_symbol].updated_date == self.Time.date():
                    continue
                
                contracts: List[OptionContract] = [x for x in chain]
                
                # make sure, there are enough contracts for stock
                if len(contracts)  None:
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
        atm_call: Symbol = sorted(atm_calls, key = lambda item: item.ID.Date, reverse=True)[0]
        atm_put: Symbol = sorted(atm_puts, key = lambda x: x.ID.Date, reverse=True)[0]
        
        # add contracts
        for contract in [atm_call, atm_put]:
            self.AddContract(contract)
        
        # get expiry date of contracts
        expiry_date: datetime.date = atm_call.ID.Date.date()
        # create new Contracts object for stock            
        self.contracts[symbol] = Contract(expiry_date, [atm_call, atm_put])   
        
def FilterContracts(self, contracts: List[Symbol], option_right: float, strike: float) -> List[Symbol]:
    ''' filter contracts based on option_right and select only contracts with expiry in next month are selected '''
    
    # filter contracts based on option right and select only contracts with next month expiry
    filtered_contracts: List[Symbol] = [i for i in contracts if i.ID.OptionRight == option_right and 
                                             i.ID.StrikePrice == strike and 
                                             (self.Time.month + 1) == i.ID.Date.month]
                                            #  self.min_expiry  None:
    ''' subcribe to contract, set price model and normalization mode '''
    option = self.AddOptionContract(contract, Resolution.Minute)
    option.PriceModel = OptionPriceModels.CrankNicolsonFD()
    option.SetDataNormalizationMode(DataNormalizationMode.Raw)
    
def Selection(self) -> None:
    self.selection_flag = True
    
class Contract():
def __init__(self, expiry_date: datetime.date, contracts: List[Symbol]) -> None:
    self.expiry_date: datetime.date = expiry_date
    self.contracts: List[Symbol] = contracts
    
class SymbolData():
def __init__(self, period: int, market_cap: float):
    self.implied_vol: RollingWindow = RollingWindow[float](period)
    self.market_cap: float = market_cap
    self.updated_date: Union[None, datetime.date] = None
    
def update_implied_vol(self, implied_vol: float, updated_date: datetime.date) -> None:
    self.implied_vol.Add(implied_vol)
    self.updated_date = updated_date
    
def update_market_cap(self, market_cap: float) -> None:
    self.market_cap = market_cap

def volatility_of_volatility(self) -> float:
    iv_values: np.ndarray = np.array([x for x in self.implied_vol])
    mean_iv: float = np.mean(iv_values)
    vov: float = np.sqrt(np.mean((iv_values - mean_iv)**2)) / mean_iv
    return vov
    
def is_ready(self) -> bool:
    return self.implied_vol.IsReady and self.market_cap
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
