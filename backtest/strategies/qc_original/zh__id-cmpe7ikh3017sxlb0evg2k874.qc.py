# Original QuantConnect / library Python
# locale=zh slug="加密货币中的套息因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
class CarryFactorInCryptocurrencies(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(1_000_000)
    
    # Coin issuance seven days data and data about first of those seven days
    self.period: int = 7
    self.count_days: int = 1
    self.percentage_traded: float = 0.1
    
    self.symbols: Dict[str, str] = {
        'BTC' : 'BTCUSD',
        'ETH' : 'ETHUSD', 
        'LTC' : 'LTCUSD', 
        'ETC' : 'ETCUSD',
        'XMR' : 'XMRUSD',
        'ZEC' : 'ZECUSD'
    }
    
    self.data: Dict[str, SymbolData] = {}
    self.SetBrokerageModel(BrokerageName.Bitfinex)  
    for crypto, ticker in self.symbols.items():
        data: Securities = self.AddCrypto(ticker, Resolution.Daily, Market.Bitfinex)
        
        self.AddData(CryptoNetworkData, crypto, Resolution.Daily)
        self.data[crypto] = SymbolData(self.period)
    
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
        
def OnData(self, data: Slice) -> None:
    crypto_data_last_update_date: Dict[Symbol, datetime.date] = CryptoNetworkData.get_last_update_date()
    # Store daily data.
    for symbol in self.symbols:
        if symbol in data and data[symbol]:
            coin_issuance: float = data[symbol].Price
            if coin_issuance != 0:
                self.data[symbol].update(coin_issuance)
    if self.Time.date().weekday() != 0:
        return
    if self.count_days == self.period:
        self.count_days = 1
    else:
        self.count_days = self.count_days + 1
        return
    
    long: List[str] = []
    short: List[str] = []
    
    for crypto, ticker in self.symbols.items():
        # network data is still comming in
        if self.Securities[crypto].GetLastData() and self.Time.date() > crypto_data_last_update_date[crypto]:
            continue
        
        if self.data[crypto].is_ready():
            carry_metric: float = self.data[crypto].carry_metric()
            
            if carry_metric > 0.:
                long.append(self.Symbol(ticker))
            else:
                short.append(self.Symbol(ticker))
    
    # Trade Execution
    invested: List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
    for i, portfolio in enumerate([long, short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, round(((-1) ** i) / len(portfolio) * self.percentage_traded, 2))
    
class SymbolData():
def __init__(self, period: int) -> None:
    self.coin_issuance_data: RollingWindow = RollingWindow[float](period)
    
def update(self, value: float) -> None:
    self.coin_issuance_data.Add(value)
    
def carry_metric(self) -> float:
    issuance_data: List[float] = list(self.coin_issuance_data)
    return sum(issuance_data) / issuance_data[-1]
    
def is_ready(self) -> bool:
    return self.coin_issuance_data.IsReady
    
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
    try:
        cols:str = ['SplyCur']
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
