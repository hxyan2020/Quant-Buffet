# Original QuantConnect / library Python
# locale=en slug="改进后的跨资产时间序列动量策略-i-xtsm"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# endregion
class ImprovedCrossAssetTimeSeriesMomentumIXTSM(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2005, 1, 1) 
    self.SetCash(100000)
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.bil:Symbol = self.AddEquity('BIL', Resolution.Daily).Symbol
    self.industrial_metal_index:Symbol = self.AddData(IndustrialMetalIndex, 'IMI', Resolution.Daily).Symbol
    
    self.leverage:int = 5
    self.period:int = 12 * 21
    self.selection_months:List[int] = [1, 4, 7, 10]
    self.SetWarmup(self.period, Resolution.Daily)
    for symbol in [self.market, self.bil]:
        self.Securities[symbol.Value].SetLeverage(self.leverage)
    self.market_mom:Momentum = self.MOM(self.market, self.period, Resolution.Daily)
    self.industrial_metal_mom:Momentum = self.MOM(self.industrial_metal_index, self.period, Resolution.Daily)
    self.rebalance_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)
def OnData(self, data: Slice) -> None:
    if self.IsWarmingUp:
        return
    # quarterly rebalance
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    # check industrial metal index data arrival
    industrial_metal_last_update_date:datetime.date = IndustrialMetalIndex.get_last_update_date()
    if self.Securities[self.industrial_metal_index].GetLastData():
        if self.Time.date() >= industrial_metal_last_update_date: 
            self.Liquidate()
            return
    # compare momentums and define traded asset and trade direction
    traded_asset:Symbol|None = None
    trade_direction:int = 0
    if all(x in data and data[x] for x in [self.market, self.industrial_metal_index]):
        market_mom:float = self.market_mom.Current.Value
        industrial_metal_mom:float = self.industrial_metal_mom.Current.Value
        if market_mom >= 0:
            traded_asset = self.market
            trade_direction = 1
        else:
            if industrial_metal_mom = 0:
                traded_asset = self.bil
                trade_direction = 1
    
        # trade execution
        if not self.Portfolio[traded_asset].Invested:
            self.Liquidate()
            self.SetHoldings(traded_asset, trade_direction)
        else:
            self.SetHoldings(traded_asset, trade_direction)
def Selection(self) -> None:
    if self.Time.month in self.selection_months:
        self.rebalance_flag = True
# Source: https://www.investing.com/indices/gsci-industrial-metals-historical-data
class IndustrialMetalIndex(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource('data.quantpedia.com/backtesting_data/index/GSCI_Industrial_Metal_index.csv', SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)

_last_update_date:datetime.date = datetime(1,1,1).date()
@staticmethod
def get_last_update_date() -> datetime.date:
   return IndustrialMetalIndex._last_update_date
def Reader(self, config, line, date, isLiveMode):
    data = IndustrialMetalIndex()
    data.Symbol = config.Symbol
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    # Parse the CSV file's columns into the custom data class
    data.Time = datetime.strptime(split[0], "%m/%d/%Y") + timedelta(days=1)
    data.Value = float(split[1])
    if data.Time.date() > IndustrialMetalIndex._last_update_date:
        IndustrialMetalIndex._last_update_date = data.Time.date()
    
    return data
