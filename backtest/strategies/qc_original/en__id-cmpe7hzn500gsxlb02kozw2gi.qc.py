# Original QuantConnect / library Python
# locale=en slug="地缘政治风险与加密货币跨类别收益策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import List, Dict
# endregion

class CrawlingYellowBarracuda(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(1000000)
    
    self.period: int = 21 + 1 # need n of daily data
    self.quantile: int = 5
    self.leverage: int = 5
    self.portfolio_percentage: float = .5

    cryptos: Dict[str, str] = {
        "ANTUSD": "ANT", # Aragon
        "BATUSD": "BAT", # Basic Attention Token
        "BTCUSD": "BTC", # Bitcoin
        "BTGUSD": "BTG", # Bitcoin Gold
        "DAIUSD": "DAI", # Dai
        "DGBUSD": "DGB", # Dogecoin
        "EOSUSD": "EOS", # EOS
        "ETCUSD": "ETC", # Ethereum Classic
        "ETHUSD": "ETH", # Ethereum
        "FUNUSD": "FUN", # FUNToken
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
        "ZRXUSD": "ZRX", # Ox
    }

    self.data: Dict[str, data_tools.SymbolData] = {}
    
    self.SetBrokerageModel(BrokerageName.Bitfinex)
    
    for crypto, ticker in cryptos.items():
        # GDAX is coinmarket, but it doesn't support this many cryptos, so we choose Bitfinex
        data: Securities = self.AddCrypto(crypto, Resolution.Daily, Market.Bitfinex)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        
        network_symbol: Symbol = self.AddData(data_tools.CryptoNetworkData, ticker, Resolution.Daily).Symbol
        
        self.data[crypto] = data_tools.SymbolData(network_symbol, self.period)

    self.geo_risk_index: Symbol = self.AddData(data_tools.QuantpediaGeopoliticalRisk, 'GeopoliticalRiskIndex', Resolution.Daily).Symbol
    self.geo_risk_index_values: RollingWindow = RollingWindow[float](self.period)
    self.geo_risk_beta_value_index: int = 1

    self.value_weighted: bool = True
    self.selection_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.WeekStart('BTCUSD'), self.TimeRules.At(9, 30), self.Selection)

def OnData(self, data: Slice) -> None:
    curr_date: datetime.date = self.Time.date()
    crypto_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.CryptoNetworkData.get_last_update_date()
    qp_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.QuantpediaGeopoliticalRisk.get_last_update_date()

    # daily updating of crypto prices and market capitalization(CapMrktCurUSD)
    if self.Securities[self.geo_risk_index].GetLastData() and self.Time.date()  crypto_data_last_update_date[network_symbol]:
            self.Liquidate()
            return

        if not symbol_obj.is_ready():
            continue

        monthly_returns_by_symbol[crypto] = symbol_obj.get_daily_returns()

    if len(monthly_returns_by_symbol)  None:
    self.selection_flag = True
