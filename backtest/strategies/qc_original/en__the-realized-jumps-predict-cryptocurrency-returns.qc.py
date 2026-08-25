# Original QuantConnect / library Python
# locale=en slug="the-realized-jumps-predict-cryptocurrency-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from datetime import datetime, timedelta
from AlgorithmImports import *
#endregion

class TheRealizedJumpsPredictCryptocurrencyReturns(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2017, 1, 1)
    self.SetCash(1000000)
    
    self.min_prices: int = 60 * 6 # m minuties * n hours
    self.quantile: int = 5
    self.portfolio_percentage: float = .1
    self.leverage: int = 5

    self.cryptos: List[str] = [
        "BTC", # Bitcoin
        "EOS", # EOS
        "ETH", # Ethereum
        "LTC", # Litecoin
        "NEO", # Neo
        "OMG", # OMG Network
        "TRX", # Tron
        "XLM", # Stellar
        "XMR", # Monero
        "XRP", # XRP
        "XVG", # Verge
        "ZRX"  # Ox
    ]
    
    self.data: Dict[Symbol, SymbolData] = {}
    self.SetBrokerageModel(BrokerageName.Bitfinex)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    
    for crypto in self.cryptos:
        crypto_ticker: str = crypto + 'USD'
        data: Securities = self.AddCrypto(crypto_ticker, Resolution.Minute, Market.Bitfinex)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage)

        crypto_symbol: Symbol = data.Symbol
        network_symbol: Symbol = self.AddData(CryptoNetworkData, crypto, Resolution.Daily).Symbol

        self.data[crypto_symbol] = SymbolData(network_symbol)
    
    self.curr_day: int = -1

def OnData(self, data: Slice) -> None:
    crypto_data_last_update_date: Dict[Symbol, datetime.date] = CryptoNetworkData.get_last_update_date()

    # rebalance daily
    if self.Time.day != self.curr_day: 
        self.curr_day = self.Time.day

        realized_signed_jump: Dict[Symbol, float] = {}

        for crypto_symbol, symbol_obj in self.data.items():
            network_symbol: Symbol = symbol_obj.network_symbol
            # make sure crypto data are ready and new data are still comming
            if self.Securities[network_symbol].GetLastData() and self.Time.date() > crypto_data_last_update_date[network_symbol]:
                self.Liquidate()
                return

            if symbol_obj.is_ready(self.min_prices):
                # calculate crypto's realized signed jump
                realized_signed_jump_value: float = symbol_obj.realized_signed_jump()

                # clear crypto prices from last day
                symbol_obj.prices.clear()

                if realized_signed_jump_value != None:
                    realized_signed_jump[crypto_symbol] = realized_signed_jump_value

        weight: Dict[Symbol, float] = {}

        # trade only, when there are enough cryptos with realized signed jump value
        if len(realized_signed_jump) > self.quantile:
            # perform selection
            quantile: int = int(len(realized_signed_jump) / self.quantile)

            sorted_by_jump: List[Symbol] = [x[0] for x in sorted(realized_signed_jump.items(), key=lambda item: item[1])]
            
            # long bottom quantile
            long: List[Symbol] = sorted_by_jump[:quantile]

            # short top quantile
            short: List[Symbol] = sorted_by_jump[-quantile:]

            # value weighting
            for i, portfolio in enumerate([long, short]):
                mc_sum:float = sum(list(map(lambda symbol: self.data[symbol].cap_mrkt_cur_usd, portfolio)))
                for symbol in portfolio:
                    weight[symbol] = ((-1)**i) * self.data[symbol].cap_mrkt_cur_usd / mc_sum

        # trade execution
        portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, self.portfolio_percentage * w) for symbol, w in weight.items() if symbol in data and data[symbol]]
        if len(portfolio) != 0:
            self.SetHoldings(portfolio, True)
        
    # update prices each minute
    for crypto_symbol, symbol_obj in self.data.items():
        network_symbol: Symbol = symbol_obj.network_symbol
        
        if crypto_symbol in data.Bars and data[crypto_symbol]:
            # update prices
            price: float = data[crypto_symbol].Value
            self.data[crypto_symbol].update_prices(price)
        
        if network_symbol in data and data[network_symbol]:
            # get market capitalization
            cap_mrkt_cur_usd: float = data[network_symbol].Value
            self.data[crypto_symbol].update_cap(cap_mrkt_cur_usd)

class SymbolData():
def __init__(self, network_symbol: Symbol) -> None:
    self.network_symbol: Symbol = network_symbol
    self.prices: List[float] = []
    self.cap_mrkt_cur_usd: Union[None, float] = None
        
def update_prices(self, price: float) -> None:
    self.prices.append(price)
    
def update_cap(self, cap_mrkt_cur_usd: float) -> None:
    self.cap_mrkt_cur_usd = cap_mrkt_cur_usd
        
def is_ready(self, min_prices: int) -> bool: 
    return self.cap_mrkt_cur_usd and len(self.prices) >= min_prices

def realized_signed_jump(self) -> Union[None, float]:
    # the time interval for the realized volatility computation is 5 minutes
    # compute the daily realized volatility (sum of squared returns)
    interval_length: int = 5
    prices_length: int = len(self.prices)

    # split minute prices to intervals with same length and for each interval calculate it's return
    intervals_returns: List[float] = [self.calc_return(self.prices[i:i+interval_length]) for i in range(0, prices_length, interval_length)]

    realized_volatility: float = sum(list(map(lambda interval_return: interval_return ** 2, intervals_returns)))

    # can't perform division by zero
    if realized_volatility == 0:
        return None
    
    positive_semivariance, negative_semivariance = 0, 0

    # calculate positive and negative semivarince
    for interval_return in intervals_returns:
        if interval_return > 0:
            # positive semivariance contains is sum of positive interval returns squared
            positive_semivariance += (interval_return ** 2)
        else:
            # negative semivariance contains is sum of negatie interval returns squared
            negative_semivariance += (interval_return ** 2)

    signed_jump: float = positive_semivariance - negative_semivariance
    realized_signed_jump: float = signed_jump / realized_volatility

    return realized_signed_jump

def calc_return(self, prices: List[float]) -> float:
    return (prices[-1] - prices[0]) / prices[0]

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
        cols:str = ['CapMrktCurUSD']

        if not line[0].isdigit():
            header_split = line.split(',')
            self.col_index = [header_split.index(x) for x in cols]
            return None

        split = line.split(',')
        
        data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
        
        for i, col in enumerate(cols):
            data[col] = float(split[self.col_index[i]])

        data.Value = float(split[self.col_index[0]])

        if config.Symbol not in CryptoNetworkData._last_update_date:
            CryptoNetworkData._last_update_date[config.Symbol] = datetime(1,1,1).date()
        if data.Time.date() > CryptoNetworkData._last_update_date[config.Symbol]:
            CryptoNetworkData._last_update_date[config.Symbol] = data.Time.date()

    except:
        return None

    return data

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
