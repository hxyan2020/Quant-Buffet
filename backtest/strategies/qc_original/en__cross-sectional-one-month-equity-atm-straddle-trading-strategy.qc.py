# Original QuantConnect / library Python
# locale=en slug="cross-sectional-one-month-equity-atm-straddle-trading-strategy"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
from pandas.core.frame import DataFrame
from pandas.core.series import Series
#endregion
class CrossSectionalOneMonthEquityATMStraddleTradingStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2012, 1, 1)
    self.SetCash(1000000)
    
    self.tickers_to_ignore: List[str] = ['DFG']
    self.min_expiry: int = 20
    self.max_expiry: int = 45
    self.period: int = 21 # need n of stock daily prices
    self.percentage_traded: float = 0.2
    self.min_share_price: int = 10
    self.leverage: int = 5
    self.quantile: int = 10
    self.min_contracts: int = 2
    self.day: int = -1
    
    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = True
    self.data: Dict[Symbol, RollingWindow] = {}
    self.symbols_by_ticker: Dict[str, Symbol] = {}
    self.subscribed_contracts: Dict[Symbol, Contracts] = {}
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
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
    
    # rebalance, when contracts expiried
    if not self.selection_flag:
        return Universe.Unchanged
    
    # select top n stocks by dollar volume
    selected: List[Fundamental] = [
        x for x in fundamental
        if x.HasFundamentalData
        and x.Market == 'usa'
        and x.Price > self.min_share_price
        and x.Symbol.Value not in self.tickers_to_ignore
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
    
    # check if any of the subscribed contracts expired
    for _, symbol in self.symbols_by_ticker.items():
        if symbol in self.subscribed_contracts and self.subscribed_contracts[symbol].expiry_date  0 and len(puts) > 0:
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
                        expiry_date: datetime.date = call.ID.Date.date() if call.ID.Date.date()  List[Symbol]:
    ''' filter call and put contracts from contracts parameter '''
    ''' return call and put contracts '''
    
    # Straddle
    call_strike: float = min(strikes, key=lambda x: abs(x-underlying_price))
    put_strike: float = call_strike
    
    calls: List[Symbol] = [] # storing call contracts
    puts: List[Symbol] = [] # storing put contracts
    
    for contract in contracts:
        # check if contract has one month expiry
        if self.min_expiry  None:
    ''' subscribe option contract, set price mondel and normalization mode '''
    option = self.AddOptionContract(contract, Resolution.Daily)
    option.PriceModel = OptionPriceModels.CrankNicolsonFD()
    
def GetImpliedVolatilities(self, contracts: List[Symbol]) -> float:
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
    
def GetHistoricalVolatility(self, rolling_window_prices: RollingWindow) -> np.ndarray:
    ''' calculate historical volatility based on daily prices in rolling_window_prices parameter '''
    prices: np.ndarray = np.array([x for x in rolling_window_prices])
    returns: np.ndarray = (prices[:-1] - prices[1:]) / prices[1:]
    return np.std(returns)
    
def TradeOptions(self, 
                data: Slice, 
                symbols: List[Symbol], 
                long_flag: bool) -> None:
    ''' on long signal buy call and put option contract '''
    ''' on short signal sell call and put option contract '''
    length: int = len(symbols)
    
    # trade etf's call and put contracts
    for symbol in symbols:
        # get call and put contract
        call, put = self.subscribed_contracts[symbol].contracts
        
        # get underlying price
        underlying_price: float = self.subscribed_contracts[symbol].underlying_price
        
        options_q: int = int(((self.Portfolio.TotalPortfolioValue * self.percentage_traded) / length) / (underlying_price * 100))
        
        if call in data and data[call] and put in data and data[put]:
            if long_flag:
                self.Buy(call, options_q)
                self.Buy(put, options_q)
            else:
                self.Sell(call, options_q)
                self.Sell(put, options_q)
    
class Contracts():
def __init__(self, expiry_date: datetime.date, underlying_price: float, contracts: List[Symbol]) -> None:
    self.expiry_date: datetime.date = expiry_date
    self.underlying_price: float = underlying_price
    self.contracts: List[Symbol] = contracts
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
