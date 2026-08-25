# Original QuantConnect / library Python
# locale=en slug="中国市场中的财报公告后漂移效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List
from data_tools import ChineseStocks, ChineseIncomeStatement, QuantpediaCSI500, SymbolData, \
CustomFeeModel, WaitingStock, ActiveStock
# endregion

class PostEarningsAnnouncementDriftInChina(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)   # Chinese data starts in 2015
    self.SetCash(100000)

    self.short_flag:bool = True

    self.leverage:int = 5

    self.threshold:float = 0.03

    self.wait_period:int = 3
    self.holding_period:int = 60

    self.active_universe:Dict[Symbol, ActiveStock] = {}     # symbols of stocks, which are actively traded
    self.waiting_universe:Dict[Symbol, WaitingStock] = {}   # symbols of stocks, which overnight perf was greater than 3%
    self.potential_trades:Dict[Symbol, datetime.date] = {}  # symbols of stocks with value of their annoucement date(income statement date)

    self.data:dict[Symbol, SymbolData] = {}

    self.top_size_symbol_count:int = 300
    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/chinese_stocks/large_cap_500.csv')
    tickers:List[str] = ticker_file_str.split('\r\n')[:self.top_size_symbol_count]

    for t in tickers:
        data = self.AddData(ChineseStocks, t, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage)

        stock_symbol:Symbol = data.Symbol
        data = self.AddData(ChineseIncomeStatement, t, Resolution.Daily)

        self.data[stock_symbol] = SymbolData(data.Symbol)

    if self.short_flag:
        data = self.AddData(QuantpediaCSI500, 'CSI_500', Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage)

        self.benchmark = data.Symbol

def OnData(self, data: Slice):
    curr_date:datetime.date = self.Time.date()

    # store daily data
    for symbol, symbol_data in self.data.items():
        income_statement_symbol:Symbol = symbol_data.get_income_statement_symbol()

        if data.ContainsKey(symbol):
            price_data:dict[str, str] = data[symbol].GetProperty('price_data')
            # valid price data
            if data[symbol].Value != 0. and price_data:
                close_price:float = data[symbol].Value
                open_price:float = price_data['openPrice']
                symbol_data.update_prices(curr_date, close_price, open_price)

                mc:float = float(price_data['marketValue'])
                symbol_data.update_market_cap(mc)

        # check if stock has income statement day(announcement day)
        if data.ContainsKey(income_statement_symbol):
            self.potential_trades[symbol] = curr_date

    potential_trades_to_remove:List[Symbol] = []
    for symbol, announcement_day in self.potential_trades.items():
        # make sure overnight perf is calculated day after annoucement day
        if curr_date == announcement_day:
            continue
        
        symbol_data:SymbolData = self.data[symbol]
        # make sure prices for overnight perf calculations are ready
        if symbol_data.prices_ready():
            prev_close_price:float = symbol_data.get_prev_close_price()
            open_price:float = symbol_data.get_open_price()
            perf:float = (open_price - prev_close_price) / prev_close_price # overnight perf
            
            if perf >= self.threshold:
                # add stock's symbol to universe of stocks, which will be traded after self.wait_period days since curr_date
                self.waiting_universe[symbol] = WaitingStock(curr_date, symbol, self.wait_period)

        # stock's symbols has to be removed from universe of potential trades each time
        potential_trades_to_remove.append(symbol)

    for symbol in potential_trades_to_remove:
        del self.potential_trades[symbol]

    trade_flag:bool = False
    waiting_stocks_to_remove:List[Symbol] = []

    for symbol, waiting_stock_obj in self.waiting_universe.items():
        # stocks in waiting universe have to wait self.waiting_period before they will be trade
        # this condition makes sure these days will be fulfilled
        if curr_date != waiting_stock_obj.get_date():
            waiting_stock_obj.decrease_waiting_period(curr_date)

        if waiting_stock_obj.waiting_period_expired():
            # when self.waiting_period days pass, stock's symbol will be traded
            # and added to universe of actively trading stocks
            trade_flag = True
            waiting_stocks_to_remove.append(symbol)
            self.active_universe[symbol] = ActiveStock(curr_date, symbol, self.holding_period)

    for symbol in waiting_stocks_to_remove:
        del self.waiting_universe[symbol]

    new_active_universe:Dict[Symbol, ActiveStock] = {}
    for symbol, active_stock_obj in self.active_universe.items():
        # stocks in active universe are hold for self.holding_period days
        # this condition makes sure these holding days will be fulfilled
        if curr_date != active_stock_obj.get_date():
            active_stock_obj.decrease_holding_period(curr_date)

        if active_stock_obj.holding_period_expired():
            # liquidate stock, when it was holded for self.holding_period days
            self.Liquidate(symbol)
            # change trade_flag to True, because liquidated stock was removed from active universe
            trade_flag = True
        else:
            new_active_universe[symbol] = active_stock_obj

    self.active_universe = new_active_universe
    # trade only, when there has been change in active universe
    # when trade_flag is true, the signal for trade is met
    if trade_flag:
        total_cap:float = sum(list(map(lambda symbol: self.data[symbol].get_market_cap(), self.active_universe)))
        for symbol in self.active_universe:
            self.SetHoldings(symbol, self.data[symbol].get_market_cap() / total_cap)

        if self.short_flag:
            if not self.Securities[self.benchmark].Invested and len(self.active_universe) != 0:
                self.SetHoldings(self.benchmark, -1)
            elif self.Securities[self.benchmark].Invested:
                self.Liquidate(self.benchmark)
