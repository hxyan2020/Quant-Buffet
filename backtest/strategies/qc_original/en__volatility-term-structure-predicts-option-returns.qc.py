# Original QuantConnect / library Python
# locale=en slug="volatility-term-structure-predicts-option-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict, Tuple
from dataclasses import dataclass
#endregion
class VolatilityTermStructurePredictsOptionReturns(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(1000000)
    self.symbol_price_manager = {}
    self.tickers_to_ignore: List[str] = ['DASH', 'GOOG', 'GME']
    self.short_term_min_expiry: int = 25
    self.short_term_max_expiry: int = 35
    
    self.long_term_min_expiry: int = 50
    self.long_term_max_expiry: int = 360
    self.threshold: int = 4
    self.leverage: int = 5
    self.quantile: int = 10
    self.min_share_price: int = 5
    self.fundamental_count = 100
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.short_term_contracts: Dict[str, Contracts] = {}
    self.long_term_contracts: Dict[str, Contracts] = {}
    self.symbols_by_ticker: Dict[str, Symbol] = {}      # stock symbols indexed by ticker
    self.updated_date: Dict[Symbol, datetime.date] = {} # last IV update date indexed by stock symbol
    self.opened_positions: List[Symbol] = []            # opened stock symbols
    
    symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.some_trade_was_opened_day_before: bool = False
    
    self.day: int = -1
    self.traded_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
        stock_symbol: Symbol = security.Symbol
        self.updated_date[stock_symbol] = None
    
    for security in changes.RemovedSecurities:
        stock_symbol = security.Symbol
        if stock_symbol in self.updated_date:
            del self.updated_date[stock_symbol]
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # rebalance on contract expirations
    if len(self.symbols_by_ticker) != 0:
        return Universe.Unchanged
    
    # select top n stocks by dollar volume with price higher than 5
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.Market == 'usa' and
        x.Price > self.min_share_price 
        and x.Symbol.Value not in self.tickers_to_ignore
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # create pair stock's ticker and stock's symbol
    self.symbols_by_ticker = { x.Symbol.Value : x.Symbol for x in selected }
    
    # return symbols of selected stocks
    return list(self.symbols_by_ticker.values())
    
def OnData(self, data: Slice) -> None:
    # prevent data error
    # calculate slope every day if trades are not opened
    if len(self.opened_positions) == 0:
        slope: Dict[Symbol, float] = {}          # stored slope of stock
        stock_prices: Dict[Symbol, float] = {}   # stored price of stock
        
        for kvp in data.OptionChains:
            chain: OptionChain = kvp.Value
            
            # option symbol
            symbol: Symbol = chain.Underlying.Symbol
            # option ticker
            ticker: str = symbol.Value
            
            if ticker not in self.symbols_by_ticker:
                continue
            
            # based on option ticker get stock symbol
            stock_symbol: Symbol = self.symbols_by_ticker[ticker]
            
            # make sure, spread is updated once in a day
            if stock_symbol in self.updated_date:
                if self.updated_date[stock_symbol] is not None:
                    if self.updated_date[stock_symbol] == self.Time.date():
                        continue
            contracts: List[OptionContract] = [x for x in chain]
            
            # check if there are enough contracts
            if len(contracts) = self.quantile:
            quantile: int = int(len(slope) / self.quantile)
            sorted_by_slope: List[Tuple[Symbol, float]] = sorted(slope.items(), key = lambda x: x[1], reverse=True)
            
            # long highest slope and short lowest slope
            long: List[Tuple[Symbol, float]] = sorted_by_slope[:quantile]
            short: List[Tuple[Symbol, float]] = sorted_by_slope[-quantile:]
            
            long_count: int = len(long)
            short_count: int = len(short)
            
            long_w: float = 1 / long_count
            short_w: float = 1 / short_count
            for stock_symbol, _ in long:
                # retrieve short atm call contract symbol based on ticker
                contract_symbol: Symbol = self.short_term_contracts[stock_symbol.Value].contracts[0]
                price: float = stock_prices[stock_symbol]
                
                equity: float = self.Portfolio.TotalPortfolioValue * long_w
                options_q: int = int(equity / (price * 100))
                # buy contract
                if stock_symbol in data and data[stock_symbol] and contract_symbol in data and data[contract_symbol]:
                    self.Buy(contract_symbol, options_q)
                    self.Sell(stock_symbol, options_q * 50)  # initial delta hedge
                
                # store opened position
                self.opened_positions.append(stock_symbol)
            for stock_symbol, _ in short:
                if self.Securities[stock_symbol].IsDelisted:
                    continue
                # retrieve short atm call contract symbol based on ticker
                contract_symbol: Symbol = self.short_term_contracts[stock_symbol.Value].contracts[0]
                price: float = stock_prices[stock_symbol]
                equity: float = self.Portfolio.TotalPortfolioValue * short_w
                options_q: int = int(equity / (price * 100))
                # sell contract
                if stock_symbol in data and data[stock_symbol] and contract_symbol in data and data[contract_symbol]:
                    self.Sell(contract_symbol, options_q)
                    self.Buy(stock_symbol, options_q * 50)  # initial delta hedge
                # store opened position
                self.opened_positions.append(stock_symbol)
                
    # check if contracts expiries once in a day
    if self.day == self.Time.day:
        return
    self.day = self.Time.day
    
    for ticker, stock_symbol in self.symbols_by_ticker.items():
        # subscribe to new short term contracts, when last one expiries
        if ticker in self.short_term_contracts and ticker in self.long_term_contracts:
            short_contracts_obj = self.short_term_contracts[ticker]
            # check if contract is about to expire
            if short_contracts_obj.expiry.date() - timedelta(days=2)  None:
    contracts: List[Symbol] = self.OptionChainProvider.GetOptionContractList(symbol, self.Time)
    # get current price for stock
    underlying_price: float = self.Securities[symbol].Price
    
    # get strikes from stock contracts
    strikes: List[float] = [i.ID.StrikePrice for i in contracts]
    
    # check if there is at least one strike    
    if len(strikes)  0 and len(atm_puts) > 0:
        # sort by expiry
        atm_call: Symbol = sorted(atm_calls, key = lambda item: item.ID.Date, reverse=True)[0]
        atm_put: Symbol = sorted(atm_puts, key = lambda item: item.ID.Date, reverse=True)[0]
        
        subscriptions = self.SubscriptionManager.SubscriptionDataConfigService.GetSubscriptionDataConfigs(atm_call.Underlying)
        if subscriptions:
            # add contracts
            for contract in [atm_call, atm_put]:
                if self.Securities[contract.Underlying].IsDelisted:
                    continue
                self.AddContract(contract)
                
            # based on value of short_term_flag store subscribed contracts in specific dictionary
            if short_term_flag:
                self.short_term_contracts[ticker] = Contracts(atm_call.ID.Date, [atm_call, atm_put])
            else:
                self.long_term_contracts[ticker] = Contracts(atm_call.ID.Date, [atm_call, atm_put])
            
def AddContract(self, contract: Symbol) -> None:
    ''' subcribe to contract, set price model and normalization mode '''
    option: Option = self.AddOptionContract(contract, Resolution.Daily)
    option.SetLeverage(self.leverage)
    option.PriceModel = OptionPriceModels.CrankNicolsonFD()
    
class SymbolData():
def __init__(self) -> None:
    self.slope: Union[None, float] = None
    self.updated_date: Union[None, datetime.date] = None
    
def update_slope(self, slope: float, updated_date: datetime.date) -> None:
    self.slope = slope
    self.updated_date = updated_date
    
@dataclass
class Contracts():
expiry: datetime.date
contracts: List[Symbol] 
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
