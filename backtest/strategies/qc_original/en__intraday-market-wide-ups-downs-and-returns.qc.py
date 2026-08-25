# Original QuantConnect / library Python
# locale=en slug="intraday-market-wide-ups-downs-and-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
from dataclasses import dataclass
# endregion
class IntradayMarketWideUpsDowns(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']	
    data: Equity = self.AddEquity('SPY', Resolution.Minute)
    data.SetFeeModel(CustomFeeModel())
    self.symbol: Symbol = data.Symbol
    
    self.data: Dict[Symbol, SymbolData] = {} # Storing SymbolData for each stocks
    self.selected_stocks: List[Symbol] = []
    
    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Rebalance monthly
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    # Filter universe
    selected: List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]    
        
    # Add filtered stocks in self.data dictionary
    for stock in selected:
        symbol: Symbol = stock.Symbol
        self.data[symbol] = SymbolData()
    
    # Store selected stocks symbols in self.selected_stocks parameter
    self.selected_stocks = list(map(lambda x:x.Symbol, selected))
    
    return self.selected_stocks
    
def OnData(self, data: Slice) -> None:
    # Trade stocks at this time
    if self.Time.hour == 9 and self.Time.minute == 45 and len(self.selected_stocks) > 0:
        # Diffrence between upwards and downwards
        difference: Union[None, float] = None
        
        # Make calculation for each stock in self.selected_stocks
        for symbol in self.selected_stocks:
            # Check if symbol is in data slices and stock with this symbol has close price
            if symbol in data and data[symbol] and self.data[symbol].close:
                price: float = data[symbol].Value
                
                # Make sure, that trade is make based on difference
                if difference == None:
                    difference = 0
                    
                # If stock's current price is greater than it's close,
                # then it is upwards stock, otherwise it is downwards stock
                if price > self.data[symbol].close:
                    difference += 1
                else:
                    difference -= 1
        
        # Trade only if it calculated difference
        if difference != None:
            # Calculate uds based od difference between upwards and downwards divided by total count of selected stocks            
            uds: float = difference / len(self.selected_stocks)
            trade_direction: int = 1 if uds >= 0 else -1
            
            self.SetHoldings(self.symbol, trade_direction)
        
    # Store close prices and liquidate portfolio
    if self.Time.hour == 15 and self.Time.minute == 59 and len(self.selected_stocks) != 0:
        
        # Update closes of stocks
        for symbol in self.selected_stocks:
            # Check if symbol is in data slices
            if symbol in data and data[symbol]:
                self.data[symbol].close = data[symbol].Value
            
        # Liquidate portfolio
        self.Liquidate()
    
def Selection(self) -> None:
    self.selection_flag = True
    
@dataclass
class SymbolData():
close: Union[None, float] = None
open: Union[None, float] = None
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
