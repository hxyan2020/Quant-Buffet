# Original QuantConnect / library Python
# locale=zh slug="有毒物质排放与股票表现"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from numpy import isnan
from typing import List, Dict
# endregion
class ToxicalReleasesandStocksPerformance(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.leverage: int = 10
    self.quantile: int = 5
 
    self.toxic_release_data: Dict[Dict[datetime.date, str]] = {}
    self.report_dates: Dict[datetime.date, datetime.date] = {}
    self.last_data: Dict[str, float] = {}
    self.last_year: int = -1
    self.weight: Dict[Symbol, float] = {}
    
    # Data source: https://peri.umass.edu/top-100-indexes-archives
    toxic_release_data: str = self.Download('data.quantpedia.com/backtesting_data/economic/toxic_releases.json')
    toxic_release_data_json: Dict[str] = json.loads(toxic_release_data)
    for obj in toxic_release_data_json:
        report_date: int = datetime.strptime(obj['report_date'], "%Y").year
        data_date: int = datetime.strptime(obj['data_date'], "%Y").year
        if report_date not in self.toxic_release_data:
            self.toxic_release_data[report_date] = {}
            self.report_dates[report_date] = data_date
        for stock_data in obj['stocks']:
            ticker: str = stock_data['ticker']
            try:
                toxic_release: float = float(stock_data['toxic air release[mil./lb]'])
            except:
                continue
            self.toxic_release_data[report_date][ticker] = toxic_release
    self.current_year: int = -1
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # rebalance yearly
    if self.Time.year == self.current_year:
        return Universe.Unchanged
    self.current_year = self.Time.year
    if self.Time.year not in self.toxic_release_data:
        return Universe.Unchanged
    current_report_year = self.Time.year
    current_data_year = self.report_dates[current_report_year]
    selected: List[Fundamental] = [x for x in fundamental if x.Symbol.Value in list(self.toxic_release_data[current_report_year]) and x.MarketCap != 0 and \
        not isnan(x.FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths) and x.FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths != 0]
    emissions_by_dollar: Dict[Fundamental, float] = {}

    if len(self.last_data) != 0:
        # check if data is present
        for stock in selected:
            if stock.Symbol.Value in self.last_data:
                toxic_release_change: float = self.toxic_release_data[current_report_year][stock.Symbol.Value] - self.last_data[stock.Symbol.Value]
                emissions_dolar: float = toxic_release_change / stock.FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths
                emissions_by_dollar[stock] = emissions_dolar
    # save current data for next selection
    self.last_data.clear()
    self.last_data = {stock.Symbol.Value: self.toxic_release_data[current_report_year][stock.Symbol.Value] for stock in selected}
    self.last_year = self.report_dates[self.Time.year]
    if len(emissions_by_dollar) >= self.quantile:
        self.selection_flag = True
        # sort stocks and divide into quantiles
        sorted_stocks: List[Fundamental] = sorted(emissions_by_dollar, key=emissions_by_dollar.get, reverse=True)
        quantile: int = int(len(sorted_stocks) / self.quantile)
        long: List[Fundamental] = sorted_stocks[:quantile]
        short: List[Fundamental] = sorted_stocks[-quantile:]
        # value weighting
        for i, portfolio in enumerate([long, short]):
            mc_sum: float = sum(list(map(lambda stock: stock.MarketCap, portfolio)))
            for stock in portfolio:
                self.weight[stock.Symbol] = ((-1)**i) * stock.MarketCap / mc_sum
    return list(self.weight.keys())
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # trade execution
    invested: List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in self.weight:
            self.Liquidate(symbol)
    
    for symbol, weight in self.weight.items():
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, weight)
    
    self.weight.clear()
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
