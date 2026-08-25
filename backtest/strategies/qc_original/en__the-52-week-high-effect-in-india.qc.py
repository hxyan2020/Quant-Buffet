# Original QuantConnect / library Python
# locale=en slug="the-52-week-high-effect-in-india"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import List, Dict
# endregion

class The52WeekHighEffectinIndia(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(10000000) # INR

    self.period:int = 252
    self.universe_count:int = 100

    self.data:Dict[Symbol, data_tools.SymbolData] = {}
    self.tickers_to_ignore:List[str] = ['TATAMTRDVR', 'LODHA']

    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/india_stocks/nse_500_tickers.csv')
    ticker_lines:List[str] = ticker_file_str.split('\r\n')
    tickers = [ ticker_line.split(',')[0] for ticker_line in ticker_lines[1:] ]

    self.quantile:int = 5
    self.leverage:int = 3

    for t in tickers[:self.universe_count]:
        # price data subscription
        if t in self.tickers_to_ignore:
            continue
        data:Security = self.AddData(data_tools.IndiaStocks, t, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        stock_symbol:Symbol = data.Symbol

        self.data[stock_symbol] = data_tools.SymbolData(stock_symbol, self.period)
    
    self.SetWarmUp(self.period, Resolution.Daily)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

    self.recent_month:int = -1

def OnData(self, data: Slice) -> None:
    price_last_update_date:Dict[Symbol, datetime.date] = data_tools.IndiaStocks.get_last_update_date()

    # custom data still comming in
    if all([self.Securities[x].GetLastData() for x in list(self.data.keys())]) and any([self.Time.date() >= price_last_update_date[x] for x in price_last_update_date]):
        self.Liquidate()
        return

    # store daily price data
    for price_symbol, symbol_data in self.data.items():
        if price_symbol in data and data[price_symbol] and data[price_symbol].Value != 0:
            price:float = data[price_symbol].Value
            self.data[price_symbol].update_price(price)
    
    if self.IsWarmingUp:
        return
        
    # monthly rebalance
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month

    proximity:Dict[Symbol, float] = {symbol: symbol_data.get_latest_price() / symbol_data.high_price() for symbol, symbol_data in self.data.items() if symbol_data.is_ready()}

    if len(proximity) > self.quantile:
        sorted_proximity:List[Symbol] = sorted(proximity, key=proximity.get)
        quantile:int = int(len(sorted_proximity) / self.quantile)
        long:List[Symbol] = sorted_proximity[:quantile]
        short:List[Symbol] = sorted_proximity[-quantile:]

        targets:List[PortfolioTarget] = []
        for i, portfolio in enumerate([long, short]):
            for symbol in portfolio:
                if symbol in data and data[symbol]:
                    targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
        
        self.SetHoldings(targets, True)
