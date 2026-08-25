# Original QuantConnect / library Python
# locale=en slug="conglomerates-post-earnings-announcement-drift"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from trade_manager import TradeManager
from collections import deque
from pandas.tseries.offsets import BDay
from dateutil.relativedelta import relativedelta
class ConglomeratesPostEarningsAnnouncementDrift(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.period:int = 13
    self.leverage:int = 5
    self.seasonal_eps_count:int = 3
    self.eps:Dict[Symbol, List[datetime.date, float]] = {}
    self.earnings_data:Dict[datetime.date, Dict[str, float]] = {}
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol        
    
    self.long:List[Symbol] = []
    
    # equally weighted brackets for traded symbols
    self.trade_manager:TradeManager = TradeManager(self, 20, 20, 58)
    earnings_data:str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json:list[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date:datetime.date = datetime.strptime(obj['date'], '%Y-%m-%d').date()
        self.earnings_data[date] = {}
        
        for stock_data in obj['stocks']:
            ticker:str = stock_data['ticker']
            if stock_data['eps'] != '':
                self.earnings_data[date][ticker] = float(stock_data['eps'])
    self.UniverseSettings.Resolution = Resolution.Daily
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.AddUniverse(self.FundamentalSelectionFunction)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # stocks with yesterday's earnings
    yesterday:datetime.date = (self.Time - BDay(1)).date()
    if yesterday not in self.earnings_data:
        return Universe.Unchanged
    tickers_with_yesterday_earnings:List[str] = list(self.earnings_data[yesterday].keys())
    
    # stocks with yesterday's earnings
    selected:List[Fundamental] = [x for x in fundamental if x.AssetClassification.MorningstarIndustryGroupCode == MorningstarIndustryGroupCode.Conglomerates and \
        x.Symbol.Value in tickers_with_yesterday_earnings] 
    for stock in selected:
        symbol:Symbol = stock.Symbol
        ticker:str = symbol.Value
        # store eps data
        if symbol not in self.eps:
            self.eps[symbol] = deque(maxlen=self.period)
        data:List[datetime.date, float] = [yesterday, self.earnings_data[yesterday][ticker]]
        self.eps[symbol].append(data)
        if len(self.eps[symbol]) == self.eps[symbol].maxlen:
            recent_eps_data:List[datetime.date, float] = self.eps[symbol][-1]
            
            year_range:range = range(self.Time.year - 3, self.Time.year)
            
            last_month_date:datetime.date = recent_eps_data[0] - relativedelta(months=1)
            next_month_date:datetime.date = recent_eps_data[0] + relativedelta(months=1)
            month_range:List[int] = [last_month_date.month, recent_eps_data[0].month, next_month_date.month]
            # earnings with todays month number 4 years back
            seasonal_eps_data:List[List[datetime.date, float]] = [x for x in self.eps[symbol] if \
                x[0].month in month_range and x[0].year in year_range]
            if len(seasonal_eps_data) != self.seasonal_eps_count: continue
            
            # make sure we have a consecutive seasonal data
            # same months with one year difference
            year_diff:np.array = np.diff([x[0].year for x in seasonal_eps_data])
            if all(x == 1 for x in year_diff):
                seasonal_eps:List[float] = [x[1] for x in seasonal_eps_data]
                diff_values:np.array = np.diff(seasonal_eps)
                drift:float = np.average(diff_values)
                
                # SUE calculation
                last_earnings:float = seasonal_eps[-1]
                expected_earnings:float = last_earnings + drift
                actual_earnings:float = recent_eps_data[1]
            
                # earning beat
                if actual_earnings > expected_earnings:
                    self.long.append(symbol)
    return self.long
def OnData(self, data):
    self.trade_manager.TryLiquidate()
    
    # Open new trades.
    for symbol in self.long:
        self.trade_manager.Add(symbol, True)
    
    self.long.clear()
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
