# Original QuantConnect / library Python
# locale=zh slug="股息股票与利率的上升或下降"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
#endregion
class DividendStocksAndRisingOrFallingInterestRates(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    self.symbol:Symbol = self.AddData(FEDFUNDS, 'FEDFUNDS', Resolution.Daily).Symbol
    self.period:int = 12
    self.quantile:int = 10
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.fed_fund_rate:RollingWindow = RollingWindow[float](self.period)
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.recent_month:int = -1
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
            
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    # FED rate data is still comming in
    last_update_date:datetime.date = FEDFUNDS.get_last_update_date()
    if last_update_date = self.min_share_price and \
            not np.isnan(x.EarningReports.DividendPerShare.ThreeMonths) and x.EarningReports.DividendPerShare.ThreeMonths != 0
        ]
        
        if len(selected) > self.fundamental_count:
            selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        dividend_yield:Dict[Symbol, float] = {x.Symbol : x.EarningReports.DividendPerShare.ThreeMonths for x in selected}
        if len(dividend_yield) >= self.quantile:
            # Stocks are sorted descending by dividend yield
            sorted_by_dividend_yield:List[Symbol] = sorted(dividend_yield, key=dividend_yield.get, reverse=True)
            quantile:int = len(sorted_by_dividend_yield) // self.quantile
            high_dividend_stocks:List[Symbol] = sorted_by_dividend_yield[:quantile] # top decile
            low_dividend_stocks:List[Symbol] = sorted_by_dividend_yield[-quantile:] # bottom decile
            
            # identify rising or declining interest rate periods, based on the one-year change in the fed funds rate 
            interest_rate_rising:bool = self.fed_fund_rate[0] > self.fed_fund_rate[self.period-1]
            
            if interest_rate_rising: # rising period
                self.long = low_dividend_stocks
                self.short = high_dividend_stocks
            else: # declining period
                self.long = high_dividend_stocks
                self.short = low_dividend_stocks
    
    return self.long + self.short    
def OnData(self, data: Slice) -> None:
    # Add fed-rates to object in self.data
    if self.symbol in data and data[self.symbol]:
        price:float = data[self.symbol].Value
        self.fed_fund_rate.Add(price)
        
        self.selection_flag = True
        return
    
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution
    count_long:int = len(self.long)
    count_short:int = len(self.short)
    
    self.Liquidate()
    
    if not (self.Time.year == 2008 and self.Time.month == 6):
        for symbol in self.long:
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, 1 / count_long)
            
        for symbol in self.short:
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, - 1 / count_short)
    self.short.clear()
    self.long.clear()
        
# Source: https://fred.stlouisfed.org/series/T10Y3M
class FEDFUNDS(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource('data.quantpedia.com/backtesting_data/economic/FEDFUNDS.csv', SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
_last_update_date:datetime.date = datetime(1,1,1).date()
@staticmethod
def get_last_update_date() -> datetime.date:
   return FEDFUNDS._last_update_date
def Reader(self, config, line, date, isLiveMode):
    data = FEDFUNDS()
    data.Symbol = config.Symbol
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    # Parse the CSV file's columns into the custom data class
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    if split[1] != '.':
        data.Value = float(split[1])
    if data.Time.date() > FEDFUNDS._last_update_date:
        FEDFUNDS._last_update_date = data.Time.date()
    
    return data
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
