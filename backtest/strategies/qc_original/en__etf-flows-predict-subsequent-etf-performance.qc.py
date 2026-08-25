# Original QuantConnect / library Python
# locale=en slug="etf-flows-predict-subsequent-etf-performance"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
from data_tools import CustomFeeModel, QuantpediaSharesOutstandingETFs, SymbolData
# endregion

class ETFFlowsPredictSubsequentETFPerformance(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)

    self.leverage:int = 5

    self.market_close_minute:int = 0
    self.market_close_hour:int = 16

    self.market_open_minute:int = 31
    self.market_open_hour:int = 9

    self.max_missing_days:int = 5

    self.open_trades:List[List[Symbol, float]] = []
    self.data:Dict[Symbol, SymbolData] = {}

    csv_file:str = self.Download('data.quantpedia.com/backtesting_data/equity/etf_shares_outstanding.csv')
    lines:List[str] = csv_file.split('\r\n')

    tickers:List[str] = lines[0].split(';')[1:]

    for ticker in tickers:
        data = self.AddEquity(ticker, Resolution.Minute)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage)

        self.data[ticker] = SymbolData(data.Symbol)

    self.etf_shares_outstanding:Symbol = self.AddData(QuantpediaSharesOutstandingETFs,
        'etf_shares_outstanding', Resolution.Daily).Symbol

def OnData(self, data: Slice):
    if self.etf_shares_outstanding in data and data[self.etf_shares_outstanding]:
        shares_outstanding:Dict[str, float] = data[self.etf_shares_outstanding].GetProperty('shares_outstanding')

        curr_date:datetime.date = self.Time.date()

        for ticker, shares_outstanding in shares_outstanding.items():
            self.data[ticker].update_shares_outstanding(curr_date, shares_outstanding)

    if self.Time.minute == self.market_close_minute and self.Time.hour == self.market_close_hour:
        # on market close calculate flow values and create MarketOnOper orders
        long_leg:List[str] = []
        short_leg:List[str] = []
        curr_date:datetime.date = self.Time.date()
        
        for ticker, symbol_data in self.data.items():
            symbol:Symbol = symbol_data.get_symbol()

            if not symbol_data.data_still_coming(curr_date, self.max_missing_days):
                # make sure shares outstanding data are still coming
                symbol_data.reset()

            elif symbol_data.shares_outstanding_ready() and symbol in data and data[symbol]:
                # trade only ETFs, which have price and shares outstanding
                price:float = data[symbol].Value
                symbol_data.update_price(price)
                symbol_data.update_market_cap()

                flow_value:float = symbol_data.get_flow()
                
                if flow_value > 0:
                    long_leg.append(ticker)
                elif flow_value  float:
    price:float = self.data[ticker].get_price()
    market_cap:float = self.data[ticker].get_market_cap()

    quantity:float = np.floor((weight * (market_cap / total_cap)) / price)

    return quantity
