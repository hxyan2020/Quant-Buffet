# Original QuantConnect / library Python
# locale=en slug="具有递减碳足迹的基准投资组合"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
# endregion

class BenchmarksPortfolioswithDecreasingCarbonFootprints(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100_000)

    self.leverage: int = 3
    self.quantile: int = 3
    self.portfolio_threshold: float = 0.75

    self.data: Dict[int, Dict[str, float]] = {}

    # DJI stocks
    self.tickers: List[str] = [
        'AXP', 'AMGN', 'AAPL', 'BA', 'CAT', 'CSCO', 'CVX', 'GS', 'HD', 'HON', 
        'IBM', 'INTC', 'JNJ', 'KO', 'JPM', 'MCD', 'MMM', 'MRK', 'MSFT', 'NKE', 
        'PG', 'TRV', 'UNH', 'CRM', 'VZ', 'V', 'WBA', 'WMT', 'DIS', 'DOW'
    ]

    for ticker in self.tickers:
        data: Equity = self.AddEquity(ticker, Resolution.Daily)
        data.SetLeverage(self.leverage)

    # Source: https://esg.exerica.com/Company?Name=Apple
    ghg_emissions: str = self.Download('data.quantpedia.com/backtesting_data/economic/GHG_emissions.csv')
    lines: List[str] = ghg_emissions.split('\r\n')

    for line in lines[1:]:  # skip first comment lines
        if line == '':
            continue
        
        line_split: List[str] = line.split(';')
        year: str = line_split[0]
        if year not in self.data:
            self.data[year] = {}
     
        # N stocks -> n*4 properties
        for i in range(1, len(line_split), 4):
            # parse GHG emissions info
            if line_split[i] not in self.data[year]:
                self.data[year][line_split[i]] = sum( float(line_split[x]) for x in range(i+1, i+4) if line_split[x] != '' )

    self.rebalance_month: int = 7
    self.current_month: int = -1

def OnData(self, slice: Slice) -> None:
    if self.Time.month == self.current_month:
        return
    self.current_month = self.Time.month

    if self.Time.month != self.rebalance_month:
        return

    if str(self.Time.year - 1) not in list(self.data.keys()):
        return

    # calculate emission intensity
    emission_intensity: Dict[Symbol, float] = { 
        self.Symbol(ticker) : self.data[str(self.Time.year - 1)][ticker] / self.Securities[ticker].Fundamentals.FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths \
        for ticker in self.tickers if self.data[str(self.Time.year - 1)][ticker] != 0 and self.Securities[ticker].Fundamentals.HasFundamentalData\
        and not np.isnan(self.Securities[ticker].Fundamentals.FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths) \
        and self.Securities[ticker].Fundamentals.FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths != 0 
    }

    weight: Dict[Symbol, float] = {}
    final_portfolio: List[Symbol] = []
    portfolio_percentage: float = 0.

    # sort and divide portfolio
    if len(emission_intensity) != 0:
        sorted_emissions:List[Symbol] = sorted(emission_intensity, key=emission_intensity.get)
    
        # calculate weights based on marketcap
        mc_sum:float = sum(list(map(lambda symbol: self.Securities[symbol].Fundamentals.MarketCap, sorted_emissions)))
        for symbol in sorted_emissions:
            w: float = self.Securities[symbol].Fundamentals.MarketCap / mc_sum

            portfolio_percentage += w
            if portfolio_percentage
