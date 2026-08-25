# Original QuantConnect / library Python
# locale=zh slug="期权-股票成交量比率变化预测股票回报"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
from dataclasses import dataclass
#endregion
class ChangeInOptionStockVolumeRatioPredictsStockReturns(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2014, 1, 1)
    self.SetCash(100000)
    
    self.tickers_to_ignore: List[str] = ['AMD', 'TSLA', 'MSFT']
    self.min_expiry: int = 20
    self.max_expiry: int = 30
    self.period: int = 6           # need n monthly volumes
    self.min_period_len: int = 14  # need at least n daily volumes and at least n minute volumes  
    self.quantile: int = 5
    self.leverage: int = 15
    self.min_share_price: int = 5
    
    self.current_fundamental: List[Symbol] = []
    self.previous_fundamental: List[Symbol] = []
    self.data: Dict[Symbol, SymbolData] = {}                      
    self.subscribed_contracts: Dict[Symbol, Contracts] = {}  # subscribed option universe
    # initial data feed
    self.AddEquity('SPY', Resolution.Minute)
    
    self.months_counter: int = 1
    self.fundamental_count: int = 100
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = True
    self.subscribing_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Minute
    self.settings.daily_precise_end_time = False
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # rebalance yearly
    if not self.selection_flag:
        return Universe.Unchanged
    
    # change flags values
    self.selection_flag = False
    self.subscribing_flag = True
    # filter top n U.S. stocks by dollar volume
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.Market == 'usa' 
        and x.Price > self.min_share_price
        and x.Symbol.Value not in self.tickers_to_ignore
        ]
    if len(selected) > self.fundamental_count:
        selected = [
            x for x in sorted(
                selected, 
                key=self.fundamental_sorting_key, 
                reverse=True)[:self.fundamental_count]]
    
    for stock in selected:
        symbol: Symbol = stock.Symbol
        self.current_fundamental.append(symbol)
        
        # make sure data are consecutive
        if symbol not in self.data or symbol not in self.previous_fundamental:
            self.data[symbol] = SymbolData(self.period)
        
    # return newly selected symbols
    return self.current_fundamental
    
def OnData(self, data: Slice) -> None:
    for stock_symbol in self.current_fundamental:
        # stock has to have subscribed option contracts
        if stock_symbol not in self.subscribed_contracts:
            continue
        
        if self.Securities[stock_symbol].IsDelisted:
            continue
        # check if any of the subscribed contracts expired
        if self.subscribed_contracts[stock_symbol].expiry_date - timedelta(days=1) = self.quantile:
            # perform selection
            quantile: int = int(len(OS_ratio_change) / self.quantile)
            sorted_by_ratio: List[Symbol] = [x[0] for x in sorted(OS_ratio_change.items(), key=lambda item: item[1])]
            
            # long low and short high 
            long: List[Symbol] = sorted_by_ratio[:quantile]
            short: List[Symbol] = sorted_by_ratio[-quantile:]
            
            # trade execution
            targets: List[PortfolioTarget] = []
            for i, portfolio in enumerate([long, short]):
                for symbol in portfolio:
                    if symbol in data and data[symbol]:
                        targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
            self.SetHoldings(targets, True)
        
        elif not self.selection_flag:
            # liquidate all positions from previous selection
            self.Liquidate()
        
        if len(self.current_fundamental) != 0 and self.months_counter % 12 == 0:
            # reinitialize previous fundamental
            self.previous_fundamental = list(map(lambda symbol: symbol, self.current_fundamental))
            # make space for new stocks from fundamental
            self.current_fundamental.clear()
            # increase month counter
            self.months_counter += 1 
            # perform next selection
            self.selection_flag = True
            
        elif not self.subscribing_flag and len(self.current_fundamental) != 0:
            # perform new subscribtion without selection
            self.subscribing_flag = True
            # increase months counter
            self.months_counter += 1
        
        return # skip to firstly perform fundamental selection and then contracts subscribing
    
    # subscribe to new contracts after selection
    if len(self.subscribed_contracts) == 0 and self.subscribing_flag:
        for symbol in self.current_fundamental:
            if self.Securities[symbol].IsDelisted:
                continue
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
                    expiry_date: datetime.date = atm_call.ID.Date.date() if atm_call.ID.Date.date()  0:
            self.subscribing_flag = False
    
def FilterContracts(self, 
                    strike: float, 
                    contracts: List[Symbol], 
                    underlying_price: float) -> List[Symbol]:
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
def __init__(self, period: int) -> None:
    self.os_ratios: RollingWindow = RollingWindow[float](period)
    
    self.stock_minute_volumes: List[float] = []
    self.options_minute_volumes: List[float] = []
    
    self.stock_daily_volumes: List[float] = []
    self.options_daily_volumes: List[float] = []
    
def update_daily_volumes(self) -> None:
    self.stock_daily_volumes.append(sum(self.stock_minute_volumes))
    self.options_daily_volumes.append(sum(self.options_minute_volumes))
    
    self.stock_minute_volumes.clear()
    self.options_minute_volumes.clear()
    
def update_os_ratios(self) -> None:
    os_ratio_value = sum(self.options_daily_volumes) / sum(self.stock_daily_volumes)
    self.os_ratios.Add(os_ratio_value)
    
    self.stock_daily_volumes.clear()
    self.options_daily_volumes.clear()
    
def clear_data(self) -> None:
    self.stock_minute_volumes.clear()
    self.options_minute_volumes.clear()
    self.stock_daily_volumes.clear()
    self.options_daily_volumes.clear()
    
def daily_volumes_ready(self, period: int) -> bool:
    return len(self.stock_daily_volumes) >= period and len(self.options_daily_volumes) >= period
    
def minute_volumes_ready(self, period: int) -> bool:
    return len(self.stock_minute_volumes) >= period and len(self.options_minute_volumes) >= period
    
def is_ready(self) -> bool:
    return self.os_ratios.IsReady
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
