# Original QuantConnect / library Python
# locale=en slug="印度市场中的对抗贝塔策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from scipy import stats
import data_tools
#endregion

class BettingAgainstBetainIndia(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100000)
    
    self.data:dict = {}
    self.long_term_period:int = 5 * 12 * 21
    self.short_term_period:int = 1 * 12 * 21
    self.SetWarmUp(self.short_term_period, Resolution.Daily)
    
    self.quantile:int = 5
    self.max_missing_days:int = 5
    self.market = self.AddData(data_tools.BSE_200, 'BSE_200', Resolution.Daily).Symbol
    self.data[self.market] = data_tools.SymbolData(self.short_term_period)
    
    csv_string_file = self.Download('data.quantpedia.com/backtesting_data/equity/india_stocks/india_nifty_100_tickers.csv')
    line_split = csv_string_file.split(';')
    
    # NOTE: Download method is rate-limited to 100 calls (https://github.com/QuantConnect/Documentation/issues/345)
    self.ticker:list[str] = line_split[:99]
    
    for ticker in self.ticker:
        security = self.AddData(data_tools.QuantpediaIndiaStocks, ticker, Resolution.Daily)
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(5)
    
        self.data[ticker] = data_tools.SymbolData(self.short_term_period)

    self.recent_month:int = -1

def OnData(self, data):
    rebalance_flag:bool = False

    # rebalance once a month
    if not self.IsWarmingUp and self.Time.month != self.recent_month:
        rebalance_flag = True
        self.recent_month = self.Time.month
    
    beta:dict[str, float] = {}
    
    # store daily price data
    if self.market in data and data[self.market]:
        # market price data
        self.data[self.market].update(data[self.market].Value)
        
        # stock price data
        for ticker in self.ticker:
            if ticker in data and data[ticker]:
                self.data[ticker].update(data[ticker].Value)
            else:
                if self.data[ticker].closes.Count != 0:
                    self.data[ticker].update(self.data[ticker].closes[0])

            if self.IsWarmingUp: continue
            if rebalance_flag:
                if self.data[ticker].is_ready() and self.data[self.market].is_ready():
                    # stock price data is still comming in
                    if self.Securities[ticker].GetLastData() and (self.Time.date() - self.Securities[ticker].GetLastData().Time.date()).days = 0 else (1/(1-z)) for ticker, z in z_score.items()}

        long:list[Symbol] = []
        short:list[Symbol] = []

        if len(z_transform) >= self.quantile:
            quantile:int = int(len(z_transform) / self.quantile)
            sorted_by_zscore = sorted(z_transform.items(), key=lambda item: item[1], reverse=True)

            long = [x[0] for x in sorted_by_zscore[:quantile]]
            short = [x[0] for x in sorted_by_zscore[-quantile:]]
            
        # trade execution
        long_count:int = len(long)
        short_count:int = len(short)

        stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
        for symbol in stocks_invested:
            if symbol not in long + short:
                self.Liquidate(symbol)

        for symbol in long:
            self.SetHoldings(symbol, 1 / long_count)
        for symbol in short:
            self.SetHoldings(symbol, -1 / short_count)
