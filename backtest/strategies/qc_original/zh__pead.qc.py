# Original QuantConnect / library Python
# locale=zh slug="宏观新闻对收益公告后漂移（pead）策略的影响"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from collections import deque
from typing import List, Dict, Deque
from numpy import isnan
#endregion
class ImpactofMacroNewsonPEADStrategy(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']	
    self.period: int = 13
    self.quantile: int = 5
    self.leverage: int = 5
    self.threshold: int = 3
    self.min_share_price: int = 5
    # EPS quarterly data.
    self.eps_data: Dict[Symbol, Deque[List[float]]] = {} 
    self.long: List[Symbol] = []
    self.short: List[Symbol] = []
    
    symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    # Import macro dates.
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/economic/economic_announcements.csv')
    dates: List[str] = csv_string_file.split('\r\n')
    self.macro_dates: List[datetime.date] = [datetime.strptime(x, "%Y-%m-%d").date() for x in dates]
    self.fundamental_count: int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.selection_flag: int = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(symbol), self.TimeRules.AfterMarketOpen(symbol), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged

    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.Market == 'usa' 
        and x.Price > self.min_share_price 
        and x.SecurityReference.ExchangeId in self.exchange_codes
        and not isnan(x.EarningReports.BasicEPS.ThreeMonths) and (x.EarningReports.BasicEPS.ThreeMonths != 0)
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    # Stocks with last month's earnings.
    last_month_date: datetime.date = self.Time - timedelta(self.Time.day)
    filtered_fundamental: List[Fundamental] = [x for x in selected if (x.EarningReports.FileDate.ThreeMonths.year == last_month_date.year and x.EarningReports.FileDate.ThreeMonths.month == last_month_date.month)]
    
    # earnings surprises data for stocks
    earnings_surprises: Dict[Symbol, List[float, datetime.date]] = {}
    
    for stock in filtered_fundamental:
        symbol: Symbol = stock.Symbol
        
        # Store eps data.
        if symbol not in self.eps_data:
            self.eps_data[symbol] = deque(maxlen = self.period)
        self.eps_data[symbol].append([stock.EarningReports.FileDate.ThreeMonths.date(), stock.EarningReports.BasicEPS.ThreeMonths])
        if len(self.eps_data[symbol]) == self.eps_data[symbol].maxlen:
            year_range: range = range(self.Time.year - 3, self.Time.year)
            month_range: List[datetime.date] = [last_month_date.month - 1, last_month_date.month, last_month_date.month + 1]
            
            # Earnings 3 years back.
            seasonal_eps_data: List[List[datetime.date, float]] = [
                x for x in self.eps_data[symbol] 
                if x[0].month in month_range
                and x[0].year in year_range]
            if len(seasonal_eps_data) != self.threshold:
                continue
            recent_eps_data: List[datetime.date, float] = self.eps_data[symbol][-1]
            
            # Make sure we have a consecutive seasonal data. Same months with one year difference.
            year_diff: np.ndarray = np.diff([x[0].year for x in seasonal_eps_data])
            if all(x == 1 for x in year_diff):
                seasonal_eps: List[float] = [x[1] for x in seasonal_eps_data]
                diff_values: np.ndarray = np.diff(seasonal_eps)
                drift: float = np.average(diff_values)
                
                # earnings surprise calculation
                last_earnings: float = seasonal_eps[-1]
                expected_earnings: float = last_earnings + drift
                actual_earnings: float = recent_eps_data[1]
                # Store sue value with earnigns date
                earnings_surprise: float = actual_earnings - expected_earnings
                earnings_surprises[symbol] = [earnings_surprise, stock.EarningReports.FileDate.ThreeMonths.date()]
    
    # wait until earnings suprises are ready           
    if len(earnings_surprises)  self.macro_dates[-1]:
        return Universe.Unchanged
    # sort by earnings suprises.
    quantile: int = int(len(earnings_surprises) / self.quantile) 
    sorted_by_earnings_surprise: List[Symbol] = [x[0] for x in sorted(earnings_surprises.items(), key=lambda item: item[1][0])]
    
    # select top quintile and bottom quintile based on earnings suprise sort
    top_quintile: List[Symbol] = sorted_by_earnings_surprise[-quantile:]
    bottom_quintile: List[Symbol] = sorted_by_earnings_surprise[:quantile]
    
    # long stocks, which are in top quintile by earnings suprise sort and have non-macro date
    self.long = [x for x in top_quintile if earnings_surprises[x][1] not in self.macro_dates]
    # short stocks, which are in bottom quintile by earnings suprise sort and have non-macro date
    self.short = [x for x in bottom_quintile if earnings_surprises[x][1] not in self.macro_dates]
    
    return self.long + self.short
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
        
    # Trade execution.
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
