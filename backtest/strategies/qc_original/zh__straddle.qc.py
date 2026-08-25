# Original QuantConnect / library Python
# locale=zh slug="横截面六个月股票平值straddle-交易策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
from pandas.core.frame import DataFrame
from pandas.core.series import Series
#endregion
class CrossSectionalSixMonthEquityATMStraddleTradingStrategy(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(1000000)
    
    self.min_expiry: int = 180
    self.max_expiry: int = 240
    
    self.period: int = 6 * 21 # need n of stock daily prices
    self.percentage_traded: float = 0.1
    self.selection_threshold: int = 10
    self.min_share_price: int = 10
    self.quantile: int = 10
    self.leverage: int = 10
    
    self.data: Dict[Symbol, RollingWindow[float]] = {}
    self.symbols_by_ticker: Dict[str, Symbol] = {}
    self.subscribed_contracts: Dict[Symbol, Contracts] = {}
    
    symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.day: int = -1
    self.fundamental_count: int = 100
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
    self.Schedule.On(self.DateRules.MonthStart(symbol), self.TimeRules.BeforeMarketClose(symbol), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update daily prices of stocks in self.data dictionary
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
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
        
        self.data[symbol] = RollingWindow[float](self.period)
        history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
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
            if self.Securities[symbol].IsDelisted:
                continue
            if symbol in data and data[symbol]:
                if symbol in self.data and self.data[symbol].IsReady:
                    # get all contracts for current stock symbol
                    contracts: List[Symbol] = self.OptionChainProvider.GetOptionContractList(symbol, self.Time)
                    # get current price for etf
                    underlying_price: float = self.data[symbol][0]
                    
                    # get strikes from commodity future contracts
                    strikes: List[float] = [i.ID.StrikePrice for i in contracts]
                    
                    # can't filter contracts, if there isn't any strike price
                    if len(strikes)  0 and len(puts) > 0:
                        # sort by expiry
                        call: Symbol = sorted(calls, key = lambda x: x.ID.Date, reverse=True)[0]
                        put: Symbol = sorted(puts, key = lambda x: x.ID.Date, reverse=True)[0]
                        
                        subscriptions = self.SubscriptionManager.SubscriptionDataConfigService.GetSubscriptionDataConfigs(call.Underlying)
                        if subscriptions:
                            # add call contract
                            self.AddContract(call)
                            # add put contract
                            self.AddContract(put)
                            
                            # retrieve expiry date for contracts
                            expiry_date: dateTime.date = call.ID.Date.date()
                            # store contracts with expiry date under stock's symbol
                            self.subscribed_contracts[symbol] = Contracts(expiry_date, underlying_price, [call, put])
            
    # calculate term structure and trade options
    elif len(self.subscribed_contracts) != 0 and data.OptionChains.Count != 0 and self.selection_flag:
        self.selection_flag = False # this makes sure, there will be no other trades until next selection
        
        term_structure: Dict[Symbol, float] = {} # storing term structures keyed by stock's symbol
        
        for kvp in data.OptionChains:
            chain: OptionChain = kvp.Value
            
            ticker: str = chain.Underlying.Symbol.Value
            if ticker in self.symbols_by_ticker:
                # get stock's symbol
                symbol: Symbol = self.symbols_by_ticker[ticker]
                if symbol in data and data[symbol]:
                    # get contracts
                    contracts: List[Symbol] = [x for x in chain]
                    
                    # check if there are enough contracts for option and daily prices are ready
                    if len(contracts)  None:
    self.selection_flag = True  # perform new selection
    self.Liquidate()            # rebalance monthly, so liquidate all holdings
    
    # clear dictionary for subscribed contracts, because there will be new selection
    self.subscribed_contracts.clear()
    # clear dictionary of tickers and their symbols, because new stocks will be selected
    self.symbols_by_ticker.clear()
    
def FilterContracts(self, strikes: List[float], contracts: List[Symbol], underlying_price: float) -> List[Symbol]:
    ''' filter call and put contracts from contracts parameter '''
    ''' return call and put contracts '''
    
    # straddle
    call_strike: float = min(strikes, key=lambda x: abs(x-underlying_price))
    put_strike: float = call_strike
    
    calls: List[Symbol] = []  # storing call contracts
    puts: List[Symbol] = []   # storing put contracts
    
    for contract in contracts:
        # check if contract has six months expiry
        if self.min_expiry  None:
    ''' subscribe option contract, set price mondel and normalization mode '''
    option: Option = self.AddOptionContract(contract, Resolution.Daily)
    option.PriceModel = OptionPriceModels.CrankNicolsonFD()
    
def GetImpliedVolatilities(self, contracts: List[Symbol]) -> List[float]:
    ''' retrieve implied volatility of contracts from contracts parameteres '''
    ''' returns call and put implied volatility '''
    call_iv: Union[None, float] = None
    put_iv: Union[None, float] = None
            
    # go through option contracts
    for c in contracts:
        if c.Right == OptionRight.Call:
            # found call option
            call_iv = c.ImpliedVolatility
        else:
            # found put option
            put_iv = c.ImpliedVolatility
        
    return call_iv, put_iv
    
def GetHistoricalVolatility(self, rolling_window_prices: RollingWindow) -> float:
    ''' calculate historical volatility based on daily prices in rolling_window_prices parameter '''
    prices: np.ndarray = np.array([x for x in rolling_window_prices])
    returns: np.ndarray = (prices[:-1] - prices[1:]) / prices[1:]
    return np.std(returns)
    
def TradeOptions(self, data: Slice, symbols: List[Symbol], long_flag: bool):
    ''' on long signal buy call and put option contract '''
    ''' on short signal sell call and put option contract '''
    count: int = len(symbols)
    
    # trade etf's call and put contracts
    for symbol in symbols:
        if symbol in self.subscribed_contracts:
            # check if contracts are tradebale and don't have 0 price
            # for contract in self.subscribed_contracts[symbol].contracts:
            #     if not self.Securities[contract].IsTradable or self.Securities[contract].Price == 0:
            #         return

            # get call and put contract
            call, put = self.subscribed_contracts[symbol].contracts
            # get underlying price
            underlying_price: float = self.subscribed_contracts[symbol].underlying_price
            
            options_q: int = int(((self.Portfolio.MarginRemaining * self.percentage_traded) / count) / (underlying_price * 100))
            
            if call in data and data[call] and put in data and data[put]:
                if long_flag:
                    self.Buy(call, options_q)
                    self.Buy(put, options_q)
                else:
                    self.Sell(call, options_q)
                    self.Sell(put, options_q)
    
class Contracts():
def __init__(self, expiry_date: datetime.date, underlying_price: float, contracts: List[Symbol]):
    self.expiry_date: datetime.date = expiry_date
    self.underlying_price: float = underlying_price
    self.contracts: List[Symbol] = contracts
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
