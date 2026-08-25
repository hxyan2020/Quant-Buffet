# Original QuantConnect / library Python
# locale=zh slug="横截面六个月减去一个月股票atm跨式日历交易策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
from pandas.core.frame import DataFrame
from pandas.core.series import Series
#endregion
class CrossSectionalSixMinusOneMonthEquityATMStraddleCalendarTradingStrategy(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2012, 1, 1)
    self.SetCash(1000000)
    
    self.long_term_min_expiry: int = 150
    self.long_term_max_expiry: int = 230
    
    self.short_term_min_expiry: int = 20
    self.short_term_max_expiry: int = 45
    
    self.long_term_period: int = 6 * 21 # need n of stock daily prices
    self.short_term_period: int = 21 # need n of stock daily prices
    self.percentage_traded: float = 0.2
    self.min_contracts: int = 4
    self.leverage: int = 10
    self.min_share_price: int = 5
    self.quantile: int = 5
    
    self.data: Dict[Symbol, RollingWindow] = {}
    self.symbols_by_ticker: Dict[str, Symbol] = {}
    self.subscribed_contracts: Dict[Symbol, Contracts] = {}
    
    symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.day: int = -1
    self.fundamental_count: int = 50
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
    self.Schedule.On(self.DateRules.MonthStart(symbol), self.TimeRules.BeforeMarketClose(symbol, 0), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update daily prices of stocks in self.data dictionary
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].Add(stock.AdjustedPrice)
    
    # rebalance monthly
    if not self.selection_flag:
        return Universe.Unchanged
    
    # select top n stocks by dollar volume
    selected: List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price > self.min_share_price
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    for stock in selected:
        symbol: Symbol = stock.Symbol
        ticker: str = symbol.Value 
        self.symbols_by_ticker[ticker] = symbol
        
        if symbol in self.data:
            continue
        
        self.data[symbol] = RollingWindow[float](self.long_term_period)
        history: DataFrame = self.History(symbol, self.long_term_period, Resolution.Daily)
        if history.empty:
            continue
        closes: Series = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].Add(close)
    # return newly selected symbols
    return list(map(lambda x: x.Symbol, selected))
def OnData(self, data: Slice) -> None:
    # execute once a day
    if self.day == self.Time.day:
        return
    self.day = self.Time.day
    
    # subscribe to new contracts after selection
    if len(self.subscribed_contracts) == 0 and self.selection_flag:
        for _, symbol in self.symbols_by_ticker.items():
            if symbol in self.data and self.data[symbol].IsReady:
                # get all contracts for current stock symbol
                contracts: List[Symbol] = self.OptionChainProvider.GetOptionContractList(symbol, self.Time)
                # get current price for etf
                underlying_price: float = self.data[symbol][0]
                
                # get strikes from commodity future contracts
                strikes: List[float] = [i.ID.StrikePrice for i in contracts]
                
                # can't filter contracts, if there isn't any strike price
                if len(strikes)  0 and len(long_term_puts) > 0 and len(short_term_calls) > 0 and len(short_term_puts) > 0:
                    # sort by expiry
                    long_term_call: Symbol = sorted(long_term_calls, key = lambda x: x.ID.Date, reverse=True)[0]
                    long_term_put: Symbol = sorted(long_term_puts, key = lambda x: x.ID.Date, reverse=True)[0]
                    
                    short_term_call: Symbol = sorted(short_term_calls, key = lambda x: x.ID.Date, reverse=True)[0]
                    short_term_put: Symbol = sorted(short_term_puts, key = lambda x: x.ID.Date, reverse=True)[0]
                    
                    subscriptions = self.SubscriptionManager.SubscriptionDataConfigService.GetSubscriptionDataConfigs(short_term_call.Underlying)
                    if subscriptions:
                        # add contracts
                        for contract in [long_term_call, long_term_put, short_term_call, short_term_put]:
                            
                            self.AddContract(contract)
                        
                        # retrieve expiry date for contracts
                        long_term_expiry_date: datetime.date = long_term_call.ID.Date.date()
                        
                        short_term_expiry_date: datetime.date = short_term_call.ID.Date.date()
                        
                        # store contracts with expiry date under stock's symbol
                        self.subscribed_contracts[symbol] = Contracts(
                            long_term_expiry_date,
                            short_term_expiry_date, 
                            [long_term_call, long_term_put],
                            [short_term_call, short_term_put],
                            underlying_price
                        )
        
    # calculate term structure and trade options
    elif len(self.subscribed_contracts) != 0 and data.OptionChains.Count != 0 and self.selection_flag:
        self.selection_flag = False # this makes sure, there will be no other trades until next selection
        
        term_structure_long_term: Dict[Symbol, float] = {} # storing term structures keyed by stock's symbol
        term_structure_short_term: Dict[Symbol, float] = {}
        
        for kvp in data.OptionChains:
            chain: OptionChain = kvp.Value
            ticker: str = chain.Underlying.Symbol.Value
            if ticker in self.symbols_by_ticker:
                # get stock's symbol
                symbol: Symbol = self.symbols_by_ticker[ticker]
                if symbol in self.subscribed_contracts:
                    # get contracts
                    contracts: List[Symbol] = [x for x in chain]
                    
                    # check if there are enough contracts for option and daily prices are ready
                    if len(contracts)  None:
    self.selection_flag = True # perform new selection
    self.Liquidate() # rebalance monthly, so liquidate all holding contracts
    
    # remove contracts from securities
    # for _, contracts_obj in self.subscribed_contracts.items():
    #     for contract in contracts_obj.long_term_contracts + contracts_obj.short_term_contracts:
    #         self.RemoveSecurity(contract)
            
    # clear dictionary for subscribed contracts, because there will be new selection
    self.subscribed_contracts.clear()
    # clear dictionary of tickers and their symbols, because new stocks will be selected
    self.symbols_by_ticker.clear()
    
