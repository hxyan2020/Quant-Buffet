# Original QuantConnect / library Python
# locale=en slug="low-value-factor-in-india"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from datetime import datetime
import data_tools
# endregion

class LowValueFactorInIndia(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2006, 1, 1)
    self.SetCash(100000)

    self.leverage:int = 5
    self.quantile:int = 10

    self.max_missing_days:int = 5
    
    self.PB_data:dict = {}
    self.data:dict[str, data_tools.SymbolData] = {}

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    # load price to book values
    csv_string_file:str = self.Download('data.quantpedia.com/backtesting_data/equity/india_stocks/price_to_book.csv')
    lines:list = csv_string_file.split('\r\n')
    tickers_with_PB_values:list = lines[0].split(';')[1:]

    for line in lines[1:]: # skip header
        if line == '':
            continue

        line_split:list = line.split(';')

        date:datetime.date = datetime.strptime(line_split[0], '%Y-%m-%d').date()
        # init dictionary for this date
        self.PB_data[date] = {}

        length = len(line_split[1:])
        for i in range(length):
            PB_value:float = float(line_split[i + 1])

            if PB_value != 0:
                ticker:str = tickers_with_PB_values[i]

                self.PB_data[date][ticker] = PB_value

    # subscribe india stocks
    csv_string_file:str = self.Download('data.quantpedia.com/backtesting_data/equity/india_stocks/india_nifty_100_tickers.csv')
    lines:list = csv_string_file.split('\r\n')

    for line in lines[:99]:
        line_split:list = line.split(';')

        for ticker in line_split:
            # subscribe india stock
            security:Security = self.AddData(data_tools.QuantpediaIndiaStocks, ticker, Resolution.Daily)
            security.SetFeeModel(data_tools.CustomFeeModel())
            security.SetLeverage(self.leverage)

            india_stock_symbol:Symbol = security.Symbol

            self.data[ticker] = data_tools.SymbolData(india_stock_symbol)

    self.selection_flag = False
    self.Schedule.On(self.DateRules.MonthEnd(self.market), self.TimeRules.BeforeMarketClose(self.market), self.Selection)

def OnData(self, data: Slice):
    curr_date:datetime.date = self.Time.date()

    if curr_date in self.PB_data:
        PB_values:dict[ticker, float] = self.PB_data[curr_date] 
        
        for ticker, PB_value in PB_values.items():
            self.data[ticker].update_PB_value(PB_value)

    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False

    book_to_market:dict[Symbol, float] = {}
    all_book_to_markets:list = []

    for _, symbol_obj in self.data.items():
        if not symbol_obj.is_ready():
            continue
        
        india_stock_symbol:Symbol = symbol_obj.india_stock_symbol
        if self.Securities[india_stock_symbol].GetLastData() and (self.Time.date() - \
            self.Securities[india_stock_symbol].GetLastData().Time.date()).days = 0 else (1/ (1-z)) for symbol, z in z_score.items()}

    quantile:int = int(len(z_score_transform) / self.quantile)
    sorted_by_z_score:list[Symbol] = [x[0] for x in sorted(z_score_transform.items(), key=lambda item: item[1])]

    # Buy the bottom decile (stocks with the lowest book-to-market ratios)
    long_part:list[Symbol] = sorted_by_z_score[:quantile]
    long_part_length:int = len(long_part)

    # trade execution
    invested:list[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long_part:
            self.Liquidate(symbol)

    for symbol in long_part:
        self.SetHoldings(symbol, 1 / long_part_length)

def Selection(self):
    self.selection_flag = True
