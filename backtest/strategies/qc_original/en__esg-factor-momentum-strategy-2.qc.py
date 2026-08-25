# Original QuantConnect / library Python
# locale=en slug="esg-factor-momentum-strategy-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from numpy import floor
from collections import deque
from typing import List, Dict, Tuple
from dataclasses import dataclass
from decimal import *
#endregion
class ESGFactorMomentumStrategy(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2009, 6, 1)
    self.SetCash(100_000)
    
    # Decile weighting.
    # True - Value weighted
    # False - Equally weighted
    self.value_weighting: bool = True
    
    self.esg_data: Security = self.AddData(ESGData, 'ESG', Resolution.Daily)
    self.tickers: List[str] = []
    
    self.holding_period: int = 3
    self.managed_queue: List[RebalanceQueueItem] = []
    self.quantile: int = 10
    self.leverage: int = 10
    # Monthly ESG decile data.
    self.esg: Dict[str, RollingWindow[float]] = {}
    self.period: int = 14
    
    self.latest_price: Dict[Symbol, float] = {}
    
    self.selection_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    self.latest_price.clear()
    
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.MarketCap != 0
        and (x.Symbol.Value).lower() in self.tickers]
    
    for stock in selected:
        symbol: Symbol = stock.Symbol
        self.latest_price[symbol] = stock.AdjustedPrice
    momentum: Dict[Fundamental, float] = {}
    
    # Momentum calc.
    for stock in selected:
        symbol: Symbol = stock.Symbol
        ticker: str = symbol.Value
        # ESG data for 14 months is ready.
        if ticker in self.esg and self.esg[ticker].IsReady:
            esg_data: List[float] = [x for x in self.esg[ticker]]
            
            esg_decile_2_months_ago: float = esg_data[1]
            esg_decile_14_months_ago: float = esg_data[13]
            
            if esg_decile_14_months_ago != 0 and esg_decile_2_months_ago != 0:
                # Momentum as difference.
                # momentum_ = esg_decile_2_months_ago - esg_decile_14_months_ago
                
                # Momentum as ratio.
                momentum_: float = (esg_decile_2_months_ago / esg_decile_14_months_ago) - 1
                
                # Store momentum/market cap pair.
                momentum[stock] = momentum_
    
    if len(momentum)  None:
    new_data_arrived: bool = False
    custom_data_last_update_date: datetime.date = ESGData.get_last_update_date()
    if self.esg_data.get_last_data() and self.time.date() > custom_data_last_update_date:
        self.liquidate()
        return
    if slice.contains_key('ESG') and slice['ESG']:
        # Store universe tickers.
        if len(self.tickers) == 0:
            # TODO '_typename' in storage dictionary?
            self.tickers = [x.Key for x in self.esg_data.GetLastData().GetStorageDictionary()][1:-1]
    
        # Store history for every ticker.
        for ticker in self.tickers:
            ticker_u: str = ticker.upper()
            if ticker_u not in self.esg:
                self.esg[ticker_u] = RollingWindow[float](self.period)
            
            decile: float = self.esg_data.GetLastData()[ticker]
            self.esg[ticker_u].Add(decile)
            
            # trigger selection after new esg data arrived.
            if not self.selection_flag:
                new_data_arrived = True
    
    if new_data_arrived:
        self.selection_flag = True
        return
    
    if not self.selection_flag:
        return
    self.selection_flag = False
    # Trade execution
    remove_item: Union[None, RebalanceQueueItem] = None
    
    # Rebalance portfolio
    for item in self.managed_queue:
        if item.holding_period == self.holding_period:
            for symbol, quantity in item.symbol_q:
                self.MarketOrder(symbol, -quantity)
                        
            remove_item = item
            
        elif item.holding_period == 0:
            open_symbol_q: List[RebalanceQueueItem] = []
            
            for symbol, quantity in item.symbol_q:
                if quantity >= 1:
                    if slice.contains_key(symbol) and slice[symbol]:
                        self.MarketOrder(symbol, quantity)
                        open_symbol_q.append((symbol, quantity))
                        
            # Only opened orders will be closed        
            item.symbol_q = open_symbol_q
            
        item.holding_period += 1
        
    if remove_item:
        self.managed_queue.remove(remove_item)
@dataclass
class RebalanceQueueItem():
# symbol/quantity collections
symbol_q: List[Tuple[Symbol, float]] 
holding_period: int = 0
# ESG data.
class ESGData(PythonData):
_last_update_date:datetime.date = datetime(1,1,1).date()
@staticmethod
def get_last_update_date() -> datetime.date:
   return ESGData._last_update_date
def __init__(self):
    self.tickers = []

def GetSource(self, config: SubscriptionDataConfig, date: datetime, isLiveMode: bool) -> SubscriptionDataSource:
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/economic/esg_deciles_data.csv", SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)

def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:
    data = ESGData()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit():
        self.tickers = [x for x in line.split(';')][1:]
        return None
        
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    index = 1
    for ticker in self.tickers:
        data[ticker] = float(split[index])
        index += 1
        
    data.Value = float(split[1])
    if data.Time.date() > ESGData._last_update_date:
        ESGData._last_update_date = data.Time.date()
    return data
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
