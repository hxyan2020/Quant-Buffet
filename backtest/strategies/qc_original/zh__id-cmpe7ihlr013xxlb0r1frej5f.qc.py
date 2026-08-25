# Original QuantConnect / library Python
# locale=zh slug="序列化内幕交易"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
from typing import List, Dict
import pandas as pd
from dateutil.relativedelta import relativedelta
#endregion
class SequencedInsiderTrading(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2014, 1, 1)
    self.SetCash(100000)
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.insider_data: Dict[Symbol, QuiverInsiderTrading] = {}
    self.routine_traders_stocks: List[str] = []
    self.leverage: int = 3
    self.min_consecutive_month_count: int = 2
    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        symbol: Symbol = security.Symbol
        dataset_symbol: Symbol = self.AddData(QuiverInsiderTrading, symbol).Symbol
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # monthly selection
    if not self.selection_flag:
        return Universe.Unchanged
    selected: List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.MarketCap != 0 and \
        x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    selected: Dict[str, Symbol] = {x.Symbol.Value: x.Symbol for x in selected}
    aggregated_data: Dict[Tuple[datetime.date, str], float] = {}
    curr_month: int = self.Time
    insiders: Dict[str, List[Tuple[datetime.date, str, float]]] = {}
    # aggregate data on monthly format
    for name, data in self.insider_data.items():
        if name not in insiders:
            insiders[name] = []
        for data_point in data:
            date: str = data_point[0].strftime('%m-%Y')
            key = (date, data_point[1])
            if key in aggregated_data:
                if data_point[2] is not None:
                    aggregated_data[key] += data_point[2]
            else:
                aggregated_data[key] = data_point[2]
        insiders[name].append([(key[0], key[1], shares) for key, shares in aggregated_data.items()])
        aggregated_data.clear()
    # check for routine insider trades
    months_to_check: List[str] = [(curr_month - relativedelta(months=i)).strftime('%m-%Y') for i in [1, 2, 13, 14, 25, 26, 37, 38]]
    for name, data in insiders.items():
        ticker: str = data[0][0][1]
        if len(data[0]) > self.min_consecutive_month_count:
            if (data[0][-1][0] == months_to_check[0] and data[0][-2][0] == months_to_check[1] and \
                all(i[0] != month for month in months_to_check[2:] for i in data[0])) and \
                ticker in selected:
                self.routine_traders_stocks.append(selected[ticker])
    
    return [x for x in selected.values()]
def OnData(self, data: Slice) -> None:
    for insider_trades in data.Get(QuiverInsiderTrading).values():
        for insider_trade in insider_trades:
            if insider_trade.Name not in self.insider_data:
                self.insider_data[insider_trade.Name] = []           
            self.insider_data[insider_trade.Name].append((insider_trade.Time, insider_trade.Symbol.Value, insider_trade.Shares))

    # monthly rebalance
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    targets: List[PortfolioTarget] = []
    for symbol in self.routine_traders_stocks:
        if symbol in data and data[symbol]:
            targets.append(PortfolioTarget(symbol, 1 / len(self.routine_traders_stocks)))

    self.SetHoldings(targets, True)
    self.routine_traders_stocks.clear()
def Selection(self) -> None:
    self.selection_flag = True
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
