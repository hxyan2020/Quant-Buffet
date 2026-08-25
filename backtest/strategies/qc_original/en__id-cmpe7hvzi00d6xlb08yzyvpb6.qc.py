# Original QuantConnect / library Python
# locale=en slug="大市值加密货币中的横截面动量"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict

class CrosssectionalMomentumInLargeCryptos(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(1_000_000)

    self.period: int = 14 # need n of daily prices
    self.quantile: int = 3
    self.portfolio_percentage: float = .1
    self.leverage: int = 10
    
    self.cryptos: Dict[str, str] = {
        "ANTUSD": "ANT", # Aragon
        "BATUSD": "BAT", # Basic Attention Token
        "BTCUSD": "BTC", # Bitcoin
        "BTGUSD": "BTG", # Bitcoin Gold
        "DAIUSD": "DAI", # Dai
        "DGBUSD": "DGB", # Dogecoin
        "EOSUSD": "EOS", # EOS
        "ETCUSD": "ETC", # Ethereum Classic
        "ETHUSD": "ETH", # Ethereum
        "FUNUSD": "FUN", # FUN Token
        "LTCUSD": "LTC", # Litecoin
        "MKRUSD": "MKR", # Maker
        "NEOUSD": "NEO", # Neo
        "OMGUSD": "OMG", # OMG Network
        "SNTUSD": "SNT", # Status
        "TRXUSD": "TRX", # Tron
        "XLMUSD": "XLM", # Stellar
        "XMRUSD": "XMR", # Monero
        "XRPUSD": "XRP", # XRP
        "XTZUSD": "XTZ", # Tezos
        "XVGUSD": "XVG", # Verge
        "ZECUSD": "ZEC", # Zcash
        "ZRXUSD": "ZRX"  # Ox
    }
    
    self.data: Dict[str, data_tools.SymbolData] = {}
    self.weight: Dict[str, float] = {}
    
    self.SetBrokerageModel(BrokerageName.Bitfinex)
    
    for crypto, ticker in self.cryptos.items():
        # GDAX is coinmarket, but it doesn't support this many cryptos, so we choose Bitfinex
        data: Securities = self.AddCrypto(crypto, Resolution.Daily, Market.Bitfinex)
        data.SetLeverage(self.leverage)
        
        network_symbol: Symbol = self.AddData(data_tools.CryptoNetworkData, ticker, Resolution.Daily).Symbol
        self.data[crypto] = data_tools.SymbolData(network_symbol, self.period)
    
    self.rebalance_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.WeekStart("BTCUSD"), self.TimeRules.At(0,0), self.Rebalance)
    
def OnData(self, data: Slice) -> None:
    # daily updating of crypto prices and market capitalization(CapMrktCurUSD)
    for crypto, symbol_obj in self.data.items():
        network_symbol: Symbol = symbol_obj.network_symbol
        
        if crypto in data.Bars and data[crypto]:
            # get crypto price
            price: float = data.Bars[crypto].Value
            self.data[crypto].update(price)
        
        if network_symbol in data and data[network_symbol]:
            # get market capitalization
            cap_mrkt_cur_usd: float = data[network_symbol].Value
            if cap_mrkt_cur_usd != 0:
                self.data[crypto].update_cap(cap_mrkt_cur_usd)

    if not self.rebalance_flag:
        return

    # trade execution
    invested: List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for ticker in invested:
        if ticker not in self.weight:
            self.Liquidate(ticker)

    for ticker, w in self.weight.items():
        self.SetHoldings(ticker, w)

    self.rebalance_flag = False
    self.weight.clear()
    
def Rebalance(self) -> None:
    self.rebalance_flag = True

    crypto_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.CryptoNetworkData.get_last_update_date()
    
    performance: Dict[str, float] = {}
    
    for crypto, symbol_obj in self.data.items():
        network_symbol: Symbol = symbol_obj.network_symbol
        if network_symbol not in crypto_data_last_update_date:
            continue

        # crypto doesn't have enough data
        if self.Securities[network_symbol].GetLastData() and self.Time.date() > crypto_data_last_update_date[network_symbol]:
            self.Liquidate()
            return

        if symbol_obj.is_ready():
            # calculate performance for current crypto
            performance[crypto] = symbol_obj.performance()
    
    # not enough cryptos for selection    
    if len(performance)
