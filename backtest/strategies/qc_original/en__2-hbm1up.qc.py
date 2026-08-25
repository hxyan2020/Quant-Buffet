# Original QuantConnect / library Python
# locale=en slug="外汇套利交易策略-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
import data_tools

class ForexCarryTrade(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1) 
    self.SetCash(100000)
    
    # Data sources
    self.tickers: Dict[str, str] = {
        "CME_AD1": "IR3TIB01AUM156N",  # Australian Dollar Futures, Continuous Contract #1
        "CME_BP1": "LIOR3MUKM",        # British Pound Futures, Continuous Contract #1
        "CME_CD1": "IR3TIB01CAM156N",  # Canadian Dollar Futures, Continuous Contract #1
        "CME_EC1": "IR3TIB01EZM156N",  # Euro FX Futures, Continuous Contract #1
        "CME_JY1": "IR3TIB01JPM156N",  # Japanese Yen Futures, Continuous Contract #1
        "CME_MP1": "IR3TIB01MXM156N",  # Mexican Peso Futures, Continuous Contract #1
        "CME_NE1": "IR3TIB01NZM156N",  # New Zealand Dollar Futures, Continuous Contract #1
        "CME_SF1": "IR3TIB01CHM156N"   # Swiss Franc Futures, Continuous Contract #1
    }
    
    self.traded_count: int = 3
    self.leverage: int = 3

    for ticker, rate_symbol in self.tickers.items():
        # Adding interest rate data
        self.AddData(data_tools.InterestRate3M, rate_symbol, Resolution.Daily)
        
        # Adding futures data
        data = self.AddData(data_tools.QuantpediaFutures, ticker, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        
    self.recent_month = -1
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

def OnData(self, data: Slice) -> None:
    rebalance_flag: bool = False
    rate: Dict[Symbol, float] = {}

    ir_last_update_date: Dict[str, datetime.date] = data_tools.InterestRate3M.get_last_update_date()

    for ticker, int_rate in self.tickers.items():
        # Check if futures data is available
        if ticker in data and data[ticker]:
            if self.recent_month != self.Time.month:
                rebalance_flag = True
                self.recent_month = self.Time.month

            if rebalance_flag:
                # Check if interest rate data is available
                if self.Securities[int_rate].GetLastData() and ir_last_update_date[int_rate] > self.Time.date():
                    # Obtain the last interest rate value
                    rate[self.Symbol(ticker)] = self.Securities[int_rate].Price

    if rebalance_flag:
        targets: List[PortfolioTarget] = []

        if len(rate) >= self.traded_count:
            # Sort symbols by interest rate
            sorted_by_rate: List[Symbol] = sorted(rate, key=rate.get, reverse=True)
            long: List[Symbol] = sorted_by_rate[:self.traded_count]
            short: List[Symbol] = sorted_by_rate[-self.traded_count:]
            
            # Execute orders
            for i, portfolio in enumerate([long, short]):
                for symbol in portfolio:
                    if symbol in data and data[symbol]:
                        targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
        
        self.SetHoldings(targets, True)
