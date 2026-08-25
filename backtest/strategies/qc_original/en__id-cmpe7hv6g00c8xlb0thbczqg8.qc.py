# Original QuantConnect / library Python
# locale=en slug="军费开支与股票市场表现相关性策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import Dict, List
# endregion

class MilitaryExpendituresandPerformanceoftheStockMarkets(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2006, 1, 1)
    self.SetCash(100000)

    self.selection:int = 3
    self.leverage:int = 3

    self.symbols:Dict[str, str] = {
        'USA': 'SPY',
        'United Kingdom': 'EWU',
        'Germany': 'EWG',
        'France': 'EWQ',
        'Italy': 'EWI',
        'Sweden': 'EWD',
        'Netherlands': 'EWN',
        'Spain': 'EWP',
        'Belgium': 'EWK',
        'Switzerland': 'EWL',
        'Canada': 'EWC',
        'Japan': 'EWJ',
        'Mexico': 'EWW',
        'Malaysia': 'EWM',
        'Australia': 'EWA',
        'Singapore': 'EWS',
        'South Korea': 'EWY',
        'Taiwan': 'EWT',
        'Brazil': 'EWZ',
        'South Africa': 'EZA',
        'China': 'FXI',
        'India': 'INDY'
    }

    for country, ticker in self.symbols.items():
        data = self.AddEquity(ticker, Resolution.Daily)
        data.SetLeverage(self.leverage)

    self.military_expenditures:Symbol = self.AddData(data_tools.MilitaryExpenditures, 'military_expenditures', Resolution.Daily).Symbol
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

def OnData(self, data: Slice):
    military_expenditures_last_update_date:datetime.date = data_tools.MilitaryExpenditures._last_update_date
    rebalance_flag:bool = False

    # sort countries by military expenditures
    if self.military_expenditures in data and data[self.military_expenditures]:
        current_military_expenditures:Dict[Symbol, float] = {self.Symbol(ticker) : data[self.military_expenditures][country] for country, ticker in self.symbols.items() \
                                                    if self.Securities[self.Symbol(ticker)].GetLastData() and self.Time.date() = self.selection * 2:
            sorted_military_expenditures:List[Symbol] = sorted(current_military_expenditures, key=current_military_expenditures.get, reverse=True)
            long:List[Symbol] = sorted_military_expenditures[:self.selection]
            short:List[Symbol] = sorted_military_expenditures[-self.selection:]
            rebalance_flag = True
        else:
            self.Liquidate()
            
    if rebalance_flag:
        # trade execution
        invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
        for symbol in invested:
            if symbol not in long + short:
                self.Liquidate(symbol)

        for i, portfolio in enumerate([long, short]):
            for symbol in portfolio:
                if symbol in data and data[symbol]:
                    self.SetHoldings(symbol, ((-1) ** i) / len(portfolio))
