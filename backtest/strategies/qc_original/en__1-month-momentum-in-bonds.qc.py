# Original QuantConnect / library Python
# locale=en slug="1-month-momentum-in-bonds"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class OneMonthMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.symbols = [
        "EUREX_FGBL1",    # Euro-Bund (10Y) Futures, Continuous Contract #1 (Germany)
        "CME_TY1",        # 10 Yr Note Futures, Continuous Contract #1 (USA)
        "MX_CGB1",        # Ten-Year Government of Canada Bond Futures, Continuous Contract #1 (Canada)
        "ASX_XT1",        # 10 Year Commonwealth Treasury Bond Futures, Continuous Contract #1 (Australia)
        "SGX_JB1",        # SGX 10-Year Mini Japanese Government Bond Futures, Continuous Contract #1 (Japan)
        "LIFFE_R1",       # Long Gilt Futures, Continuous Contract #1 (U.K.)
        "EUREX_FBTP1"     # Long-Term Euro-BTP Futures, Continuous Contract #1 (Italy)
    ]
    
    self.period = 21
    self.quantile = 5
    self.SetWarmUp(self.period)
    
    # Daily ROC data.
    self.data = {}
    
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(5)
        
        self.data[symbol] = self.ROC(symbol, self.period, Resolution.Daily)
    
    self.rebalance_flag: bool = False
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.At(0, 0), self.Rebalance)
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.

def on_data(self, slice: Slice) -> None:
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    # Return sorting.
    sorted_by_return = sorted([x for x in self.data.items() if x[1].IsReady and self.Securities[x[0]].GetLastData() and self.Time.date() = self.quantile:
        quintile = int(len(sorted_by_return) / self.quantile)
        long = [x[0] for x in sorted_by_return[:quintile]]
        short = [x[0] for x in sorted_by_return[-quintile:]]
    # Trade execution.
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([long, short]):
        for symbol in portfolio:
            if slice.contains_key(symbol) and slice[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
def Rebalance(self):
    self.rebalance_flag = True
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
_last_update_date:Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return QuantpediaFutures._last_update_date
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/futures/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaFutures()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['back_adjusted'] = float(split[1])
    data['spliced'] = float(split[2])
    data.Value = float(split[1])
    if config.Symbol.Value not in QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol.Value]:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = data.Time.date()
    return data
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
