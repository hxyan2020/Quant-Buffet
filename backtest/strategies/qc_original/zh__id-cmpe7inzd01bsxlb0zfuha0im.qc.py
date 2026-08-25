# Original QuantConnect / library Python
# locale=zh slug="高分红日的价格压力"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List
import data_tools
import json
class PricePressureDuringTopDividendDays(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2012, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    self.symbol = self.AddEquity('VTI', Resolution.Daily).Symbol
    self.data:Dict[Symbol, SymbolData] = {}
    
    # dividend data
    self.dividend_data:Dict[Dict[datetime.date, DividendInfo]] = {}  # dict of dicts indexed by paydate date
    self.dividend_tickers:List[str] = []
    
    self.dividend_period:int = 272 # one year of trading days
    self.dividend_payments_yield_period:int = 252
    self.dividend_paids_yields:DividendPaitYield = data_tools.DividendPaidYield(self.dividend_period, self.dividend_payments_yield_period)
    
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
            self.dividend_data[payday][ticker] = data_tools.DividendInfo(ticker, ex_div_date, payday, record_date, dividend_value, ann_dividend_value, announcement_date)
            
            # store dividend info ticker universe
            self.dividend_tickers.append(ticker)
    
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.selection_flag = False
    self.active_universe = [] # selected stock universe
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    
def OnSecuritiesChanged(self, changes:SecurityChanges):
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update daily prices
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].update_close(stock.AdjustedPrice)
    
    # monthly selection  
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    selection:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Symbol.Value in self.dividend_tickers and x.Price > 5 \
                                    and x.MarketCap != 0 and ((x.SecurityReference.ExchangeId == "NYS") or (x.SecurityReference.ExchangeId == "NAS") or (x.SecurityReference.ExchangeId == "ASE"))]
    # select stocks, which have dividends data
    selected_symbols = []
    # warm up stock prices
    for stock in selection:
        symbol:Symbol = stock.Symbol
        
        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData()
        self.data[symbol].update_close(stock.AdjustedPrice)
        self.data[symbol].update_market_cap(stock.MarketCap)
        
        selected_symbols.append(symbol)
    self.active_universe = selected_symbols
            
    # return only stocks, which have ready close and market capitalization
    return selected_symbols
    
def OnData(self, data):
    yesterday:datetime.date = self.Time.date() - timedelta(days=1)
    
    # rebalance daily
    self.Liquidate()
    
    today_dividends_paid:int = 0
    
    # can't get today's data at 00:00
    if yesterday in self.dividend_data:
        payday_tickers:List[str] = list(self.dividend_data[yesterday].keys())
        
        dividends_paid:List[float] = [] # storing values of paid dividends for each stock, which has payday
        
        # iterate through currently selected universe
        for symbol in self.active_universe:
            ticker:str = symbol.Value
            # stock has payday today
            if ticker in payday_tickers and symbol in self.data:
                # get stock's dividend value
                dividend_value:float = self.dividend_data[yesterday][ticker].dividend_value
                
                # make sure, there are data for stock's dividend paid value calculation
                if not self.data[symbol].is_ready() or not dividend_value:
                    continue
                
                close:float = self.data[symbol].close
                market_cap:float = self.data[symbol].market_cap
                
                # calculate stock's dividend paid value
                stock_dividend_paid:float = (dividend_value / close) * market_cap
                # store stock's dividend paid value
                dividends_paid.append(stock_dividend_paid)
                
        today_dividends_paid:float = sum(dividends_paid)
        
    self.dividend_paids_yields.update_dividends_paid(today_dividends_paid)
    
    # check if one year of daily dividends paid data are ready
    if self.dividend_paids_yields.dividends_paid_ready():
        # update dividend payments yield 
        self.dividend_paids_yields.update_dividend_payments_yield()
        
        # check if dividend payments yield data are ready
        if self.dividend_paids_yields.dividend_payments_yield_ready():
            # check if today dividend payments yield is in top 50 yields for 252 trading days period
            trade_flag:bool = self.dividend_paids_yields.check_for_trade()
            
            if trade_flag:
                # go long on SPY, because today dividend payment yield is in top 50 yields for 252 trading days period
                self.SetHoldings(self.symbol, 1)
                
def Selection(self):
    self.selection_flag = True
