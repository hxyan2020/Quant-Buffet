# Original QuantConnect / library Python
# locale=en slug="mean-absolute-daily-return-in-cryptos"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from typing import List, Dict
class MeanAbsoluteDailyReturnInCryptos(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(1_000_000)
    
    self.period: int = 5 # need n of daily prices
    self.percentage_traded: float = 0.1
    self.quantile: int = 5
    self.leverage: int = 5
    self.cryptos: Dict[str, str] = {
        "ANTUSD": "ANT", # Aragon
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
        "TRXUSD": "TRX", # Tron
        "XLMUSD": "XLM", # Stellar
        "XMRUSD": "XMR", # Monero
        "XRPUSD": "XRP", # XRP
        "XTZUSD": "XTZ", # Tezos
        "XVGUSD": "XVG", # Verge
        "ZECUSD": "ZEC", # Zcash
        "ZRXUSD": "ZRX"  # Ox
    }
    
    self.data: Dict[str, SymbolData] = {}
    
    self.SetBrokerageModel(BrokerageName.Bitfinex)
    
    for crypto, ticker in self.cryptos.items():
        # GDAX is coinmarket, but it doesn't support this many cryptos, so we choose Bitfinex
        data: Securities = self.AddCrypto(crypto, Resolution.Daily, Market.Bitfinex)
        data.SetLeverage(self.leverage)
        
        network_symbol: Symbol = self.AddData(CryptoNetworkData, ticker, Resolution.Daily).Symbol
        
        self.data[crypto] = SymbolData(network_symbol, self.period)
    
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    
def OnData(self, data: Slice) -> None:
    crypto_data_last_update_date: Dict[Symbol, datetime.date] = CryptoNetworkData.get_last_update_date()
    # daily updating of crypto prices their volumes and market capitalization(CapMrktCurUSD)
    for crypto, symbol_obj in self.data.items():
        network_symbol = symbol_obj.network_symbol
        
        if network_symbol in data and data[network_symbol]:
            # get market capitalization
            cap_mrkt_cur_usd: float = data[network_symbol].Value
            self.data[crypto].update_cap(cap_mrkt_cur_usd)
        if crypto in data.Bars and data[crypto]:
            # get crypto price and crypto volume
            price: float = data.Bars[crypto].Value
            volume: float = data.Bars[crypto].Volume
            self.data[crypto].update(price, volume)
        
    mean_abs: Dict[str, float] = {} # storing "MEANABS" for each crypto currency
    
    for crypto, symbol_obj in self.data.items():
        network_symbol = self.cryptos[crypto]
        if network_symbol not in crypto_data_last_update_date:
            continue
        if self.Securities[network_symbol].GetLastData() and self.Time.date() > crypto_data_last_update_date[network_symbol]:
            continue
        # crypto doesn't have enough data
        if not symbol_obj.is_ready():
            continue
        
        # calculate "MEANABS" for current crypto
        mean_abs[crypto] = symbol_obj.mean_abs()
    
    # rebalance weekly
    if self.Time.date().weekday() != 0:
        return
    # not enough cryptos for quantile selection    
    if len(mean_abs)  None:
    self.network_symbol: str = network_symbol
    self.cap_mrkt_cur_usd: Union[None, float] = None
    self.closes: RollingWindow = RollingWindow[float](period)
    self.volumes: RollingWindow = RollingWindow[float](period)
        
def update(self, close: float, volume: float) -> None:
    self.closes.Add(close)
    self.volumes.Add(volume)
    
def update_cap(self, cap_mrkt_cur_usd: float) -> None:
    self.cap_mrkt_cur_usd: float = cap_mrkt_cur_usd
        
def is_ready(self) -> bool:
    return self.closes.IsReady and self.volumes.IsReady and self.cap_mrkt_cur_usd
    
def mean_abs(self) -> float:
    daily_prices: np.ndarray = np.array([x for x in self.closes])
    daily_volumes: np.ndarray = np.array([x for x in self.volumes])
    
    # calculate mean of absolute daily returns
    daily_returns: float = abs((daily_prices[:-1] - daily_prices[1:]) / daily_prices[1:])
    mean_daily_returns: float = np.mean(daily_returns)
    dollar_volume: float = sum(daily_prices * daily_volumes)
    
    # return "MEANABS"
    return mean_daily_returns / dollar_volume
    
# Crypto network data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
# Data source: https://coinmetrics.io/community-network-data/
class CryptoNetworkData(PythonData):
_last_update_date: Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return CryptoNetworkData._last_update_date
def GetSource(self, config: SubscriptionDataConfig, date: datetime, isLiveMode: bool) -> SubscriptionDataSource:
    self.cap_mrkt_cur_usd_index = None
    return SubscriptionDataSource(f"data.quantpedia.com/backtesting_data/crypto/{config.Symbol.Value}_network_data.csv", SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
# File exmaple:
# date,AdrActCnt,AdrBal1in100KCnt,AdrBal1in100MCnt,AdrBal1in10BCnt,AdrBal1in10KCnt,AdrBal1in10MCnt,AdrBal1in1BCnt,AdrBal1in1KCnt,AdrBal1in1MCnt,AdrBalCnt,AdrBalNtv0.001Cnt,AdrBalNtv0.01Cnt,AdrBalNtv0.1Cnt,AdrBalNtv100Cnt,AdrBalNtv100KCnt,AdrBalNtv10Cnt,AdrBalNtv10KCnt,AdrBalNtv1Cnt,AdrBalNtv1KCnt,AdrBalNtv1MCnt,AdrBalUSD100Cnt,AdrBalUSD100KCnt,AdrBalUSD10Cnt,AdrBalUSD10KCnt,AdrBalUSD10MCnt,AdrBalUSD1Cnt,AdrBalUSD1KCnt,AdrBalUSD1MCnt,AssetEODCompletionTime,BlkCnt,BlkSizeMeanByte,BlkWghtMean,BlkWghtTot,CapAct1yrUSD,CapMVRVCur,CapMVRVFF,CapMrktCurUSD,CapMrktFFUSD,CapRealUSD,DiffLast,DiffMean,FeeByteMeanNtv,FeeMeanNtv,FeeMeanUSD,FeeMedNtv,FeeMedUSD,FeeTotNtv,FeeTotUSD,FlowInExNtv,FlowInExUSD,FlowOutExNtv,FlowOutExUSD,FlowTfrFromExCnt,HashRate,HashRate30d,IssContNtv,IssContPctAnn,IssContPctDay,IssContUSD,IssTotNtv,IssTotUSD,NDF,NVTAdj,NVTAdj90,NVTAdjFF,NVTAdjFF90,PriceBTC,PriceUSD,ROI1yr,ROI30d,RevAllTimeUSD,RevHashNtv,RevHashRateNtv,RevHashRateUSD,RevHashUSD,RevNtv,RevUSD,SER,SplyAct10yr,SplyAct180d,SplyAct1d,SplyAct1yr,SplyAct2yr,SplyAct30d,SplyAct3yr,SplyAct4yr,SplyAct5yr,SplyAct7d,SplyAct90d,SplyActEver,SplyActPct1yr,SplyAdrBal1in100K,SplyAdrBal1in100M,SplyAdrBal1in10B,SplyAdrBal1in10K,SplyAdrBal1in10M,SplyAdrBal1in1B,SplyAdrBal1in1K,SplyAdrBal1in1M,SplyAdrBalNtv0.001,SplyAdrBalNtv0.01,SplyAdrBalNtv0.1,SplyAdrBalNtv1,SplyAdrBalNtv10,SplyAdrBalNtv100,SplyAdrBalNtv100K,SplyAdrBalNtv10K,SplyAdrBalNtv1K,SplyAdrBalNtv1M,SplyAdrBalUSD1,SplyAdrBalUSD10,SplyAdrBalUSD100,SplyAdrBalUSD100K,SplyAdrBalUSD10K,SplyAdrBalUSD10M,SplyAdrBalUSD1K,SplyAdrBalUSD1M,SplyAdrTop100,SplyAdrTop10Pct,SplyAdrTop1Pct,SplyCur,SplyExpFut10yr,SplyFF,SplyMiner0HopAllNtv,SplyMiner0HopAllUSD,SplyMiner1HopAllNtv,SplyMiner1HopAllUSD,TxCnt,TxCntSec,TxTfrCnt,TxTfrValAdjNtv,TxTfrValAdjUSD,TxTfrValMeanNtv,TxTfrValMeanUSD,TxTfrValMedNtv,TxTfrValMedUSD,VelCur1yr,VtyDayRet180d,VtyDayRet30d
# 2009-01-09,19,19,19,19,19,19,19,19,19,19,19,19,19,0,0,19,0,19,0,0,0,0,0,0,0,0,0,0,1614334886,19,215,860,16340,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,9.44495122962963E-7,0,950,36500,100,0,950,0,1,0,0,0,0,1,0,0,0,0,11641.53218269,1005828380.584716757433,0,0,950,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,950,950,950,950,950,950,950,950,950,950,950,950,950,0,0,0,0,0,0,0,0,0,0,0,0,0,950,50,50,950,17070250,950,1000,0,1000,0,0,0,0,0,0,0,0,0,0,0,0,0
def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:
    data: CryptoNetworkData = CryptoNetworkData()
    data.Symbol = config.Symbol
    try:
        cols: List[str] = ['CapMrktCurUSD']
        if not line[0].isdigit():
            header_split = line.split(',')
            self.col_index = [header_split.index(x) for x in cols]
            return None
        split: str = line.split(',')
        
        data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
        
        for i, col in enumerate(cols):
            data[col] = float(split[self.col_index[i]])
        data.Value = float(split[self.col_index[0]])
        if config.Symbol.Value not in CryptoNetworkData._last_update_date:
            CryptoNetworkData._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
        if data.Time.date() > CryptoNetworkData._last_update_date[config.Symbol.Value]:
            CryptoNetworkData._last_update_date[config.Symbol.Value] = data.Time.date()
    except:
        return None
    return data
