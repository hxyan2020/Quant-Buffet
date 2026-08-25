# Original QuantConnect / library Python
# locale=zh slug="加密货币中的网络规模因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from typing import List, Dict
#endregion
class NetworkSizeFactorinCryptocurrencies(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(1_000_000)
    self.percentage_traded: int = 0.1
    self.period: int = 14
    self.leverage: int = 10
    self.segment: int = 7
    self.crypto_symbols: Dict[str, str] = {
        'BTC' : 'BTCUSD',
        'ETH' : 'ETHUSD', 
        'LTC' : 'LTCUSD',
    }
                    
    # daily network size
    self.network_size: Dict[str, RollingWindow] = {}
    self.growth: Dict[str, float] = {}
    self.SetBrokerageModel(BrokerageName.Bitfinex)
    for crypto, ticker in self.crypto_symbols.items():
        data = self.AddCrypto(ticker, Resolution.Daily, Market.Bitfinex)
        data.SetLeverage(self.leverage)
        
        self.AddData(CryptoNetworkData, crypto, Resolution.Daily)
        
        # crypto data
        self.network_size[crypto] = RollingWindow[float](self.period)
    
    self.selection_flag: bool = False
    self.rebalance_flag: bool = False
    self.recent_month: int = -1
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.SetWarmUp(self.period, Resolution.Daily)
def OnData(self, data: Slice) -> None:
    crypto_data_last_update_date: Dict[Symbol, datetime.date] = CryptoNetworkData.get_last_update_date()
    for crypto, ticker in self.crypto_symbols.items():
        if self.Securities[crypto].GetLastData() and self.Time.date() > crypto_data_last_update_date[crypto]:
            self.liquidate(crypto)
            continue
        if crypto in data and data[crypto]:
            # network data came in
            network_size: float = data[crypto].Price
            
            # store daily data
            if network_size != 0:
                self.network_size[crypto].Add(network_size)
            # rebalance once a month
            if self.recent_month != self.Time.month:
                self.selection_flag = True
                self.recent_month = self.Time.month
            if self.selection_flag:
                if self.network_size[crypto].IsReady:
                    ticker: str = self.crypto_symbols[crypto]
                    week_t1_network_sizes: List[float] = [np.log(x) for x in self.network_size[crypto]][:self.segment]
                    week_t2_network_sizes: List[float] = [np.log(x) for x in self.network_size[crypto]][self.segment:]
                    
                    self.growth[ticker] = np.mean(week_t1_network_sizes) - np.mean(week_t2_network_sizes)
                    self.rebalance_flag = True
    self.selection_flag = False
    
    if self.rebalance_flag:
        total_growth_abs: float = sum(abs(x[1]) for x in self.growth.items())
        weight: Dict[str, float] = {x[0] : x[1] / total_growth_abs for x in self.growth.items()}
        
        # trade execution
        invested: List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
        for symbol in invested:
            if symbol not in weight:
                self.Liquidate(symbol)
        portfolio: List[PortfolioTarget] = [PortfolioTarget(ticker, (self.percentage_traded * w)) for ticker, w in weight.items() if ticker in data and data[ticker] and w > 0]
        if len(portfolio) != 0:
            self.SetHoldings(portfolio)
            self.rebalance_flag = False
# Crypto network data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
# Data source: https://coinmetrics.io/community-network-data/
class CryptoNetworkData(PythonData):
_last_update_date: Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return CryptoNetworkData._last_update_date
def GetSource(self, config: SubscriptionDataConfig, date: datetime, isLiveMode: bool) -> SubscriptionDataSource:
    return SubscriptionDataSource(f"data.quantpedia.com/backtesting_data/crypto/{config.Symbol.Value}_network_data.csv", SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
# File exmaple:
# date,AdrActCnt,AdrBal1in100KCnt,AdrBal1in100MCnt,AdrBal1in10BCnt,AdrBal1in10KCnt,AdrBal1in10MCnt,AdrBal1in1BCnt,AdrBal1in1KCnt,AdrBal1in1MCnt,AdrBalCnt,AdrBalNtv0.001Cnt,AdrBalNtv0.01Cnt,AdrBalNtv0.1Cnt,AdrBalNtv100Cnt,AdrBalNtv100KCnt,AdrBalNtv10Cnt,AdrBalNtv10KCnt,AdrBalNtv1Cnt,AdrBalNtv1KCnt,AdrBalNtv1MCnt,AdrBalUSD100Cnt,AdrBalUSD100KCnt,AdrBalUSD10Cnt,AdrBalUSD10KCnt,AdrBalUSD10MCnt,AdrBalUSD1Cnt,AdrBalUSD1KCnt,AdrBalUSD1MCnt,AssetEODCompletionTime,BlkCnt,BlkSizeMeanByte,BlkWghtMean,BlkWghtTot,CapAct1yrUSD,CapMVRVCur,CapMVRVFF,CapMrktCurUSD,CapMrktFFUSD,CapRealUSD,DiffLast,DiffMean,FeeByteMeanNtv,FeeMeanNtv,FeeMeanUSD,FeeMedNtv,FeeMedUSD,FeeTotNtv,FeeTotUSD,FlowInExNtv,FlowInExUSD,FlowOutExNtv,FlowOutExUSD,FlowTfrFromExCnt,HashRate,HashRate30d,IssContNtv,IssContPctAnn,IssContPctDay,IssContUSD,IssTotNtv,IssTotUSD,NDF,NVTAdj,NVTAdj90,NVTAdjFF,NVTAdjFF90,PriceBTC,PriceUSD,ROI1yr,ROI30d,RevAllTimeUSD,RevHashNtv,RevHashRateNtv,RevHashRateUSD,RevHashUSD,RevNtv,RevUSD,SER,SplyAct10yr,SplyAct180d,SplyAct1d,SplyAct1yr,SplyAct2yr,SplyAct30d,SplyAct3yr,SplyAct4yr,SplyAct5yr,SplyAct7d,SplyAct90d,SplyActEver,SplyActPct1yr,SplyAdrBal1in100K,SplyAdrBal1in100M,SplyAdrBal1in10B,SplyAdrBal1in10K,SplyAdrBal1in10M,SplyAdrBal1in1B,SplyAdrBal1in1K,SplyAdrBal1in1M,SplyAdrBalNtv0.001,SplyAdrBalNtv0.01,SplyAdrBalNtv0.1,SplyAdrBalNtv1,SplyAdrBalNtv10,SplyAdrBalNtv100,SplyAdrBalNtv100K,SplyAdrBalNtv10K,SplyAdrBalNtv1K,SplyAdrBalNtv1M,SplyAdrBalUSD1,SplyAdrBalUSD10,SplyAdrBalUSD100,SplyAdrBalUSD100K,SplyAdrBalUSD10K,SplyAdrBalUSD10M,SplyAdrBalUSD1K,SplyAdrBalUSD1M,SplyAdrTop100,SplyAdrTop10Pct,SplyAdrTop1Pct,SplyCur,SplyExpFut10yr,SplyFF,SplyMiner0HopAllNtv,SplyMiner0HopAllUSD,SplyMiner1HopAllNtv,SplyMiner1HopAllUSD,TxCnt,TxCntSec,TxTfrCnt,TxTfrValAdjNtv,TxTfrValAdjUSD,TxTfrValMeanNtv,TxTfrValMeanUSD,TxTfrValMedNtv,TxTfrValMedUSD,VelCur1yr,VtyDayRet180d,VtyDayRet30d
# 2009-01-09,19,19,19,19,19,19,19,19,19,19,19,19,19,0,0,19,0,19,0,0,0,0,0,0,0,0,0,0,1614334886,19,215,860,16340,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,9.44495122962963E-7,0,950,36500,100,0,950,0,1,0,0,0,0,1,0,0,0,0,11641.53218269,1005828380.584716757433,0,0,950,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,950,950,950,950,950,950,950,950,950,950,950,950,950,0,0,0,0,0,0,0,0,0,0,0,0,0,950,50,50,950,17070250,950,1000,0,1000,0,0,0,0,0,0,0,0,0,0,0,0,0
def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:
    data: CryptoNetworkData = CryptoNetworkData()
    data.Symbol = config.Symbol
    
    cols:str = ['HashRate']
    try:
        if not line[0].isdigit():
            header_split = line.split(',')
            self.col_index = [header_split.index(x) for x in cols]
            return None
        split = line.split(',')
        
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
