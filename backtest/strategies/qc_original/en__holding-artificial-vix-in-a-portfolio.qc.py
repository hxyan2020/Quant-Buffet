# Original QuantConnect / library Python
# locale=en slug="holding-artificial-vix-in-a-portfolio"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from numpy import mean, std
from AlgorithmImports import *
class HoldingArtificialVIXinaPortfolio(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2012, 1, 1)
    self.init_cash = 100000
    self.SetCash(self.init_cash)
    
    self.vix: Symbol = self.AddData(CBOE, 'VIX', Resolution.Daily).Symbol
    self.period: float = 12 * 21
    self.SetWarmUp(self.period, Resolution.Daily)
    self.vix_prices = []
    
    data: Equity = self.AddEquity('SPY', Resolution.Daily)
    data.SetLeverage(10)
    data.SetFeeModel(CustomFeeModel())
    self.market: Symbol = data.Symbol
    option = self.AddOption(self.market, Resolution.Minute)
    # filter the contracts with strikes between(ATM Strike - 10 * strike space value, market price + 10 * strike space value) and with expiration days less than 35 days
    option.SetFilter(-5, +5, timedelta(days=0), timedelta(days=35))
    # storing an entire option chain for a single underlying security
    self.chains = None
    
    self.portfolio_multiplier = 1 # invest only n percent of portfolio
    
    # benchmark chart settings
    benchmark_chart = Chart("Equity Curve With Benchmark")
    benchmark_chart.AddSeries(Series("Equity Curve", SeriesType.Line, 0))
    benchmark_chart.AddSeries(Series("Benchmark", SeriesType.Line, 0))
    self.benchmark_values: List[float] = []
    self.AddChart(benchmark_chart)
    
    self.last_day: int = -1
def OnData(self, slice: Slice) -> None:
    if self.vix in slice and slice[self.vix]:
        vix_price: float = slice[self.vix].Value
        self.vix_prices.append(vix_price)
    
    for i in slice.OptionChains:
        self.chains = i.Value
    
    # check once a day
    if self.Time.day == self.last_day:
        return
    self.last_day = self.Time.day
    
    if len(self.vix_prices)
