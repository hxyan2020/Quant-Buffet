# Original QuantConnect / library Python
# locale=en slug="bitcoin-leads-altcoins-on-intraday-basis"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from dateutil.relativedelta import relativedelta
import numpy as np
# endregion

class BitcoinLeadsAltcoinsonIntradayBasis(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2017, 1, 1)
    self.SetCash(100000)

    self.period:int = 24
    self.alpha:float = 2.0
    self.beta:float = 1.25
    self.percentile:float = 98
    self.top_count:int = 10
    self.max_traded_duration:int = 4
    self.portion:float = .1
    self.consolidation_bar_count:int = 15

    self.crypto_tickers:List[str] = ['BTCUSD', 'ETHUSD', 'SOLUSD', 'ADAUSD', 'XRPUSD', 'DOTUSD', 'DOGEUSD', 'LUNAUSD', 'AVAXUSD', 'UNIUSD',
                                    'LINKUSD', 'LTCUSD', 'BCHABCUSD', 'BSVUSD', 'FILUSD', 'XLMUSD', 'XTZUSD', 'NEOUSD', 'ATOMUSD', 'IOTAUSD', 
                                    'ETCUSD', 'DASHUSD', 'EGLDUSD', 'AAVEUSD', 'ENJUSD', 'EOSUSD', 'MKRUSD', 'MANAUSD', 'SNXUSD',  
                                    'OMGUSD', 'SUSHIUSD', 'YFIUSD', 'WBTCUSD', 'XMRUSD', 'ZECUSD', 'ZRXUSD', 'XRAUSD', 'AMPLUSD', 'GRTUSD', 
                                    'DGBUSD', '1INCHUSD'] # 'FTTUSD'

    self.data:Dict[Symbol, SymbolData] = {}
    self.btc_returns:List[float] = []
    self.symbol_performance:Dict[Symbol, float] = {}
    self.top_perf_symbols:List[Symbol] = []

    # data subscription
    for ticker in self.crypto_tickers:
        data = self.AddCrypto(ticker, Resolution.Minute, Market.Bitfinex)
        data.SetFeeModel(data_tools.CustomFeeModel())

        self.Consolidate(data.Symbol, timedelta(minutes=self.consolidation_bar_count), self.ConsolidatedBarHandler)

        self.data[data.Symbol] = data_tools.SymbolData(self.period)

    self.trade_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

    self.current_year:int = -1

def OnData(self, data: Slice):
    if self.trade_flag:
        self.trade_flag = False

    # pick top 10 performing cryptos each year
    if self.Time.year == self.current_year:
        return
    self.current_year = self.Time.year

    self.cancel_open_orders(None)
    self.top_perf_symbols.clear()
    self.btc_returns = self.btc_returns[-self.period:]

    top_perf_symbols:Dict[Symbol, float] = { symbol: symbol_data._performance for symbol, symbol_data in self.data.items() if symbol_data._performance != 0 }
    self.top_perf_symbols = sorted(top_perf_symbols, key=top_perf_symbols.get, reverse=True)[:self.top_count]

def ConsolidatedBarHandler(self, consolidated: Slice) -> None:
    symbol_data = self.data[consolidated.Symbol]

    # save performance on each crypto
    if symbol_data.is_traded():
        symbol_data._count += 1

        # count in performance for optimization
        if consolidated.High > symbol_data._tp_price and consolidated.Low = symbol_data._tp_price and consolidated.Low > symbol_data._sl_price:
            symbol_data.update_performance(symbol_data._tp_price / symbol_data._open_price - 1)
        elif consolidated.High = self.max_traded_duration:
            symbol_data.update_performance(consolidated.Close / symbol_data._open_price - 1)
            
            if self.Portfolio[consolidated.Symbol].Invested:
                self.cancel_open_orders(consolidated.Symbol)
                self.MarketOrder(consolidated.Symbol, -self.Portfolio[consolidated.Symbol].Quantity, tag='1 hour threshold')

    if consolidated.Symbol in self.data:
        if consolidated.Symbol.Value == 'BTCUSD':
            if len(self.btc_returns) >= self.period:
                if np.log(consolidated.Close / consolidated.Open) > np.percentile(self.btc_returns, self.percentile):
                    if not any(symbol_data.is_traded() for symbol, symbol_data in self.data.items()):
                        self.trade_flag = True

            self.btc_returns.append(np.log(consolidated.Close / consolidated.Open))
        else:
            # execute trade
            if self.trade_flag:
                if symbol_data.is_ready():
                    price_std:float = symbol_data.get_std()
                    if price_std != 0.:
                        sl_price:float = round(consolidated.Close - self.beta * price_std, 5)
                        tp_price:float = round(consolidated.Close + self.alpha * price_std, 5)

                        symbol_data.trade(consolidated.Close, tp_price, sl_price)
                        
                        # trading when symbol is in actual selection
                        if consolidated.Symbol in self.top_perf_symbols:
                            quantity:int = self.Portfolio.TotalPortfolioValue // len(self.top_perf_symbols) * self.portion // consolidated.Close
                            self.MarketOrder(consolidated.Symbol, quantity, tag='MarketOrder')

            self.data[consolidated.Symbol].update_price(consolidated.Close)

def OnOrderEvent(self, orderEvent: OrderEvent) -> None:
    if orderEvent.Status == OrderStatus.Filled:
        order_ticket = self.Transactions.GetOrderTicket(orderEvent.OrderId)
        
        # NOTE tag text can be altered by LEAN, for example:
        # MarketOrder - Warning: fill at stale price {datetime}, using QuoteBar data.
        # that's the reason 'in' keyword is used
        if 'MarketOrder' in order_ticket.Tag:
            self.StopMarketOrder(order_ticket.Symbol, -order_ticket.Quantity, self.data[order_ticket.Symbol]._sl_price)
            self.LimitOrder(order_ticket.Symbol, -order_ticket.Quantity, self.data[order_ticket.Symbol]._tp_price)

        # either SL or TP
        else:
            self.cancel_open_orders(order_ticket.Symbol)

def cancel_open_orders(self, symbol:Union[Symbol, None]) -> None:
    # cancel all opened orders
    orders_to_cancel = self.Transactions.GetOrderTickets(lambda order_ticket: order_ticket.Status not in [OrderStatus.Filled, OrderStatus.Canceled, OrderStatus.Invalid] and order_ticket.Symbol == symbol) if symbol is not None else \
                       self.Transactions.GetOrderTickets(lambda order_ticket: order_ticket.Status not in [OrderStatus.Filled, OrderStatus.Canceled, OrderStatus.Invalid])

    for ticket in orders_to_cancel:
        response = ticket.Cancel()
