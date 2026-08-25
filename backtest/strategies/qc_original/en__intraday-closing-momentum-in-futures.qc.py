# Original QuantConnect / library Python
# locale=en slug="intraday-closing-momentum-in-futures"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from datetime import datetime
# endregion

class IntradayClosingMomentuminFutures(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)

    self.tickers:list[str] = [
        # equity
        Futures.Indices.SP500EMini, # E-mini S&P 500 Futures
        Futures.Indices.NASDAQ100EMini, # E-mini Nasdaq-100 Futures
        Futures.Indices.Russell2000EMini, # E-mini Russell 2000 Index Futures
    ]

    self.perf_period_start_time1:datetime = datetime(2000, 1, 1, 9, 31).time()
    self.perf_period_start_time2:datetime = datetime(2000, 1, 1, 10, 0).time()
    self.perf_period_end_time:datetime = datetime(2000, 1, 1, 15, 30).time()

    self.open_trade_time:datetime = datetime(2000, 1, 1, 15, 30).time()
    self.close_trade_time:datetime = datetime(2000, 1, 1, 16, 0).time()
    
    # self.perf_period_start_hour1:int = 9
    # self.perf_period_start_minute1:int = 31
    self.perf_period_start_hour2:int = 10
    self.perf_period_start_minute2:int = 0
    self.perf_period_end_hour:int = 15
    self.perf_period_end_minute:int = 30

    self.open_trade_hour:int = 15
    self.open_trade_minute:int = 30
    self.close_trade_hour:int = 16
    self.close_trade_minute:int = 0
    self.stored_price_cnt:int = 3

    self.portfolio_percentage:float = 0.1

    self.long_leg:list[Symbol] = []
    self.short_leg:list[Symbol] = []

    self.open_orders:list[list[Symbol, float]] = []

    self.futures_data:dict[str, FutureData] = {}
    
    for ticker in self.tickers:
        future:Symbol = self.AddFuture(ticker, Resolution.Minute)
        future.SetFilter(0, 90)
        self.futures_data[ticker] = FutureData(future.Symbol)
    
def OnData(self, data: Slice):
    if (self.Time.time() == self.perf_period_start_time1) \
        or (self.Time.time() == self.perf_period_start_time2) \
        or (self.Time.time() == self.perf_period_end_time):
        
        for ticker, future_data in self.futures_data.items():
            contract:FuturesContract = future_data.contract
            contract_symbol:Symbol|None = contract.Symbol if contract else None

            if contract_symbol and self.Securities[contract_symbol].Price != 0:
                hist = self.History(contract_symbol, 1, Resolution.Minute)
                if not hist.empty:
                    price:float = hist['close'].iloc[-1]
                    future_data.update_prices(price)

            if self.Time.time() == self.perf_period_end_time:
                if contract_symbol and future_data.prices_ready() and self.Securities[contract_symbol].IsTradable \
                    and (contract.Expiry.date() > (self.Time.date() + timedelta(days=2))):

                    if future_data.buy_signal():
                        self.long_leg.append(contract_symbol)

                future_data.reset_prices()

    # find near contract
    for ticker, future_data in self.futures_data.items():
        curr_contract:FuturesContract|None = future_data.contract
        # future_data.update_contract(None)

        if curr_contract is None or ((curr_contract.Expiry.date() - timedelta(days=1))  None:
    self.symbol = symbol
    self.contract = None
    self.prices:RollingWindow = RollingWindow[float](stored_price_cnt)
    self.stored_price_cnt = stored_price_cnt

def update_contract(self, contract) -> None:
    self.contract = contract

def update_prices(self, price:float) -> None:
    self.prices.Add(price)

def prices_ready(self) -> bool:
    return self.prices.IsReady

def buy_signal(self) -> bool:
    result:bool = (self.prices[0] / self.prices[self.stored_price_cnt-1] - 1) > 0 and (self.prices[1] / self.prices[self.stored_price_cnt-1] - 1) > 0
    return result

def reset_prices(self) -> None:
    self.prices.Reset()
