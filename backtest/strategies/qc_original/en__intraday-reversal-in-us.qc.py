# Original QuantConnect / library Python
# locale=en slug="intraday-reversal-in-us"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
from pandas.core.frame import DataFrame
from pandas.core.series import Series
#endregion
class IntradayReversalInUS(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100_000)
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']	 
    self.quantile: int = 10
    self.leverage: int = 5
    self.min_share_price: int = 5
    self.percentage_threshold: float = 0.05
    self.data: Dict[Symbol, SymbolData] = {} # Storing important data for each selected stock in this strategy
    self.selected_symbols: List[Symbol] = []
    
    self.fundamental_count: int = 100
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Each day select stocks for trading
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.Market == 'usa' 
        and x.Price > self.min_share_price
        and x.MarketCap != 0
        and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    # Create list of selected symbols and create SymbolData object for each of these stocks
    for stock in selected:
        symbol: Symbol = stock.Symbol
        
        # Create SymbolData object and store stock's market capitalization
        self.data[symbol] = SymbolData(stock.MarketCap)
        
        self.selected_symbols.append(symbol)
    
    return self.selected_symbols
def OnData(self, data: Slice) -> None:
    selected: List[Symbol] = []
    
    # Calculate overnight return
    if self.Time.hour == 10 and self.Time.minute == 0:
        
        # Select only stocks, which return in absolute value isn't greater than 5% 
        for symbol in self.selected_symbols:
            if symbol in data and data[symbol]:
                # Get current price from data object
                current_price: float = data[symbol].Value
                
                # Store current price, for next calculation
                self.data[symbol].open_price = current_price
                
                # Use history to get last close
                history: DataFrame = self.History(symbol, 1, Resolution.Daily)
                
                if history.empty:
                    continue
                
                # Get last close from history
                closes: Series = history.loc[symbol].close
                close: float = closes[0]
                
                # Calculate over night return
                over_night_return: float = (current_price - close) / close 
                
                # Select current stock, if stock's absolute value of over night return is equal or smaller than 5%                   
                if abs(over_night_return)  None:
    self.market_cap: float = market_cap
    self.open_price: Union[None, float] = None
    self.over_night_return: Union[None, float] = None
    self.daily_return: Union[None, float] = None
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0
    return OrderFee(CashAmount(fee, "USD"))
