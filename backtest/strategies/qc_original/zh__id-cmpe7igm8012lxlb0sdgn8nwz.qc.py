# Original QuantConnect / library Python
# locale=zh slug="期权-股票成交量比率预测股票回报"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
#endregion
class OptionStockVolumeRatioPredictsStockReturns(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2020, 1, 1)
    self.SetCash(100_000)
    
    self.min_expiry: int = 20
    self.max_expiry: int = 30
    self.min_period_len: int = 14      # need at least n daily volumes
    self.quantile: int = 5
    self.leverage: int = 5
    self.min_share_price: int = 5
    
    self.last_fundamental: List[Symbol] = []
    self.data: Dict[Symbol, SymbolData] = {}                     # list of stocks volumes and list of total option volumes in selection 
    self.subscribed_contracts: Dict[Symbol, Contracts] = {}      # subscribed option universe
    
    # initial data feed
    self.AddEquity('SPY', Resolution.Minute)
    
    self.fundamental_count: int = 50
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = True
    self.subscribing_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # rebalance monthly
    if not self.selection_flag:
        return Universe.Unchanged
    # change flags values
    self.selection_flag = False
    self.subscribing_flag = True
    
    # filter top n U.S. stocks by dollar volume
    selected: List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData 
        and x.Market == 'usa' 
        and x.Price > self.min_share_price
        and x.Symbol.Value != 'GOOG']
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # filter top n U.S. stocks by dollar volume
    # initialize new fundamental 
    self.last_fundamental = [x.Symbol for x in selected]
    # return newly selected symbols
    return self.last_fundamental
    
def OnData(self, data: Slice) -> None:
    for stock_symbol in self.last_fundamental:
        # stock has to have subscribed option contracts
        if stock_symbol not in self.subscribed_contracts:
            continue
        
        # check if any of the subscribed contracts expired
        if self.subscribed_contracts[stock_symbol].expiry_date - timedelta(days=1) = self.quantile:
            # perform selection
            quantile: int = int(len(OS_ratio) / self.quantile)
            sorted_by_ratio: List[Symbol] = [x[0] for x in sorted(OS_ratio.items(), key=lambda item: item[1])]
            
            # long low and short high 
            long: List[Symbol] = sorted_by_ratio[:quantile]
            short: List[Symbol] = sorted_by_ratio[-quantile:]
            
            targets: List[PortfolioTarget] = []
            for i, portfolio in enumerate([long, short]):
                for symbol in portfolio:
                    if symbol in data and data[symbol]:
                        targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
            
            self.SetHoldings(targets, True)
        
        elif not self.selection_flag:
            # liquidate all positions from previous selection
            self.Liquidate()
        
        # clear for next selection
        self.last_fundamental.clear()
        
        self.selection_flag = True
        
        return # skip to firstly perform fundamental selection and then contracts subscribing
    
    # subscribe to new contracts after selection
    if len(self.subscribed_contracts) == 0 and self.subscribing_flag:
        for symbol in self.last_fundamental:
            # get all contracts for current stock symbol
            contracts: List[Symbol] = self.OptionChainProvider.GetOptionContractList(symbol, self.Time)
            # get current price for etf
            underlying_price: float = self.Securities[symbol].Price
            
            # get strikes from commodity future contracts
            strikes: List[float] = [i.ID.StrikePrice for i in contracts]
            
            # can't filter contracts, if there isn't any strike price
            if len(strikes)  0 and len(atm_puts) > 0 and len(itm_calls) > 0 and len(itm_puts) > 0 and len(otm_calls) > 0 and len(otm_puts) > 0:
                # sort by expiry
                atm_call, atm_put = self.SortByExpiry(atm_calls, atm_puts)
                itm_call, itm_put = self.SortByExpiry(itm_calls, itm_puts)
                otm_call, otm_put = self.SortByExpiry(otm_calls, otm_puts)
                
                atm_call_subscriptions: List[SubscriptionDataConfig] = self.SubscriptionManager.SubscriptionDataConfigService.GetSubscriptionDataConfigs(atm_call.Underlying)
                
                # check if stock's call and put contract was successfully subscribed
                if atm_call_subscriptions:
                    selected_contracts: List[Symbol] = [atm_call, atm_put, itm_call, itm_put, otm_call, otm_put]
                    
                    for contract in selected_contracts:
                        # add contract
                        self.AddOptionContract(contract, Resolution.Minute)
                        
                    # retrieve expiry date for contracts
                    expiry_date: datetime.date = min([c.ID.Date.date() for c in selected_contracts])
                    # store contracts with expiry date under stock's symbol
                    self.subscribed_contracts[symbol] = Contracts(expiry_date, underlying_price, selected_contracts)
        
        # at least one stock has to have successfully subscribed all option contracts, to stop subscribing
        if len(self.subscribed_contracts) > 0:
            self.subscribing_flag = False
    
def FilterContracts(self, strike: float, contracts: List[Symbol], underlying_price: float) -> List[Symbol]:
    ''' filter call and put contracts from contracts parameter '''
    ''' return call and put contracts '''
    
    calls: List[Symbol] = [] # storing call contracts
    puts: List[Symbol] = [] # storing put contracts
    
    for contract in contracts:
        # check if contract has one month expiry
        if self.min_expiry  List[Symbol]:
    ''' return option call and option put with farest expiry '''
    
    call: List[Symbol] = sorted(calls, key = lambda x: x.ID.Date, reverse=True)[0]
    put: List[Symbol] = sorted(puts, key = lambda x: x.ID.Date, reverse=True)[0]
    
    return call, put
    
class SymbolData:
def __init__(self) -> None:
    self.stock_minute_volumes: List[float] = []
    self.options_minute_volumes: List[float] = []
    self.stock_daily_volumes: List[float] = []
    self.total_option_daily_volumes: List[float] = []
    
def update_daily_volumes(self) -> None:
    self.stock_daily_volumes.append(sum(self.stock_minute_volumes))
    self.total_option_daily_volumes.append(sum(self.options_minute_volumes))
    
    self.stock_minute_volumes.clear()
    self.options_minute_volumes.clear()
    
def clear_data(self) -> None:
    self.stock_minute_volumes.clear()
    self.options_minute_volumes.clear()
    self.stock_daily_volumes.clear()
    self.total_option_daily_volumes.clear()
    
def is_ready(self, period: int) -> bool:
    return len(self.stock_daily_volumes) >= period and len(self.total_option_daily_volumes) >= period
    
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
