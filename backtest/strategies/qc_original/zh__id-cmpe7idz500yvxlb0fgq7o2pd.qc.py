# Original QuantConnect / library Python
# locale=zh slug="双重上市股票套利策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List
from data_tools import SymbolData, OpenTrade, CustomFeeModel
# endregion
class CalculatingYellowHippopotamus(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.leverage:int = 5
    self.threshold:float = 0.01
    self.period:int = 2
    self.data:Dict[Symbol, SymbolData] = {}
    self.open_trades:Dict[str, OpenTrade] = {}
    stocks_with_both_share_classes:List[str] = [
        'BRK','AKO','BF','CRB','FCE','JW','MOG','RDS','LGF',
    ]
    self.stock_pairs:Dict[str, str] = { x + '.A' : x + '.B' for x in stocks_with_both_share_classes }
    tickers:List[str] = list(self.stock_pairs.keys()) + list(self.stock_pairs.values())
    for ticker in tickers:
        security = self.AddEquity(ticker, Resolution.Daily)
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        self.data[ticker] = SymbolData(security.Symbol, self.period)
    self.UniverseSettings.Resolution = Resolution.Minute
def OnData(self, data: Slice):
    # update prices on minute basis
    for _, symbol_data in self.data.items():
        symbol:Symbol = symbol_data.get_symbol()
        if symbol in data and data[symbol]:
            price:float = data[symbol].Value
            # start updating prices, only when base price is set
            if not symbol_data.base_price_ready():
                symbol_data.set_base_price(price)
                continue
            symbol_data.update_prices(price)
    long_leg:List[Symbol] = []
    short_leg:List[Symbol] = []
    closed_trades_flag:bool = False
    for ticker1, ticker2 in self.stock_pairs.items():
        ticker1_return:float|None = None
        ticker2_return:float|None = None
        if self.data[ticker1].prices_ready():
            ticker1_return = self.data[ticker1].get_return()
            self.data[ticker1].reset_prices()
        if self.data[ticker2].prices_ready():
            ticker2_return = self.data[ticker2].get_return()
            self.data[ticker2].reset_prices()
        # make sure both stocks from pair has returns
        if not (ticker1_return and ticker2_return):
            continue
        identificator:str = ticker1 + ticker2
        # if stocks are invested, check if they should be sell
        if identificator in self.open_trades:
            open_trade:OpenTrade = self.open_trades[identificator]
            prev_diff:float = open_trade.get_prev_diff()
            if (prev_diff >= self.threshold and ticker1_return = ticker2_return):
                # liquidate, becasue stock, which had previously larger return, has now smaller or equal return
                traded_symbols:List[Symobl] = open_trade.get_traded_symbols()
                for symbol in traded_symbols:
                    self.Liquidate(symbol)
                # remove OpenTrade object, because it's stocks were liquidated
                del self.open_trades[identificator]
                closed_trades_flag = True
            continue
        diff:float = ticker1_return - ticker2_return
        # trade stocks, when differecne between their percentual return
        # in absolute value is greater than threshold
        if abs(diff) >= self.threshold:
            symbol1:Symbol = self.data[ticker1].get_symbol()
            symbol2:Symobl = self.data[ticker2].get_symbol()
            if ticker1_return > ticker2_return:
                long_leg.append(symbol2)
                short_leg.append(symbol1)
                self.open_trades[identificator] = OpenTrade(diff, symbol2, symbol1)
            else:
                long_leg.append(symbol1)
                short_leg.append(symbol2)
                self.open_trades[identificator] = OpenTrade(diff, symbol1, symbol2)
    if len(long_leg) != 0 or closed_trades_flag:
        # trade execution
        # trade execution
        long_leg = long_leg + [open_trade.get_long_symbol() for _, open_trade in self.open_trades.items()]
        short_leg = short_leg + [open_trade.get_short_symbol() for _, open_trade in self.open_trades.items()]
        length:int = len(long_leg)
        for symbol in long_leg:
            self.SetHoldings(symbol, 1 / length)
        for symbol in short_leg:
            self.SetHoldings(symbol, -1 / length)
