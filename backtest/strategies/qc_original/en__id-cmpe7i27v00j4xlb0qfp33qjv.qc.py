# Original QuantConnect / library Python
# locale=en slug="显著性理论与加密货币回报策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
class SalienceTheoryandCryptocurrencyReturns(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    
    self.cryptos: Dict[str, str] = {
        "XLMUSD": "XLM",    # Stellar
        "XMRUSD": "XMR",    # Monero
        "XRPUSD": "XRP",    # XRP
        "ADAUSD": "ADA",    # Cardano
        "DOTUSD": "DOT",    # Polkadot
        "UNIUSD": "UNI",    # Uniswap
        "LINKUSD": "LINK",  # Chainlink
        "ANTUSD": "ANT",    # Aragon
        "BATUSD": "BAT",    # Basic Attention Token
        "BTCUSD": "BTC",    # Bitcoin
        "BTGUSD": "BTG",    # Bitcoin Gold
        "DAIUSD": "DAI",    # Dai
        "DASHUSD": "DASH",  # Dash
        "DGBUSD": "DGB",    # Dogecoin
        "ETCUSD": "ETC",    # Ethereum Classic
        "ETHUSD": "ETH",    # Ethereum
        "FUNUSD": "FUN",    # FUN Token
        "LTCUSD": "LTC",    # Litecoin
        "MKRUSD": "MKR",    # Maker
        "NEOUSD": "NEO",    # Neo
        "PAXUSD": "PAX",    # Paxful
        "SNTUSD": "SNT",    # Status
        "TRXUSD": "TRX",    # Tron
        "XRPUSD": "XRP",    # XRP
        "XTZUSD": "XTZ",    # Tezos
        "XVGUSD": "XVG",    # Verge
        "ZECUSD": "ZEC",    # Zcash
        "ZRXUSD": "ZRX"     # Ox
    }
    
    self.symbol_data: Dict[str, data_tools.SymbolData] = {}
    
    self.ranking_period: int = 21
    self.momentum_period: int = self.ranking_period * 2        # need n of daily prices
    self.quantile: int = 5
    self.portfolio_percentage: float = .2
    self.leverage: int = 3
    self.delta: float = .7
    self.theta: float = .1
    self.SetBrokerageModel(BrokerageName.Bitfinex)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    
    for ticker, crypto in self.cryptos.items():
        data: Crypto = self.AddCrypto(ticker, Resolution.Daily, Market.Bitfinex)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        
        network_symbol: Symbol = self.AddData(data_tools.CryptoNetworkData, crypto, Resolution.Daily).Symbol
        self.symbol_data[ticker] = data_tools.SymbolData(network_symbol, self.momentum_period)
  
    self.recent_month: int = -1
    
def OnData(self, data: Slice) -> None:
    crypto_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.CryptoNetworkData.get_last_update_date()
    
    # daily updating of crypto prices and market capitalization(CapMrktCurUSD)
    for crypto, symbol_obj in self.symbol_data.items():
        network_symbol: Symbol = symbol_obj._network_symbol
        
        if crypto in data.Bars and data[crypto]:
            # get crypto price
            price: float = data.Bars[crypto].Value
            self.symbol_data[crypto].update(price)
        
        if network_symbol in data and data[network_symbol]:
            # get market capitalization
            cap_mrkt_cur_usd: float = data[network_symbol].Value
            self.symbol_data[crypto].update_cap(cap_mrkt_cur_usd)
    # monthly rebalance
    if self.recent_month == self.Time.month:
        return
    prepared_symbols: List[Tuple[str, data_tools.CryptoNetworkData]] = [(crypto, symbol_obj) for crypto, symbol_obj in self.symbol_data.items() if symbol_obj.is_ready() and \
                                                                 self.Securities[symbol_obj._network_symbol].GetLastData() and self.Time.date() = self.quantile:
        # sort the portfolio into quintiles, long the lowest quintile, short the highest
        sorted_by_ST: List[Tuple[str, float]] = sorted(ST.items(), key=lambda x:x[1], reverse=True)
        quantile: int = int(len(sorted_by_ST) / self.quantile)
        long = [x[0] for x in sorted_by_ST[-quantile:]]
        short = [x[0] for x in sorted_by_ST[:quantile]]
    
    # value weighting
    weight: Dict[str, float] = {}
    for i, portfolio in enumerate([long, short]):
        mc_sum:float = sum(list(map(lambda x: x[1]._cap_mrkt_cur_usd, portfolio)))
        for ticker, symbol_obj in portfolio:
            weight[ticker] = ((-1)**i) * symbol_obj._cap_mrkt_cur_usd / mc_sum
    
    # trade execution    
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, self.portfolio_percentage * w) for symbol, w in weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
