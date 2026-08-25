# Original QuantConnect / library Python
# locale=en slug="blended-factors-in-cryptocurrencies"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from typing import List, Dict
class BlendedFactorsinCryptocurrencies(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(1_000_000)
    
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
        
def OnData(self, data: Slice) -> None:
    crypto_data_last_update_date: Dict[Symbol, datetime.date] = CryptoNetworkData.get_last_update_date()
    # Store daily price data.
    for crypto, ticker in self.symbols.items():
        if crypto in data and data[crypto]:
            cap_mrkt_cur_usd: float = data[crypto].Capmrktcurusd
            txtfr_val_adj_usd: float = data[crypto].Txtfrvaladjusd
            coin_issuance: float = data[crypto].Price
            
            if cap_mrkt_cur_usd != 0 and txtfr_val_adj_usd != 0 and coin_issuance != 0:
                self.data[crypto].update_data(cap_mrkt_cur_usd, txtfr_val_adj_usd, coin_issuance)
        
        if ticker in data:
            if data[ticker]:
                self.data[crypto].update_price(data[ticker].Price)
    
    if self.Time.date().weekday() != 0:
        return
    if self.count_days == 7:
        self.count_days = 1
    else:
        self.count_days = self.count_days + 1
        return
    
    symbols_ready = [x for x in self.symbols if self.data[x].is_ready() and self.Securities[x].GetLastData() and self.Time.date()  0 else carry_metric_short.append(ticker)
        valuation_metric_long.append(ticker) if valuation_metric > 0 else valuation_metric_short.append(ticker)
        momentum_long.append(ticker) if momentum > 0 else momentum_short.append(ticker)
    
    for i, portfolio in enumerate([[carry_metric_long, valuation_metric_long, momentum_long], [carry_metric_short, valuation_metric_short, momentum_short]]):
        for sub_portfolio in portfolio:
            for ticker in sub_portfolio:
                weight[ticker] += ((-1)**i) * self.percentage_traded / len(sub_portfolio)
    # trade execution
    invested: List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in weight:
            self.Liquidate(symbol)
    for symbol, w in weight.items():
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, w)
class SymbolData():
def __init__(self, period: int) -> None:
    self.coin_issuance: RollingWindow = RollingWindow[float](period)
    self.transactions: RollingWindow = RollingWindow[float](period)
    self.curr_market_cap: float = 0.
    self.Price: RollingWindow = RollingWindow[float](period)
    
def update_data(self, current_market_value: float, num_of_transactions: int, coin_issuance: float) -> None:
    self.transactions.Add(num_of_transactions)
    self.curr_market_cap = current_market_value
    self.coin_issuance.Add(coin_issuance)
    
def update_price(self, price: float) -> None:
    self.Price.Add(price)
    
def carry_metric(self) -> float:
    seven_days_coin_issuance: List[float] = [x for x in self.coin_issuance]
    # return -1 * (sum(seven_days_coin_issuance) / seven_days_coin_issuance[-1])
    return (sum(seven_days_coin_issuance) / seven_days_coin_issuance[-1])
def valuation_metric(self) -> float:
    trailing_data: List[float] = [x for x in self.transactions]
    return self.curr_market_cap / np.mean(trailing_data)

def momentum(self) -> float:
    prices: List[float] = [x for x in self.Price]
    return prices[0] / prices[-1] - 1
    
def is_ready(self) -> bool:
    return self.coin_issuance.IsReady and self.transactions.IsReady and self.Price.IsReady
    
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
        cols:str = ['SplyCur', 'CapMrktCurUSD', 'TxTfrValAdjUSD']
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
