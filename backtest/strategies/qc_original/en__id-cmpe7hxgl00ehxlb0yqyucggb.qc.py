# Original QuantConnect / library Python
# locale=en slug="股票中的趋势跟随效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgoLib import *

class TrendFollowingEffectinStocks(XXX):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)

    self.fundamental_count:int = 100
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.long:List[Symbol] = []
    
    self.max_close:Dict[Symbol, float] = {}
    self.atr:Dict[Symbol, AverageTrueRange] = {}
    self.atr_period:int = 10
    
    self.sl_order:Dict[Symbol, OrderTicket] = {}
    self.sl_price:Dict[Symbol, float] = {}
    
    self.selection:List[Symbol] = []
    self.period:int = 10*12*21
    self.min_share_price:float = 5.
    
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        
        symbol = security.Symbol
        if symbol not in self.atr:
            self.atr[symbol] = self.ATR(symbol, self.atr_period, Resolution.Daily)
            
        if symbol not in self.max_close:
            hist = self.History([self.Symbol(symbol)], self.period, Resolution.Daily)
            if 'close' in hist.columns:
                closes:pd.Series = hist['close']
                self.max_close[symbol] = max(closes)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> None:
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.AdjustedPrice >= self.min_share_price]

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    self.selection = list(map(lambda x: x.Symbol, selected))
    
    return self.selection

def OnData(self, data: Slice) -> None:
    if self.IsWarmingUp:
        return

    for symbol in self.selection:
        if symbol in data.Bars:
            price:float = data[symbol].Value
        
            if symbol not in self.max_close: continue
        
            if price >= self.max_close[symbol]:
                self.max_close[symbol] = price
                self.long.append(symbol)

    stocks_invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    count:int = len(self.long) + len(stocks_invested)
    if count == 0: return

    # Update stoploss orders
    for symbol in stocks_invested:
        if not self.Securities[symbol].IsTradable:
            self.Liquidate(symbol)
            
        if self.atr[symbol].Current.Value == 0: continue
        
        # Move SL
        if symbol not in self.sl_price: continue
        
        self.SetHoldings(symbol, 1 / count)
        
        new_sl = self.Securities[symbol].Price - self.atr[symbol].Current.Value
        if new_sl > self.sl_price[symbol]:
            update_order_fields = UpdateOrderFields()
            update_order_fields.StopPrice = new_sl      # Update SL price
            
            quantity:float = self.CalculateOrderQuantity(symbol, (1 / count))
            update_order_fields.Quantity = quantity     # Update SL quantity

            self.sl_price[symbol] = new_sl
            self.sl_order[symbol].Update(update_order_fields)

    # Open new trades
    for symbol in self.long:
        if not self.Portfolio[symbol].Invested and self.atr[symbol].Current.Value != 0:
            price:float = data[symbol].Value
            if self.Securities[symbol].IsTradable:
                unit_size:float = self.CalculateOrderQuantity(symbol, (1 / count))
                
                self.MarketOrder(symbol, unit_size)
                
                sl_price:float = price - self.atr[symbol].Current.Value
                self.sl_price[symbol] = sl_price
                if unit_size != 0:
                    self.sl_order[symbol] = self.StopMarketOrder(symbol, -unit_size, sl_price, 'SL')

    self.long.clear()

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
