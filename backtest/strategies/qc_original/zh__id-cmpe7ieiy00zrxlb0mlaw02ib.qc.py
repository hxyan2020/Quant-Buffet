# Original QuantConnect / library Python
# locale=zh slug="利用期权信息在股票市场中获利"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List
class ExploitingOptionInformationintheEquityMarket(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(1000000)
    
    self.min_expiry:int = 25
    self.max_expiry:int = 35
    
    self.daily_period:int = 21              # stock daily price period
    self.vol_skew_change_period:int = 5     # weekly change in ATM vol skew period
    
    self.min_share_price:int = 5
    self.leverage:int = 20
    self.quantile:int = 5
    self.price_threshold:float = [0.8 , 0.95]
    self.prices:Dict[Symbol, RollingWindow] = {}
    self.symbols_by_ticker:Dict[str, Symbol] = {}
    self.subscribed_contracts:Dict[Symbol, Contracts] = {}
    self.ATM_volatility_skew_values:Dict[Symbol, RollingWindow] = {}
    
    self.day:int = -1
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.fundamental_count:int = 100
    self.selection_flag:bool = True
    self.rebalance_flag:bool = False
    self.wait_one_day = False
    
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
    
    market = self.AddEquity('SPY', Resolution.Minute).Symbol
    self.Schedule.On(self.DateRules.Every(DayOfWeek.Tuesday), self.TimeRules.BeforeMarketClose(market), self.Rebalance)

def Rebalance(self) -> None:
    self.rebalance_flag = True
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
    
    for security in changes.RemovedSecurities:
        symbol:Symbol = security.Symbol
        if symbol in self.ATM_volatility_skew_values:
            # delete ATM vol skew values
            del self.ATM_volatility_skew_values[symbol]
    
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update daily prices of stocks in self.data dictionary
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        if symbol in self.prices:
            self.prices[symbol].Add(stock.AdjustedPrice)
    
    # rebalance, when contracts expiried
    if not self.selection_flag:
        return Universe.Unchanged
    
    # select top n stocks by dollar volume
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price > self.min_share_price
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    selected_symbols:List[Symbol] = []
            
    for stock in selected:
        symbol:Symbol = stock.Symbol
        ticker:str = symbol.Value 
        
        selected_symbols.append(symbol)
        self.symbols_by_ticker[ticker] = symbol
        
        if symbol in self.prices:
            continue
        
        self.prices[symbol] = RollingWindow[float](self.daily_period)
        history:DataFrame = self.History(symbol, self.daily_period, Resolution.Daily)
        if history.empty:
            continue
        closes:Series = history.loc[symbol].close
        for time, close in closes.items():
            self.prices[symbol].Add(close)
    # return newly selected symbols
    return selected_symbols
def OnData(self, data: Slice) -> None:
    # execute once a day
    if self.day == self.Time.day:
        return
    if not (self.Time.hour == 9 and self.Time.minute == 31):
        return
    self.day = self.Time.day
    
    # check if any of the subscribed contracts expired
    for _, symbol in self.symbols_by_ticker.items():
        if symbol in self.subscribed_contracts and self.subscribed_contracts[symbol].expiry_date  0 and len(atm_puts) > 0 and len(otm_puts) > 0:
                        # sort by expiry
                        atm_call:Symbol = sorted(atm_calls, key = lambda x: x.ID.Date, reverse=True)[0]
                        atm_put:Symbol = sorted(atm_puts, key = lambda x: x.ID.Date, reverse=True)[0]
                        otm_put:Symbol = sorted(otm_puts, key = lambda x: x.ID.Date, reverse=True)[0]
                        
                        subscriptions = self.SubscriptionManager.SubscriptionDataConfigService.GetSubscriptionDataConfigs(atm_call.Underlying)
                        if subscriptions:
                            # add contracts
                            self.AddContract(atm_call)
                            self.AddContract(atm_put)
                            self.AddContract(otm_put)
                            
                            # retrieve expiry date for contracts
                            expiry_date:datetime.date = atm_call.ID.Date.date() if atm_call.ID.Date.date()  dict:
    collection_values = list(collection.values())
    # median
    collection_values_median:float = np.median(collection_values)
    # avg
    collection_values_avg:float = np.mean(collection_values)
    # median absolute deviation
    collection_med:float = np.median(np.array([abs(x-collection_values_median) for x in collection_values]))
    
    max_cap:int = 3
    result:dict = { x[0]: min(max_cap, max((x[1] - collection_values_avg) / collection_med, -max_cap)) for x in collection.items() }
    
    return result

def FilterContracts(self, strikes, contracts, underlying_price, option_type) -> tuple():
    ''' filter call and put contracts from contracts parameter '''
    ''' returns call and put contracts tuple '''
    
    strike:float = None
    if option_type == OptionType.ATM:
        # at the money strike
        strikes:List[float] = [x for x in strikes if x > self.price_threshold[1] *underlying_price]
        if len(strikes) != 0:
            strike:float = min(strikes, key=lambda x: abs(x-underlying_price))
    elif option_type == OptionType.OTM:
        # out the money 
        strikes:List[float] = [x for x in strikes if x  self.price_threshold[0] *underlying_price]
        if len(strikes) != 0:
            strike:float = min(strikes, key=lambda x: abs(x-(underlying_price* self.price_threshold[0])))
    
    calls:List[Symbol] = [] # storing call contracts
    puts:List[Symbol] = [] # storing put contracts
    if strike is not None:
        for contract in contracts:
            # check if contract has one month expiry
            if self.min_expiry  float:
    ''' calculate historical volatility based on daily prices in rolling_window_prices parameter '''
    prices:np.ndarray = np.array([x for x in rolling_window_prices])
    returns:np.ndarray = (prices[:-1] - prices[1:]) / prices[1:]
    return np.std(returns)
from enum import Enum
class OptionType(Enum):
ATM:str = 'atm'
OTM:str = 'otm'
ITM:str = 'itm'
class Contracts():
def __init__(self, expiry_date:datetime.date, underlying_price:float, atm_call:Symbol, atm_put:Symbol, otm_put:Symbol) -> None:
    self.expiry_date:datetime.date = expiry_date
    self.underlying_price:float = underlying_price
    # self.contracts = contracts  # = [atm_call, atm_put, otm_put]
    self.atm_call:Symbol = atm_call
    self.atm_put:Symbol = atm_put
    self.otm_put:Symbol = otm_put

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
