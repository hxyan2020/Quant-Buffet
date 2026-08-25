# Original QuantConnect / library Python
# locale=en slug="reversal-effect-in-india"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import QuantpediaIndiaStocks, SymbolData, CustomFeeModel
#endregion

class ReversalEffectInIndia(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.data:dict = {}
    
    self.portfolio_percentage:float = 0.5
    self.days_in_month:int = 21
    self.period:int = 12 * self.days_in_month # 12 months of daily closes
    self.SetWarmUp(self.period, Resolution.Daily)
    
    self.quantile:int = 5
    self.leverage:int = 5
    self.perf_period:int = 12
    self.max_missing_days:int = 5
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    csv_string_file = self.Download('data.quantpedia.com/backtesting_data/equity/india_stocks/india_nifty_500_tickers.csv')
    line_split = csv_string_file.split(';')
    
    # NOTE: Download method is rate-limited to 100 calls (https://github.com/QuantConnect/Documentation/issues/345)
    for ticker in line_split[:99]:
        security = self.AddData(QuantpediaIndiaStocks, ticker, Resolution.Daily)
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
    
        symbol:Symbol = security.Symbol
        self.data[symbol] = SymbolData(self.period)
    
    self.recent_month:int = -1

def OnData(self, data):
    # store daily prices
    for symbol in self.data:
        if symbol in data and data[symbol]:
            price:float = data[symbol].Value
            if price != 0 and not np.isnan(price):
                self.data[symbol].update(price)
    
    if self.IsWarmingUp: return

    # rebalance monthly
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month

    performance:[Symbol, float] = {}
    
    for symbol, symbol_obj in self.data.items():
        # prices are ready and data is still comming in
        if symbol_obj.is_ready() and self.Securities[symbol].GetLastData() and \
            (self.Time.date() - self.Securities[symbol].GetLastData().Time.date()).days = self.quantile:
        quantile:int = int(len(performance) / self.quantile)
        sorted_by_performance = [x[0] for x in sorted(performance.items(), key=lambda item: item[1], reverse=True)]

        # Long the loser portfolio and short the winner portfolio
        # The winner portfolio consists of stocks with the prior 12-month CARs in the top 20%.
        short_part = sorted_by_performance[-quantile:]
        # The loser portfolio consists of stocks with the prior 12-month CARs in the bottom 20%.
        long_part = sorted_by_performance[:quantile]
            
    # trade execution
    long_count:int = len(long_part)
    short_count:int = len(short_part)

    stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in stocks_invested:
        if symbol not in long_part + short_part:
            self.Liquidate(symbol)

    for symbol in long_part:
        self.SetHoldings(symbol, (1 / long_count) * self.portfolio_percentage)
    for symbol in short_part:
        self.SetHoldings(symbol, (-1 / short_count) * self.portfolio_percentage)
