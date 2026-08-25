# Original QuantConnect / library Python
# locale=en slug="加密货币对冲交易策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from numpy import floor
from datetime import datetime
from itertools import combinations
# endregion

class PairsTradinginCryptocurrencies(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2018, 1, 1)
    self.SetCash(100000)
    
    # formation-trading ratio of 2:1
    self.formation_period:int = int((datetime.now() - self.Time).days / 3 * 2)
    self.z_score_period:int = 6 * 21

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.crypto_tickers:List[str] = [
        'LINKUSD', 'QTUMUSD', 'NEOUSD', 'OMGUSD', 'BATUSD', 'ETHUSD', 'BNTUSD', 'XLMUSD', 'ADAUSD', 'XRPUSD',
        'EOSUSD', 'ETCUSD', 'ZECUSD', 'DASHUSD', 'XMRUSD', 'TRXUSD', 'ENJUSD', 'MANAUSD' # 'BNBUSD'
    ]

    self.possible_pairs = set(combinations(self.crypto_tickers, 2))
    
    self.pair_count:int = 6
    self.leverage:int = 2
    self.price:Dict[str, RollingWindow] = {}
    self.percentage_traded:float = .2
    
    self.threshold:float = 2.
    self.pair_z_score:Dict[TickerPair, RollingWindow] = {}
    
    self.SetWarmup(self.formation_period, Resolution.Daily)
    self.traded_pairs:List[TickerPair] = list()

    # data subscription
    for ticker in self.crypto_tickers:
        data = self.AddCrypto(ticker, Resolution.Daily, Market.Bitfinex)
        data.SetLeverage(self.leverage)

        self.price[ticker] = RollingWindow[float](self.formation_period)

    self.recent_month:int = -1

def OnData(self, data: Slice) -> None:
    # store daily prices
    for ticker in self.crypto_tickers:
        if ticker in data and data[ticker]:
            self.price[ticker].Add(data[ticker].Value)

    if self.IsWarmingUp: return

    for pair in self.traded_pairs:
        price_i:np.ndarray = np.array(list(self.price[pair._ticker_i])[::-1])
        price_j:np.ndarray = np.array(list(self.price[pair._ticker_j])[::-1])

        St:np.ndarray = price_i - price_j
        
        # price residuals, rolling mean and std
        St_rolling:np.ndarray = [St[i - self.z_score_period : i] for i in range(self.z_score_period, self.formation_period)]
        Dt_rolling:np.ndarray = [np.mean(st) for st in St_rolling]
        STDt_rolling:np.ndarray = [np.std(st) for st in St_rolling]

        # z-score
        Zt:np.ndarray = [(st[-1] - Dt_rolling[i]) / STDt_rolling[i] for i, st in enumerate(St_rolling)]

        Zt_mean:float = np.mean(Zt)
        Zt_std:float = np.std(Zt)
        
        quantity_i:float = floor((self.Portfolio.TotalPortfolioValue * self.percentage_traded) / self.pair_count / price_i[-1])
        quantity_j:float = floor((self.Portfolio.TotalPortfolioValue * self.percentage_traded) / self.pair_count / price_j[-1])

        # if the z-score touches the threshold from bellow, the spread is overpriced and shorted by selling coin i and buying coin j
        upper_threshold:float = Zt_mean + (self.threshold * Zt_std)
        lower_threshold:float = Zt_mean - (self.threshold * Zt_std)

        if Zt[-1] > upper_threshold:
            if pair.spread_is_bought():
                self.liquidate_spread(pair)
            else:
                if not pair.spread_is_sold():
                    self.trade_spread(pair, -quantity_i, quantity_j)
            
        # when threshold is hit from above, then the portfolio value is below its long-run value so that the spread is bought, which means buying coin i and selling coin j
        elif Zt[-1]  lower_threshold:
            if pair.spread_is_sold():
                self.liquidate_spread(pair)

        elif Zt[-1] > Zt_mean and Zt[-1]  None:
    self.MarketOrder(pair._ticker_i, quantity_i)
    self.MarketOrder(pair._ticker_j, quantity_j)
    pair.set_quantity(quantity_i, quantity_j)

def liquidate_spread(self, pair) -> None:
    self.MarketOrder(pair._ticker_i, -pair._quantity_i)
    self.MarketOrder(pair._ticker_j, -pair._quantity_j)
    pair.set_quantity(0., 0.)

class TickerPair():
def __init__(self, ticker_i:str, ticker_j:str) -> None:
    self._ticker_i:str = ticker_i
    self._ticker_j:str = ticker_j
    
    self._quantity_i:float = 0.
    self._quantity_j:float = 0.

def set_quantity(self, quantity_i:float, quantity_j:float) -> None:
    self._quantity_i = quantity_i
    self._quantity_j = quantity_j

def spread_is_bought(self) -> bool:
    return self._quantity_i > 0. and self._quantity_j  bool:
    return self._quantity_i  0.
