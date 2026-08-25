# Original QuantConnect / library Python
# locale=en slug="timing-carry-trade-with-central-banks-announcements"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from pandas.tseries.offsets import BDay
from pandas.core.frame import DataFrame
# endregion

class TimingCarryTradewithCentralBanksAnnouncements(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.bond:Symbol = self.AddEquity('IEF', Resolution.Daily).Symbol
    # self.dollar:Symbol = self.AddEquity('UUP', Resolution.Daily).Symbol

    # Cash rate source: https://fred.stlouisfed.org/series/IR3TIB01USM156N
    self.symbols:Dict[str, str] = {
        "CME_AD1" : "IR3TIB01AUM156N",   # Australian Dollar Futures, Continuous Contract #1
        "CME_BP1" : "LIOR3MUKM",         # British Pound Futures, Continuous Contract #1
        "CME_CD1" : "IR3TIB01CAM156N",   # Canadian Dollar Futures, Continuous Contract #1
        "CME_EC1" : "IR3TIB01EZM156N",   # Euro FX Futures, Continuous Contract #1
        "CME_JY1" : "IR3TIB01JPM156N",   # Japanese Yen Futures, Continuous Contract #1
        "CME_MP1" : "IR3TIB01MXM156N",   # Mexican Peso Futures, Continuous Contract #1
        "CME_NE1" : "IR3TIB01NZM156N",   # New Zealand Dollar Futures, Continuous Contract #1
        "CME_SF1" : "IR3TIB01CHM156N"    # Swiss Franc Futures, Continuous Contract #1
    }
    
    self.long:List[str] = []
    self.short:List[str] = []

    # load Federal Open Market Committee dates
    csv_string_file:str = self.Download('data.quantpedia.com/backtesting_data/economic/fed_days.csv')
    dates:str = csv_string_file.split('\r\n')
    self.fomc_dates:List[datetime.date] = [datetime.strptime(x, "%Y-%m-%d") + BDay(1) for x in dates]

    self.traded_count:int = 3       # fx carry long and short count
    self.leverage:int = 3
    self.period:int = 2

    # data subscription
    for symbol, rate_symbol in self.symbols.items():
        self.AddData(data_tools.InterestRate3M, rate_symbol, Resolution.Daily)

        data = self.AddData(data_tools.QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        
    self.fx_carry_flag:bool = None
    self.lag_flag:bool = False      # handles currency futures daily close data availability

def OnData(self, data: Slice) -> None:
    if self.lag_flag:
        self.lag_flag = False
        if not self.fx_carry_flag:
            
            self.fx_carry_flag = None

            # sell futures to gain exposure in USD
            for symbol in self.symbols.keys():
                if symbol in data and data[symbol]:
                    self.SetHoldings(symbol, -1 / len(self.symbols))
  
        if self.fx_carry_flag:
            self.fx_carry_flag = None

            for symbol in self.long:
                self.SetHoldings(symbol, 1 / len(self.long))
            for symbol in self.short:
                self.SetHoldings(symbol, -1 / len(self.short))
            
            self.long.clear()
            self.short.clear()

    # not FED day
    if self.Time.timestamp() not in [i.timestamp() for i in self.fomc_dates]:
        return

    self.Liquidate()

    # signal check
    history:DataFrame = self.History([self.market] + [self.bond], self.period, Resolution.Daily)['close'].unstack(level=0)
    if len(history.columns) > 1:
        if history[self.market].iloc[1]  self.Time.date() \
                    and self.Securities[symbol].GetLastData() and qp_futures_last_update_date[symbol] > self.Time.date():
                    rate[symbol] = self.Securities[int_rate].Price

        if rebalance_flag:
            if len(rate) >= self.traded_count:
                # interbank rate sorting
                sorted_by_rate = sorted(rate.items(), key = lambda x: x[1], reverse = True)
                self.long = [x[0] for x in sorted_by_rate[:self.traded_count]]
                self.short = [x[0] for x in sorted_by_rate[-self.traded_count:]]
