# Original QuantConnect / library Python
# locale=en slug="24-hour-reversal-in-cryptocurrencies"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import CustomFeeModel, SymbolData
# endregion

class HourReversalInCryptocurrencies(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2016, 1, 1)
    self.SetCash(100000)
    
    self.cryptos:list[str] = [
        #"ANTUSD", # Aragon
        #"BATUSD", # Basic Attention Token
        "BTCUSD", # Bitcoin
        #"DAIUSD", # Dai
        #"DGBUSD", # Dogecoin
        #"EOSUSD", # EOS
        #"ETCUSD", # Ethereum Classic
        "ETHUSD", # Ethereum
        #"FUNUSD", # FUN Token
        "LTCUSD", # Litecoin
        #"MKRUSD", # Maker
        #"NEOUSD", # Neo
        #"OMGUSD", # OMG Network
        #"SNTUSD", # Status
        #"TRXUSD", # Tron
        #"XLMUSD", # Stellar
        #"XMRUSD", # Monero
        "XRPUSD", # XRP
        #"XTZUSD", # Tezos
        #"XVGUSD", # Verge
        #"ZECUSD", # Zcash
        #"ZRXUSD"  # Ox
    ]
    
    self.data:dict[Symbol, SymbolData] = {}
    
    self.lag_period:int = 24 + 1
    self.max_missing_hours:int = 0

    self.leg_count:int = 2

    self.leverage:int = 5
    self.portfolio_percentage:float = 0.1
    
    self.SetBrokerageModel(BrokerageName.Bitfinex)
    
    for crypto in self.cryptos:
        # GDAX is coinmarket, but it doesn't support this many cryptos, so we choose Bitfinex
        data = self.AddCrypto(crypto, Resolution.Hour, Market.Bitfinex)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage)
        
        self.data[data.Symbol] = SymbolData(self.lag_period)
    
def OnData(self, data):
    curr_time:datetime = self.Time

    performance:dict[Symbol, float] = {}
    
    for symbol, symbol_data in self.data.items():
        if symbol in data and data[symbol]:
            price:float = data.Bars[symbol].Value

            if not symbol_data.data_still_coming(curr_time, self.max_missing_hours):
                symbol_data.reset_data()

            if symbol_data.prev_price_ready():
                symbol_data.calculate_perf(price)

                if symbol_data.performances_ready():
                    performance[symbol] = symbol_data.get_first_perf()

            symbol_data.update_price(curr_time, price)

    if len(performance)  self.Securities[symbol].SymbolProperties.MinimumOrderSize:
            self.MarketOrder(symbol, q)

    for symbol in short_leg:
        q:float = self.CalculateOrderQuantity(symbol, (1 / self.leg_count) * self.portfolio_percentage)
        if q > self.Securities[symbol].SymbolProperties.MinimumOrderSize:
            self.MarketOrder(symbol, -q)
