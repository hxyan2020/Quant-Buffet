# Original QuantConnect / library Python
# locale=zh slug="股票中的投资者模糊性策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
#endregion
class InvestorAmbiguityInEquities(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.data:Dict[Symbol, SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}
    
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.period:int = 21 * 2 # need n daily volumes and n + 1 daily prices
    self.quantile:int = 10
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol, 0), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice, stock.Volume)
            
    # rebalance monthly        
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and x.SecurityReference.ExchangeId in self.exchange_codes and x.MarketCap != 0
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    investor_disagreement:Dict[Fundamental, float] = {} 
    # warm up stock prices
    for stock in selected:
        symbol:Symbol = stock.Symbol
        
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history:DataFrame = self.History(symbol, self.period + 1, Resolution.Daily)
            if history.empty:
                continue
            
            if 'close' in history.columns and 'volume' in history.columns:
                closes:pd.Series = history.loc[symbol].close
                volumes:pd.Series = history.loc[symbol].volume
                
                for (_, close), (_, volume) in zip(closes.items(), volumes.items()):
                    self.data[symbol].update(close, volume)
        
        if self.data[symbol].are_data_ready():
            # calculate investor disagreement value
            investor_disagreement_value = self.data[symbol].investor_disagreement()
            
            # store investor disagreement value keyed by stock
            investor_disagreement[stock] = investor_disagreement_value
        
    # there has to be enough stocks for quantile selection
    if len(investor_disagreement)  None:
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def Selection(self):
    self.selection_flag = True
    
class SymbolData():
def __init__(self, period: int) -> None:
    self._prices:RollingWindow = RollingWindow[float](period + 1)
    self._daily_volumes:RollingWindow = RollingWindow[float](period)
    
def update(self, price: float, volume: float) -> None:
    self._prices.Add(price)
    self._daily_volumes.Add(volume)
    
def are_data_ready(self) -> bool:
    return self._prices.IsReady and self._daily_volumes.IsReady
    
def investor_disagreement(self) -> float:
    prices:np.ndarray = np.array([x for x in self._prices])
    daily_volumes:np.ndarray = np.array([x for x in self._daily_volumes])
    absolute_price_changes:np.ndarray = prices[:-1] - prices[1:]
    
    # calculate correlation of daily volume and absolute prices change
    correlation:np.ndarray = np.corrcoef(daily_volumes, absolute_price_changes)
    investor_disagreement_value:float = -1 * correlation[0][1]
    return investor_disagreement_value
     
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
