# Original QuantConnect / library Python
# locale=en slug="加密货币中的基于价格的价值"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import List, Dict
#endregion

class PricebasedValueinCryptocurrencies(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)

    self.period: int = 52 * 7 
    self.quantiles: int = 5
    self.percentage_traded: int = .2
    self.leverage: int = 10
    
    self.cryptos: Dict[str, str] = {
        "ANTUSD": "ANT", # Aragon
        "BATUSD": "BAT", # Basic Attention Token
        "BTCUSD": "BTC", # Bitcoin
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
    self.SetBrokerageModel(BrokerageName.Bitfinex)
    
    for crypto, ticker in self.cryptos.items():
        data: Securities = self.AddCrypto(crypto, Resolution.Daily, Market.Bitfinex)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        
        network_symbol: Symbol = self.AddData(data_tools.CryptoNetworkData, ticker, Resolution.Daily).Symbol
        self.data[crypto] = data_tools.SymbolData(network_symbol, self.period)
    
    self.rebalance_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.WeekStart('BTCUSD'), self.TimeRules.At(0,0), self.Rebalance)
    
def OnData(self, data: Slice) -> None:
    crypto_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.CryptoNetworkData.get_last_update_date()
    
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
            self.data[crypto].update_cap(cap_mrkt_cur_usd)

    if not self.rebalance_flag:
        return
    performance: Dict[str, float] = {}
    
    for crypto, symbol_obj in self.data.items():
        if crypto in data and data[crypto]:
            # crypto doesn't have enough data
            if self.Securities[symbol_obj.network_symbol].GetLastData() and self.Time.date() > crypto_data_last_update_date[symbol_obj.network_symbol]:
                self.Liquidate()
                continue

            if not symbol_obj.is_ready():
                continue
        
            # calculate performance for current crypto
            performance[crypto] = symbol_obj.performance()
    
    # not enough cryptos for selection    
    if len(performance)  None:
    self.rebalance_flag = True
