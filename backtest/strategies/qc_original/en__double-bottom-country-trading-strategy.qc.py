# Original QuantConnect / library Python
# locale=en slug="double-bottom-country-trading-strategy"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
from datetime import datetime
# endregion

class DoubleBottomCountryTradingStrategy(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.country_etfs:List[str] = [
        "EWA",  # iShares MSCI Australia Index ETF
        "EWO",  # iShares MSCI Austria Investable Mkt Index ETF
        "EWK",  # iShares MSCI Belgium Investable Market Index ETF
        "EWZ",  # iShares MSCI Brazil Index ETF
        "EWC",  # iShares MSCI Canada Index ETF
        "FXI",  # iShares China Large-Cap ETF
        "EWQ",  # iShares MSCI France Index ETF
        "EWG",  # iShares MSCI Germany ETF 
        "EWH",  # iShares MSCI Hong Kong Index ETF
        "EWI",  # iShares MSCI Italy Index ETF
        "EWJ",  # iShares MSCI Japan Index ETF
        "EWM",  # iShares MSCI Malaysia Index ETF
        "EWW",  # iShares MSCI Mexico Inv. Mt. Idx
        "EWN",  # iShares MSCI Netherlands Index ETF
        "EWS",  # iShares MSCI Singapore Index ETF
        "EZA",  # iShares MSCI South Africe Index ETF
        "EWY",  # iShares MSCI South Korea ETF
        "EWP",  # iShares MSCI Spain Index ETF
        "EWD",  # iShares MSCI Sweden Index ETF
        "EWL",  # iShares MSCI Switzerland Index ETF
        "EWT",  # iShares MSCI Taiwan Index ETF
        "THD",  # iShares MSCI Thailand Index ETF
        "EWU",  # iShares MSCI United Kingdom Index ETF
        "SPY",  # SPDR S&P 500 ETF
    ]

    self.rolling_period:int = 30

    # two local highs/lows max and min distance
    self.min_distance:int = self.rolling_period
    self.max_distance:int = 1000

    # max vertical distance between two local highs/lows
    self.max_percentage:float = .02

    self.stop_loss_pct:float = .03
    self.take_profit_pct:float = .06

    self.trade_long = True
    self.trade_short = False
    self.max_positions_opened:int = 4

    self.SetWarmup(self.max_distance, Resolution.Daily)

    self.price_data:Dict[str, List[Tuple(datetime.date, float)]] = {}

    # add Forex data
    for etf in self.country_etfs:
        data:Equity = self.AddEquity(etf, Resolution.Daily)
        data.SetLeverage(10)
        self.price_data[etf] = []
    
    self.recent_month:int = -1

def OnData(self, data: Slice) -> None:
    # trail long SL for each opened positions
    active_open_buy_orders:List = list(self.Transactions.GetOrderTickets(lambda ticket: 'LIMIT_BUY' in ticket.Tag and ticket.Status == OrderStatus.Filled))
    for ticket in active_open_buy_orders:
        if self.Portfolio[ticket.Symbol].IsLong:
            active_sl_orders:List = list(self.Transactions.GetOrderTickets(lambda sl_ticket: 'SL' in sl_ticket.Tag \
                                        and sl_ticket.Symbol == ticket.Symbol \
                                        and sl_ticket.Status not in [OrderStatus.Filled, OrderStatus.Invalid, OrderStatus.Canceled]))

            if len(active_sl_orders) != 0:
                active_sl_order = active_sl_orders[0]
                # price moved into profit
                if self.Securities[ticket.Symbol].Price > ticket.Get(OrderField.LimitPrice):
                    new_sl_price:float = round(self.Securities[ticket.Symbol].Price - (self.Securities[ticket.Symbol].Price * self.stop_loss_pct), 2)
                    if new_sl_price > active_sl_order.Get(OrderField.StopPrice):
                        active_sl_order.UpdateStopPrice(new_sl_price)

    # trail short SL for each opened positions
    active_open_buy_orders:List = list(self.Transactions.GetOrderTickets(lambda ticket: 'LIMIT_SELL' in ticket.Tag and ticket.Status == OrderStatus.Filled))
    for ticket in active_open_buy_orders:
        if self.Portfolio[ticket.Symbol].IsShort:
            active_sl_orders:List = list(self.Transactions.GetOrderTickets(lambda sl_ticket: 'SL' in sl_ticket.Tag \
                                        and sl_ticket.Symbol == ticket.Symbol \
                                        and sl_ticket.Status not in [OrderStatus.Filled, OrderStatus.Invalid, OrderStatus.Canceled]))

            if len(active_sl_orders) != 0:
                active_sl_order = active_sl_orders[0]
                # price moved into profit
                if self.Securities[ticket.Symbol].Price = self.max_distance:
            if not self.Portfolio[etf].Invested:
                etf_hist:DataFrame = pd.DataFrame(self.price_data[etf], columns=['Date', etf])
                etf_hist.set_index('Date', inplace=True)
                current_datetime:datetime = etf_hist.index[-1]
                etf_hist = self.find_support_and_resistance(etf, etf_hist, self.rolling_period, self.min_distance)
                etf_hist = self.find_double_tops_and_bottoms(etf, etf_hist, self.min_distance, self.max_distance, self.max_percentage)                    

                if self.trade_long:
                    # find not yet crossed bottom
                    last_bottom_datetime:DataFrame = etf_hist[~etf_hist['Double_Bottom'].isnull()]
                    if not last_bottom_datetime.empty:
                        last_bottom_datetime:datetime = last_bottom_datetime.index[-1]
                        if all(x[1][etf] >= etf_hist.loc[last_bottom_datetime][etf] for x in etf_hist.loc[last_bottom_datetime:current_datetime].iterrows()):
                            limit_price:float = round(etf_hist.loc[last_bottom_datetime][etf], 2)
                            active_limit_orders:List = list(self.Transactions.GetOrderTickets(lambda order_ticket: order_ticket.Status not in [OrderStatus.Filled, OrderStatus.Invalid, OrderStatus.Canceled] and order_ticket.Symbol == etf and 'LIMIT_BUY' in order_ticket.Tag))

                            # submit orders
                            if len(active_limit_orders) != 0:
                                active_order = active_limit_orders[0]
                                # there is active order for different price
                                if active_order.Get(OrderField.LimitPrice) != limit_price:
                                    new_quantity:int = self.Portfolio.TotalPortfolioValue // limit_price
                                    active_order.UpdateLimitPrice(limit_price)
                                    active_order.UpdateQuantity(new_quantity)
                            else:
                                # submit new limit order
                                if len([x for x in self.Portfolio if x.Value.Invested])  1:
                                        self.LimitOrder(etf, quantity, limit_price, tag='LIMIT_BUY')

                if self.trade_short:
                    # find not yet crossed top
                    last_top_datetime = etf_hist[~etf_hist['Double_Top'].isnull()]
                    if not last_top_datetime.empty:
                        last_top_datetime = last_top_datetime.index[-1]
                        if all(x[1][etf]  1:
                                        self.LimitOrder(etf, -quantity, limit_price, tag='LIMIT_SELL')

def cancel_all_limit_orders(self) -> None:
    # cancel all submitted limit orders for the symbol
    active_limit_orders:List = list(self.Transactions.GetOrderTickets(lambda ticket: ('LIMIT_SELL' in ticket.Tag or 'LIMIT_BUY' in ticket.Tag) and ticket.Status not in [OrderStatus.Filled, OrderStatus.Invalid, OrderStatus.Canceled]))
    for ticket in active_limit_orders:
        response = ticket.Cancel()

def cancel_all_orders(self, symbol:Symbol) -> None:
    # cancel all submitted orders for the symbol
    active_limit_orders:List = list(self.Transactions.GetOrderTickets(lambda ticket: ticket.Symbol == symbol))
    for ticket in active_limit_orders:
        response = ticket.Cancel()

def OnOrderEvent(self, orderEvent: OrderEvent) -> None:
    order = self.Transactions.GetOrderById(orderEvent.OrderId)
    if orderEvent.Status == OrderStatus.Filled:
        order_ticket = self.Transactions.GetOrderTicket(orderEvent.OrderId)
        
        # if TP or SL was hit
        if '_TP' in order_ticket.Tag or '_SL' in order_ticket.Tag:
            # cancel all submitted orders for the symbol
            self.cancel_all_orders(order_ticket.Symbol)

        # set TP and SL if limit was hit
        if orderEvent.Quantity > 0:
            if 'LIMIT_BUY' in order_ticket.Tag:
                if len([x for x in self.Portfolio if x.Value.Invested]) == self.max_positions_opened:
                    self.cancel_all_limit_orders()

                tp_price:float = round(orderEvent.FillPrice + (orderEvent.FillPrice * self.take_profit_pct), 2)
                stop_price:float = round(orderEvent.FillPrice - (orderEvent.FillPrice * self.stop_loss_pct), 2)

                self.LimitOrder(orderEvent.Symbol, -orderEvent.Quantity, tp_price, tag='BUY_TP')
                self.StopMarketOrder(orderEvent.Symbol, -orderEvent.Quantity, stop_price, tag='BUY_SL')
        
        if orderEvent.Quantity  DataFrame:
    for level_str, obj_function in [('Support', 'min'), ('Resistance', 'max')]:
        level_prices = stock_data[symbol]
        # TODO eval min and max
        if obj_function == 'min':
            pivot_level = level_prices.rolling(window=rolling_period*2+1, center=True).min().shift(-rolling_period)
        else:
            pivot_level = level_prices.rolling(window=rolling_period*2+1, center=True).max().shift(-rolling_period)
        stock_data[level_str] = None

        level_points = pivot_level.where(pivot_level == level_prices, None).dropna().index
        valid_indices = []

        for i, level_point in enumerate(level_points):
            if i == 0:
                valid_indices.append(level_point)
            else:
                timedelta = level_point - level_points[i - 1]
                if timedelta.days > lookback_period:
                    valid_indices.append(level_point)

        stock_data.loc[valid_indices, level_str] = pivot_level.loc[valid_indices]

    return stock_data

def find_double_tops_and_bottoms(self, symbol:str, stock_data:DataFrame, min_distance:int, max_distance:int, max_percentage:float) -> DataFrame:
    stock_data['Double_Top'] = None
    stock_data['Double_Bottom'] = None

    support_points = stock_data.dropna(subset=['Support']).index
    resistance_points = stock_data.dropna(subset=['Resistance']).index

    for i in range(len(resistance_points)):
        for j in range(i + 1, len(resistance_points)):
            timedelta = resistance_points[j] - resistance_points[i]
            if timedelta.days  max_distance:
                continue
            price_pct_difference = abs(stock_data.loc[resistance_points[j], 'Resistance'] / stock_data.loc[resistance_points[i], 'Resistance'] - 1)
            if price_pct_difference  max_distance:
                continue
            price_pct_difference = abs(stock_data.loc[support_points[j], 'Support'] / stock_data.loc[support_points[i], 'Support'] - 1)
            if price_pct_difference  stock_data.loc[support_points[i], 'Support'] else support_points[i]
                if all(stock_data.loc[support_points[x], symbol] >= stock_data.loc[higher_bottom_index, 'Support'] for x in range(i+1,j)):
                    stock_data.loc[higher_bottom_index, 'Double_Bottom'] = stock_data.loc[higher_bottom_index, 'Support']

    return stock_data
