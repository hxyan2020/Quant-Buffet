# Original QuantConnect / library Python
# locale=en slug="cryptomarket-discounts"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
# endregion
class CryptomarketDiscounts(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    # exchanges
    tickers:list[str] = [
        'ABUCOINS_BTCUSD', 'BITBAY_BTCUSD', 'BITSTAMP_BTCUSD', 'BITTREX_BTCUSD',
        'CEX_BTCUSD', 'COINBASE_BTCUSD', 'EXMO_BTCUSD', 'GEMINI_BTCUSD',
        'HITBTC_BTCUSD', 'ITBIT_BTCUSD', 'KRAKEN_BTCUSD', 'OKCOIN_BTCUSD', 
        'YOBIT_BTCUSD'
    ]
    bitfinex_btc_ticker:str = 'BITFINEX_BTCUSD'
    self.quantile:int = 5
    self.portfolio_percentage:float = .1
    self.exchange_btc_symbols:list[Symbol] = []
    # subscribe symbols
    for ticker in tickers + [bitfinex_btc_ticker]:
        security:Security = self.AddData(data_tools.QuantpediaBTCExchanges, ticker, Resolution.Daily)
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(5)
        if ticker == bitfinex_btc_ticker:
            self.bitfinex_btc_symbol:Symbol = security.Symbol
        else:
            self.exchange_btc_symbols.append(security.Symbol)
def OnData(self, data: Slice):
    premium_by_symbol:dict[Symbol, float] = {}
    # calculate discount (premium)
    if data.ContainsKey(self.bitfinex_btc_symbol):
        bitfinex_btc_price:float = data[self.bitfinex_btc_symbol].Value
        for exch_symbol in self.exchange_btc_symbols:
            if data.ContainsKey(exch_symbol):
                exch_price:float = data[exch_symbol].Value
                
                premium:float = exch_price / bitfinex_btc_price - 1
                premium_by_symbol[exch_symbol] = premium
    
    if len(premium_by_symbol)
