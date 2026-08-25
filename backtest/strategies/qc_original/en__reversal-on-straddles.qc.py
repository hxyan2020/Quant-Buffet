# Original QuantConnect / library Python
# locale=en slug="reversal-on-straddles"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
from dataclasses import dataclass
#endregion
class ReversalOnStraddles(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100_000)
    
    self.leverage: int = 20
    self.quantile: int = 5
    self.min_share_price: int = 5
    self.min_expiry: int = 20
    self.max_expiry: int = 30
    
    self.min_daily_period: int = 14          # need n straddle prices
     
    self.last_fundamental: List[Symbol] = []
    
    self.straddle_price_sum: Dict[Symbol, float] = {}        # call and put price sum
    self.subscribed_contracts: Dict[Symbol, Contracts] = {}      # subscribed option universe
    
    # initial data feed
    self.AddEquity('SPY', Resolution.Daily)
    
    self.fundamental_count: int = 200
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    self.rebalance_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # rebalance monthly
    if not self.selection_flag:
        return Universe.Unchanged
    self.rebalance_flag = True
    
    # filter top n U.S. stocks by dollar volume
    selected: List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price > self.min_share_price]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    # initialize new fundamental 
    self.last_fundamental = [x.Symbol for x in selected]
    # return newly selected symbols
    return self.last_fundamental
    
def OnData(self, data: Slice) -> None:
    # execute once a day
    # if not (self.Time.hour == 9 and self.Time.minute == 31):
    #     return
    
    for symbol in self.last_fundamental:
        # check if any of the subscribed contracts expired
        if symbol in self.subscribed_contracts and self.subscribed_contracts[symbol].expiry_date - timedelta(days=1)  0 and len(puts) > 0:
                # sort by expiry
                call: Symbol = sorted(calls, key = lambda x: x.ID.Date, reverse=True)[0]
                put: Symbol = sorted(puts, key = lambda x: x.ID.Date, reverse=True)[0]
                
                subscriptions = self.SubscriptionManager.SubscriptionDataConfigService.GetSubscriptionDataConfigs(call.Underlying)
                # check if stock's call and put contract was successfully subscribed
                if subscriptions:
                    # add call contract
                    self.AddOptionContract(call, Resolution.Daily)
                    # add put contract
                    self.AddOptionContract(put, Resolution.Daily)
                    
                    # retrieve expiry date for contracts
                    expiry_date: datetime.date = call.ID.Date.date() if call.ID.Date.date()  self.min_daily_period:
                continue
            
            # calculate straddle performance
            straddle_performance[symbol] = self.straddle_price_sum[symbol][-1] / self.straddle_price_sum[symbol][0] - 1
            
            # reset straddle prices for next month
            self.straddle_price_sum[symbol] = []
        # make sure there are enough stock's for quintile selection
        if len(straddle_performance)  Symbol:
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
    ''' on long signal buy call and put option contract '''
    ''' on short signal sell call and put option contract '''
    length: int = len(symbols)
    
    # trade etf's call and put contracts
    for symbol in symbols:
        # get call and put contract
        call, put = self.subscribed_contracts[symbol].contracts
        
        # get underlying price
        underlying_price: float = self.subscribed_contracts[symbol].underlying_price
        
        # calculate option and hedge quantity
        options_q: int = int((self.Portfolio.TotalPortfolioValue / length) / (underlying_price * 100))
        hedge_q: int = options_q*50
        
        if long_flag:
            self.Buy(call, options_q)
            self.Buy(put, options_q)
            
            # initial delta hedge
            self.Sell(symbol, hedge_q)
        else:
            self.Sell(call, options_q)
            self.Sell(put, options_q)
            
            # initial delta hedge
            self.Buy(symbol, hedge_q)
@dataclass
class Contracts():
expiry_date: datetime.date
underlying_price: float
contracts: List[Symbol]
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
