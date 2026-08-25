# Original QuantConnect / library Python
# locale=en slug="trading-volume-in-cryptocurrency-markets-and-reversals"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class TradingVolumeInCryptocurrencyMarketsAndReversals(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    
    self.cryptos = [
        "BTCUSD", # Bitcoin
        "ETHUSD", # Ethereum
        "XRPUSD", # XRP
        # "BCHUSD", # Bitcoin cash
        "LTCUSD", # Litecoin
        "BSVUSD", # Bitcoin SV
        "EOSUSD", # EOS
        "XMRUSD", # Monero
        "TRXUSD", # Tron
        "XTZUSD", # Tezos
        "XLMUSD", # Stellar
        "NEOUSD", # Neo
        "DAIUSD", # Dai
        "ZECUSD", # Zcash
        "VETUSD", # VeChain
        "ETCUSD", # Ethereum Classic
        "MKRUSD", # Maker
        "OMGUSD", # OMG Network
        # "DGBUSD", # Dogecoin
        # "BATUSD", # Basic Attention Token
        # "ZRXUSD", # Ox
    ]
    
    self.data = {}
    self.period = 61
    self.traded_percentage = 0.1
    self.quantile = 3
    
    self.SetBrokerageModel(BrokerageName.Bitfinex)
    
    for crypto in self.cryptos:
        # GDAX is coinmarket, but it doesn't support this many cryptos, so we choose Bitfinex
        data = self.AddCrypto(crypto, Resolution.Minute, Market.Bitfinex)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(10)
        
        self.data[crypto] = SymbolData(crypto, self.period)
    
    self.last_day = -1
    
def OnData(self, data):
    performance = {}
    volume_shock = {}
    
    if self.last_day == self.Time.day: return
    self.last_day = self.Time.day

    for crypto in self.cryptos:
        if crypto in data.Bars and data[crypto]:
            # Volume can be taken only from TradeBar and data[crypto] returns QuoteBar by default
            price = data.Bars[crypto].Value
            volume = data.Bars[crypto].Volume
            self.data[crypto].update(price, volume)
            
            if self.data[crypto].is_ready():
                result_volume_shock = self.data[crypto].volume_shock()
                if result_volume_shock:
                    performance[crypto] = self.data[crypto].performance()
                    volume_shock[crypto] = result_volume_shock
    if len(performance)
