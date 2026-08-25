# Original QuantConnect / library Python
# locale=en slug="traditional-carry-in-cryptocurrencies"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import List, Dict
# endregion

class TraditionalCarryinCryptocurrencies(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1) 
    self.SetCash(100000)
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.crypto_tickers:List[str] = ['BTCUSD', 'ETHUSD', 'SOLUSD', 'ADAUSD', 'XRPUSD', 'DOTUSD', 'DOGEUSD', 'LUNAUSD', 'AVAXUSD', 'UNIUSD',
                                    'LINKUSD', 'LTCUSD', 'BCHABCUSD', 'BSVUSD', 'FILUSD', 'XLMUSD', 'XTZUSD', 'NEOUSD', 'ATOMUSD', 'IOTAUSD', 
                                    'ETCUSD', 'DASHUSD', 'EGLDUSD', 'AAVEUSD', 'ENJUSD', 'EOSUSD', 'MKRUSD', 'MANAUSD', 'SNXUSD', 'FTTUSD', 
                                    'OMGUSD', 'SUSHIUSD', 'YFIUSD', 'WBTCUSD', 'XMRUSD', 'ZECUSD', 'ZRXUSD', 'XRAUSD', 'AMPLUSD', 'GRTUSD', 
                                    'DGBUSD', '1INCHUSD']

    self.crypto_int_symbols: Dict[str, str] = {x : x + '_FRR' for x in self.crypto_tickers}                       

    self.IR_symbol_by_price_symbol:Dict[Symbol, Symbol] = {}
    self.rebalance_flag:bool = False
    self.quantile:int = 3
    self.leverage:int = 2
    self.period:int = 365
    self.percentage_traded:float = .2

    # data subscription
    for ticker, ticker_interest in self.crypto_int_symbols.items():
        data = self.AddCrypto(ticker, Resolution.Daily, Market.Bitfinex, )
        data.SetLeverage(self.leverage)
        crypto_symbol:Symbol = data.Symbol

        interest_symbol = self.AddData(data_tools.CryptoInterestRate, ticker_interest, Resolution.Daily).Symbol
        self.IR_symbol_by_price_symbol[crypto_symbol] = interest_symbol

    self.Schedule.On(self.DateRules.WeekEnd(self.market), self.TimeRules.BeforeMarketClose(self.market), self.Selection)

def OnData(self, data: Slice):
    # weekly rebalance
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False

    rates_last_update_date:Dict[Symbol, datetime.date] = data_tools.CryptoInterestRate.get_last_update_date()
    rates:Dict[Symbol, float] = {}

    for symbol, symbol_interest in self.IR_symbol_by_price_symbol.items(): 
        # both crypto price data and IR data is still comming in
        if symbol in data and data[symbol]:
            if self.Securities[symbol_interest].GetLastData() and symbol_interest in rates_last_update_date and self.Time.date() = self.quantile:
        sorted_rates:List[Symbols] = sorted(rates, key=rates.get)
        quantile:int = len(sorted_rates) // self.quantile
        long:List[str] = sorted_rates[-quantile:]
        short:List[str] = sorted_rates[:quantile]

        # trade execution
        invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
        for price_symbol in invested:
            if price_symbol not in long + short:
                self.Liquidate(price_symbol)

        for symbol in long:
            self.SetHoldings(symbol, self.percentage_traded / len(long))

        for symbol in short:
            self.SetHoldings(symbol, -self.percentage_traded / len(short))

def Selection(self):
    self.rebalance_flag = True
