# Original QuantConnect / library Python
# locale=zh slug="在股息支付日进行交易"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from datetime import datetime
from pandas.tseries.offsets import BDay
from typing import Dict, List
import json
#endregion
class TradingDividendPaydate(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2012, 9, 18)
    self.SetCash(100000)    
    symbol:Symbol = self.AddEquity('SPY', Resolution.Minute).Symbol
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    # Store drip tickers.
    # Source: http://www.dripdatabase.com/DRIP_Directory_AtoZ.aspx
    csv_string_file:str = self.Download('data.quantpedia.com/backtesting_data/economic/drip_tickers.csv')
    lines:str = csv_string_file.split('\r\n')
    self.drip_tickers:List[str] = [x for x in lines[1:]]
    
    # dividend data
    self.dividend_data:Dict = {}  # dict of dicts indexed by paydate date
    
    # Data source: https://www.nasdaq.com/market-activity/dividends
    dividend_data:str = self.Download('data.quantpedia.com/backtesting_data/economic/dividend_dates.json')
    dividend_data_json:Dict[str] = json.loads(dividend_data)
        
    for obj in dividend_data_json:
        ex_div_date:datetime.date = datetime.strptime(obj['date'], "%Y-%m-%d").date()
        
        for stock_data in obj['stocks']:
            ticker:str = stock_data['ticker']
            payday:datetime.date = datetime.strptime(stock_data['PayDate'], '%m/%d/%Y').date()
            if payday not in self.dividend_data:
                self.dividend_data[payday] = {}    
            record_date:Union[datetime.date, None] = datetime.strptime(stock_data['RecordDate'], '%m/%d/%Y').date() if 'RecordDate' in stock_data else None
            dividend_value:float = stock_data['Div']
            ann_dividend_value:float = stock_data['AnnDiv']
            announcement_date:Union[datetime.date, None] = datetime.strptime(stock_data['AnnounceDate'], '%m/%d/%Y').date() if 'AnnounceDate' in stock_data else None
            # store ticker dividend info to current ex-div date
            self.dividend_data[payday][ticker] = DividendInfo(ticker, ex_div_date, payday, record_date, dividend_value, ann_dividend_value, announcement_date)
    self.active_universe:List[Symbol] = []   # selected stock universe
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.Schedule.On(self.DateRules.MonthEnd(symbol), self.TimeRules.AfterMarketOpen(symbol), self.Selection)
    self.Schedule.On(self.DateRules.EveryDay(symbol), self.TimeRules.BeforeMarketClose(symbol, 16), self.Rebalance)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    self.selection_flag = False
    selection:List[Fundamental] = [x for x in fundamental if x.Symbol.Value in self.drip_tickers and x.MarketCap != 0 and x.SecurityReference.ExchangeId in self.exchange_codes]
    # sorting by market cap
    sorted_by_market_cap = sorted(selection, key = lambda x: x.MarketCap, reverse = True)
    half = int(len(sorted_by_market_cap) / 2)
    
    # pick lower half
    self.active_universe = [x.Symbol for x in sorted_by_market_cap[-half:]]
    
    # pick upper half
    # self.active_universe = [x.Symbol for x in sorted_by_market_cap[:half]]
    
    return self.active_universe

def Rebalance(self) -> None:
    # close opened positions
    stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in stocks_invested:
        q_invested:int = self.Portfolio[symbol].Quantity
        self.MarketOnCloseOrder(symbol, -q_invested)
    day_to_check = (self.Time.date() + BDay(1)).date()
    # there are stocks with payday next business day
    if day_to_check in self.dividend_data:
        payday_tickers = list(self.dividend_data[day_to_check].keys())
        long = []
        for symbol in self.active_universe:
            if symbol.Value in payday_tickers:
                long.append(symbol) 
        
        if len(long) != 0:
            portfolio_value = self.Portfolio.MarginRemaining / len(long)
            for symbol in long:
                price = self.Securities[symbol].Price
                if price != 0:
                    q = portfolio_value / price
                    self.MarketOnCloseOrder(symbol, q)
def Selection(self) -> None:
    if self.Time.month % 3 == 0:
        self.selection_flag = True
# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
class DividendInfo():
def __init__(
        self, 
        ticker:str, 
        ex_div_date:datetime.date,
        payday:datetime.date, 
        record_date:Union[datetime.date, None],
        dividend_value:float,
        ann_dividend_value:float,
        announcement_date:datetime.date
    ):
    self.ticker:str = ticker
    self.ex_div_date:datetime.date = ex_div_date
    self.payday:datetime.date = payday
    self.record_date:Union[datetime.date, None] = record_date
    self.dividend_value:float = dividend_value
    self.ann_dividend_value:float = ann_dividend_value
    self.announcement_date:Union[datetime.date, None] = announcement_date