def FilterContracts(self, 
                    strikes: List[float],
                    contracts: List[Symbol], 
                    underlying_price: float, 
                    min_expiry: datetime.date, 
                    max_expiry: datetime.date) -> List[Symbol]:
    ''' filter call and put contracts from contracts parameter '''
    ''' return call and put contracts '''
    
    # Straddle
    call_strike: float = min(strikes, key=lambda x: abs(x-underlying_price))
    put_strike: float = call_strike
    
    calls: List[Symbol] = [] # storing call contracts
    puts: List[Sybol] = [] # storing put contracts
    
    for contract in contracts:
        # check if contract has one month expiry
        if min_expiry  None:
    ''' subscribe option contract, set price mondel and normalization mode '''
    option: Option = self.AddOptionContract(contract, Resolution.Daily)
    option.PriceModel = OptionPriceModels.CrankNicolsonFD()
    option.SetDataNormalizationMode(DataNormalizationMode.Raw)
    
def GetImpliedVolatilities(self, 
                        contracts: List[Symbol], 
                        long_term_expiry: datetime.date, 
                        short_term_expiry: datetime.date) -> float:
    ''' retrieve implied volatility of contracts from contracts parameteres '''
    ''' returns long term and short term implied volatility for call and put contracts '''
    long_term_call_iv: Union[None, float] = None
    long_term_put_iv: Union[None, float] = None
    
    short_term_call_iv: Union[None, float] = None
    short_term_put_iv: Union[None, float] = None
            
    # go through option contracts
    for c in contracts:
        iv: float = c.ImpliedVolatility
        expiry_date: datetime.date = c.get_Expiry().date()
        
        if c.Right == OptionRight.Call:
            if expiry_date == long_term_expiry:
                long_term_call_iv = iv
            elif expiry_date == short_term_expiry:
                short_term_call_iv = iv
        else:
            if expiry_date == long_term_expiry:
                long_term_put_iv = iv
            elif expiry_date == short_term_expiry:
                short_term_put_iv = iv
        
    return long_term_call_iv, long_term_put_iv, short_term_call_iv, short_term_put_iv
    
def GetHistoricalVolatility(self, 
                            rolling_window_prices: RollingWindow, 
                            period: int) -> float:
    ''' calculate historical volatility based on daily prices in rolling_window_prices parameter '''
    prices: np.ndarray = np.array([x for x in rolling_window_prices][:period])
    returns: np.ndarray = (prices[:-1] - prices[1:]) / prices[1:]
    return np.std(returns)
    
def TradeOptions(self, 
                data: Slice, 
                symbols: List[Symbol], 
                long_flag: bool, 
                long_term_flag: bool) -> None:
    ''' on long signal buy call and put option contract '''
    ''' on short signal sell call and put option contract '''
    length: int = len(symbols)
    
    # trade etf's call and put contracts
    for symbol in symbols:
        if long_term_flag:
            contracts: List[Symbol] = self.subscribed_contracts[symbol].long_term_contracts
        else:
            contracts: List[Symbol] = self.subscribed_contracts[symbol].short_term_contracts
            
        # check if contracts are tradebale and don't have 0 price
        for contract in contracts:
            if not self.Securities[contract].IsTradable or self.Securities[contract].Price == 0:
                return
            
        # get call and put contract
        call, put = contracts
        # get underlying price
        underlying_price: float = self.subscribed_contracts[symbol].underlying_price
        
        options_q: int = int(((self.Portfolio.TotalPortfolioValue * self.percentage_traded) / length) / (underlying_price * 100))
        
        self.Securities[put].MarginModel = BuyingPowerModel(2)
        self.Securities[call].MarginModel = BuyingPowerModel(2)
        
        if call in data and data[call] and put in data and data[put]:
            if long_flag:
                self.Buy(call, options_q)
                self.Buy(put, options_q)
            else:
                self.Sell(call, options_q)
                self.Sell(put, options_q)
    
class Contracts():
def __init__(self, 
            long_term_expiry_date: datetime.date, 
            short_term_expiry_date: datetime.date, 
            long_term_contracts: List[Symbol], 
            short_term_contracts: List[Symbol], 
            underlying_price: float) -> None:
    self.long_term_expiry_date: datetime.date = long_term_expiry_date
    self.long_term_contracts: List[Symbol] = long_term_contracts
    
    self.short_term_expiry_date: datetime.date = short_term_expiry_date
    self.short_term_contracts: List[Symbol] = short_term_contracts
    
    self.underlying_price = underlying_price
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
