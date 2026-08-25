# Original QuantConnect / library Python
# locale=zh slug="财报公布前公告漂移"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from collections import deque
from pandas.tseries.offsets import BDay
from typing import Dict, List, Deque, Set
class PreEarningsAnnouncementDrift(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.leverage:int = 5
    self.quarter_period:int = 8
    self.ear_period:int = 30
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # Daily price data.
    self.data:Dict[Symbol, Deque[DateTime, float]] = {}
    
    # Quarterly ear data.
    self.ear_data:Dict[Symbol, Deque[float]] = {}
    
    # Import earnigns data.
    self.earnings_data:Dict[DateTime, List[str]] = {}
    
    # Available symbols from earning_dates.csv.
    self.symbols:Set = set()
    
    self.first_date:datetime.date|None = None
    earnings_data:str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json:list[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date:datetime.date = datetime.strptime(obj['date'], "%Y-%m-%d").date()
        self.earnings_data[date] = []
        
        if not self.first_date: self.first_date = date
        for stock_data in obj['stocks']:
            ticker:str = stock_data['ticker']
            self.earnings_data[date].append(ticker)
            self.symbols.add(ticker)
            
    # EAR history for previous quarter used for statistics. 
    self.ear_previous_quarter:List[float] = []
    self.ear_actual_quarter:List[float] = []
    
    # Equally weighted brackets for traded symbols. - 10 symbols long , 10 for short, 5 days of holding.
    self.trade_manager:TradeManager = trade_manager.TradeManager(self, 10, 10, 5)
    
    self.month:int = 12
    self.selection_flag:bool = False
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
def OnSecuritiesChanged(self, changes:SecurityChanges):
    for security in changes.AddedSecurities:
        symbol:Symbol = security.Symbol
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
    for security in changes.RemovedSecurities:
        symbol:Symbol = security.Symbol
        if symbol in self.ear_data:
            del self.ear_data[symbol]
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].append((self.Time.date(), stock.AdjustedPrice))
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    selection:List[Fundamental] = [x.Symbol
        for x in sorted([x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price > 5 and x.Symbol.Value in self.symbols \
            and x.EarningReports.FileDate.HasValue and ((x.SecurityReference.ExchangeId == "NYS") or (x.SecurityReference.ExchangeId == "NAS") or (x.SecurityReference.ExchangeId == "ASE"))], key = lambda x: x.DollarVolume, reverse = True)]
    # Warmup price rolling windows.
    for symbol in selection:
        if symbol in self.data:
            continue
        
        self.data[symbol] = deque(maxlen = self.ear_period)
        history:DataFrame = self.History(symbol, self.ear_period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes:Series = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].append((time.date(),close))
    
    # Stocks with last month's earnings.
    last_month_date:DateTime = self.Time - timedelta(self.Time.day)
    filtered_selection = [x for x in fundamental if (x.EarningReports.FileDate.Value.year == last_month_date.year and x.EarningReports.FileDate.Value.month == last_month_date.month)]    
    
    for stock in filtered_selection:
        symbol:Symbol = stock.Symbol
        # Add symbol to ear data dict.
        if symbol not in self.ear_data:
            self.ear_data[symbol] = deque(maxlen = self.quarter_period)
        # Month of data is ready.
        if symbol in self.data and len(self.data[symbol]) == self.data[symbol].maxlen:
            
            earnings_day:DateTime = stock.EarningReports.FileDate.Value.date()
            day_before_earnings:DateTime = earnings_day - BDay(2)
            two_days_after_earnings:DateTime = earnings_day + BDay(2)
            day_range:List[DateTime, DateTime] = [day_before_earnings.date(), two_days_after_earnings.date()]
            
            # Store performance around earnings.
            ear_prices:List[float] = [x[1] for x in self.data[symbol] if x[0] >= day_range[0] and x[0]  None:
    date_to_lookup:DateTime = (self.Time + BDay(5)).date()
    
    # Liquidate opened symbols after five days.
    self.trade_manager.TryLiquidate()
    
    ear_avg:Dict[Symbol, float] = {}
    for symbol in self.data:
        # EAR data is ready.
        if symbol in self.ear_data and len(self.ear_data[symbol]) == self.ear_data[symbol].maxlen:
            if date_to_lookup in self.earnings_data:
                # Earnings is in next two day for the symbol.
                if symbol.Value in self.earnings_data[date_to_lookup]:
                    # Avg ear calc.
                    ear_values:List[float] = [x for x in self.ear_data[symbol]]
                    avg:float = np.mean(ear_values)
                    ear_avg[symbol] = avg
                    
                    # Store average return in this month's history.
                    self.ear_actual_quarter.append(avg)
        
    # Wait until we have history data for previous three months.
    if len(self.ear_previous_quarter) != 0:
        # Sort by EAR.
        ear_values:List[float] = self.ear_previous_quarter
        top_ear_quintile:float = np.percentile(ear_values, 90)
        bottom_ear_quintile:float = np.percentile(ear_values, 10)
        
        # Store symbol to set.
        short:List[Symbol] = [x[0] for x in ear_avg.items() if x[1] = top_ear_quintile]
        
        # Open new trades.
        for symbol in long:
            if symbol in data and data[symbol]:
                self.trade_manager.Add(symbol, True)
        
        for symbol in short:
            if symbol in data and data[symbol]:
                self.trade_manager.Add(symbol, False)
def Selection(self):
    self.selection_flag = True
    
    # Every three months.    
    if self.month % 3 == 0:
        # Save quarter history.
        self.ear_previous_quarter = [x for x in self.ear_actual_quarter]
        self.ear_actual_quarter.clear()
    self.month += 1
    if self.month > 12:
        self.month = 1
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
