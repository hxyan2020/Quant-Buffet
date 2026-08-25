# Original QuantConnect / library Python
# locale=en slug="公告调整的行业相对反转因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
from pandas.tseries.offsets import BDay
import numpy as np
from typing import Dict, List
# endregion

class AnnouncementAdjustedIndustryRelativeReversalFactor(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.ticker_to_ignore:List[str] = ['GME']

    self.leverage:int = 3
    self.quantile:int = 5
    self.period:int = 31
    self.fundamental_count:int = 3000

    self.data:Dict[Symbol, float] = {}
    self.earnings_dates:Dict[datetime.date, List[str]] = {}
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []

    earnings_data:str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json:list[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date:datetime.date = (datetime.strptime(obj['date'], '%Y-%m-%d') + BDay(1)).date()

        if date not in self.earnings_dates:
            self.earnings_dates[date] = []
        
        for stock_data in obj['stocks']:
            ticker:str = stock_data['ticker']

            self.earnings_dates[date].append(ticker)

    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)
    
def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # store daily prices
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        if symbol in self.data:
            self.data[symbol].update_daily_return(self.Time, stock.AdjustedPrice)

    # selection on month start
    if not self.selection_flag:
        return Universe.Unchanged

    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Symbol.Value not in self.ticker_to_ignore \
                            and x.MarketCap != 0 and not np.isnan(x.AssetClassification.MorningstarSectorCode) and x.AssetClassification.MorningstarSectorCode != 0 and \
                            (x.SecurityReference.ExchangeId == 'NYS')]

    if len(selected) > self.fundamental_count:
        selected = sorted(selected, key=lambda x: x.MarketCap, reverse=True)[:self.fundamental_count]

    selected:Dict[str, Fundamental] = {x.Symbol.Value: x for x in selected}
    
    # sort stocks on industry numbers and price warmup
    grouped_industries:Dict[MorningstarIndustryGroupCode, List[Symbol]] = {}
    
    for ticker, stock in selected.items():
        symbol:Symbol = stock.Symbol

        industry_sector_code:int = stock.AssetClassification.MorningstarSectorCode

        if not industry_sector_code in grouped_industries:
            grouped_industries[industry_sector_code] = []
        grouped_industries[industry_sector_code].append(symbol)

        if symbol in self.data:
            continue
           
        self.data[symbol] = SymbolData()
        history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes:pd.Series = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].update_daily_return(time, close)

    irrx:Dict[Symbol, float] = {}
    
    # check earnings annoucement days
    for date, ticker_list in self.earnings_dates.items():
        if date >= self.Time.date() - relativedelta(months=1) and date = self.quantile:
        sorted_irrx:List[Symbol] = sorted(irrx, key=irrx.get)
        quantile:int = len(irrx) // self.quantile
        self.long = sorted_irrx[:quantile]
        self.short = sorted_irrx[-quantile:]

    return self.long + self.short

def OnData(self, data: Slice) -> None:
    # monthly rebalance
    if not self.selection_flag:
        return
    self.selection_flag = False

    # order execution
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)

    self.long.clear()
    self.short.clear()

def Selection(self) -> None:
    self.selection_flag = True

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))

class SymbolData():
def __init__(self) -> None:
    self._last_price:float|None = None
    self._daily_return:List[Tuple[datetime.date, float]] = []

def update_daily_return(self, time:datetime, price:float) -> None:
    if self._last_price is not None:
        daily_return:float = (price - self._last_price) / self._last_price
        self._daily_return.append((time.date(), daily_return))

    self._last_price = price

def reset_daily_returns(self) -> None:
    self._daily_return.clear()

def get_monthly_return(self) -> float:
    returns:List[float] = list(map(lambda x: x[1], self._daily_return))
    return sum(returns)

def get_target_date_return(self, date:datetime.date) -> float:
    #[i[0] for i in self._daily_return]:
    if date in list(map(lambda x: x[0], self._daily_return)):
        for i in range(len(self._daily_return) - 1):
            current_date, _ = self._daily_return[i]
            if current_date == date:
                return self._daily_return[i-1][1] + self._daily_return[i][1] + self._daily_return[i+1][1] 
    else:
        return sys.float_info.min

def is_ready(self) -> bool:
    return self._last_price is not None and len(self._daily_return) != 0
