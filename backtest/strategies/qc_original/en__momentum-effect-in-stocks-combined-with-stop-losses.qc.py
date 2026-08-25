# Original QuantConnect / library Python
# locale=en slug="momentum-effect-in-stocks-combined-with-stop-losses"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
class MomentumEffectStocksCombinedStopLosses(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.period:int = 7
    self.leverage:int = 10
    self.quantile:int = 10
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    # Symbol data.
    self.data:Dict[Symbol, SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}
    
    # Opened stop-orders.
    self.opened_orders:List[OrderTicket] = []
    
    self.last_month:int = -1
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.schedule.on(self.date_rules.month_start(market),
                    self.time_rules.after_market_open(market),
                    self.selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        symbol:Symbol = security.Symbol
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    # Update the rolling window every month.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0 and \
        x.SecurityReference.ExchangeId in self.exchange_codes and x.CompanyReference.IsREIT == 0]
    if len(selected) > self.fundamental_count:
    	selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]] 
    
    performance:Dict[Fundamental, float] = {}
    # Warmup price rolling windows.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history = self.History(symbol, self.period*30, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes = history.loc[symbol].close
            
            closes_len = len(closes.keys())
            # Find monthly closes.
            for index, time_close in enumerate(closes.items()):
                # index out of bounds check.
                if index + 1 = self.quantile:
        sorted_by_return:List = sorted(performance.items(), key = lambda x: x[1], reverse = True)
        quantile:int = int(len(sorted_by_return) / self.quantile)
        long:List[Fundamental] = [x[0] for x in sorted_by_return[:quantile]]
    
        # Market cap weighting.
        mc_sum:float = sum([x.MarketCap for x in long])
        for stock in long:
            self.weight[stock.Symbol] = stock.MarketCap / mc_sum
    return list(self.weight.keys())
    
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # Trade execution.
    for symbol, w in self.weight.items():
        if symbol in data.Keys and data[symbol]:
            curr_price:float = data[symbol].Value
            if curr_price != 0:
                # Unit size calc.
                unit_size:float = self.CalculateOrderQuantity(symbol, w)
        
                # Buy order.
                if unit_size != 0:
                    self.MarketOrder(symbol, unit_size)
        
                    # SL setting.
                    sl_price:float = curr_price * 0.95    # 5% SL.
                    ticket:OrderTicket = self.StopMarketOrder(symbol, -unit_size, sl_price, 'SL')
                    self.opened_orders.append(ticket)
    
    self.weight.clear()
def selection(self) -> None:
    self.selection_flag = True
    # Liquidate and cancel pending orders.
    self.Liquidate()
    for ticket_index in range(len(self.opened_orders)-1, 0, -1):
        response = self.opened_orders[ticket_index].Cancel("Canceled Trade")
        self.opened_orders.remove(self.opened_orders[ticket_index])
class SymbolData():
def __init__(self, period: int):
    self._price:RollingWindow = RollingWindow[float](period)

def update(self, price: float) -> None:
    self._price.Add(price)
    
def is_ready(self) -> bool:
    return self._price.IsReady
    
# 12 month momentum, one month skipped.
def performance(self) -> float:
    return self._price[1] / self._price[self._price.Count - 1] - 1
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
