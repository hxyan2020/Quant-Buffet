# Original QuantConnect / library Python
# locale=en slug="esg-level-factor-investing-strategy-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from numpy import floor
from typing import List, Dict
from dataclasses import dataclass
from decimal import *
#endregion
class ESGFactorInvestingStrategy(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2009, 6, 1)
    self.SetCash(100_000)
    # Decile weighting.
    # True - Value weighted
    # False - Equally weighted
    self.value_weighting: bool = True
    
    # self.symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.esg_data: Data = self.AddData(ESGData, 'ESG', Resolution.Daily)
    
    # All tickers from ESG database.
    self.tickers: List[str] = []
    
    self.ticker_deciles: Dict[str, float] = {}
    
    self.holding_period: float = 12
    self.leverage: int = 10
    self.threshold: List[int] = [0.2, 0.8]
    self.managed_queue: List[RebalanceQueueItem] = []
    
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
        and (x.Symbol.Value).lower() in self.tickers
    ]
    
    for stock in selected:
        symbol: Symbol = stock.Symbol
        self.latest_price[symbol] = stock.AdjustedPrice
    # Store symbol/market cap pair.
    long: List[Fundamental] = [
        x for x in selected if (x.Symbol.Value in self.ticker_deciles) and \
        (self.ticker_deciles[x.Symbol.Value] is not None) and \
        (self.ticker_deciles[x.Symbol.Value] >= self.threshold[1])
    ]
    
    short: List[Fundamental] = [
        x for x in selected if (x.Symbol.Value in self.ticker_deciles) and \
        (self.ticker_deciles[x.Symbol.Value] is not None) and \
        (self.ticker_deciles[x.Symbol.Value]  None:
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
            if ticker_u not in self.ticker_deciles:
                self.ticker_deciles[ticker_u] = None
            
            decile: float = self.esg_data.GetLastData()[ticker]
            self.ticker_deciles[ticker_u] = decile
            
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
                if abs(quantity) >= 1:
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
