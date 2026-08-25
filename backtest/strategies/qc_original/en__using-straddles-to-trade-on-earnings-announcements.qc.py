# Original QuantConnect / library Python
# locale=en slug="using-straddles-to-trade-on-earnings-announcements"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.tseries.offsets import BDay
from typing import Dict, List, Tuple
#endregion
class UsingStraddlesToTradeOnEarningsAnnouncements(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2018, 1, 1)
    self.SetCash(100_000) 
    
    self.earnings: Dict[datetime.date, str] = {}
    self.selected_for_trade: List[Tuple[Symbol, float]] = []
    
    # dj30 universe
    self.tickers: List[str] = [
        'UNH','GS','HD','AMGN','MSFT','CAT','MCD','V','BA','HON','CRM','MMM','DIS','JNJ','JPM','TRV','AXP','IBM','WMT','PG','NKE','AAPL','CVX','MRK','DOW','VZ','INTC','KO','WBA','CSCO'
    ]
    
    min_strike: int = -5
    max_strike: int = 5
    min_expiry: int = 4
    max_expiry: int = 30
    self.leverage: int = 10
    self.day_threshold: int = 5
    
    self.percentage_traded: float = 0.1  # only 10% of portfolio assets are used to perform this strategy
    
    for ticker in self.tickers:
        # add equity
        data: Security = self.AddEquity(ticker, Resolution.Minute)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage)
        
        # add options
        option: Option = self.AddOption(ticker, Resolution.Minute)
        option.SetFilter(min_strike, max_strike, min_expiry, max_expiry)
    
    # source: 'https://www.nasdaq.com/market-activity/earnings
    earnings_data: str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json: List[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date: datetime.date = datetime.strptime(obj['date'], "%Y-%m-%d").date()
        self.earnings[date] = []
        for stock_data in obj['stocks']:
            ticker: str = stock_data['ticker']
            self.earnings[date].append(ticker)
    # sort earnings by date    
    self.earnings: Dict[datetime, str] = {date: tickers for date, tickers in sorted(self.earnings.items(), key=lambda x: x[0])}
                
    self.earnings_date: Union[None, datetime.date] = None
                
    self.last_day: int = -1
    self.opened_equity_count: int = 0
def OnData(self, slice: Slice) -> None:
    # check once a day
    if self.Time.day == self.last_day:
        return
    self.last_day = self.Time.day
    
    invested: List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    # only equities are opened, options expired
    if self.opened_equity_count != 0 and len(invested) == self.opened_equity_count:
        self.opened_equity_count = 0
        # liquidate hedge
        self.Liquidate()
    
    if not self.Portfolio.Invested and len(self.selected_for_trade) == 0:
        current_date: datetime.date = self.Time.date()
        for date in self.earnings:
            # get closest earnings annoucement day, which is older than 3 days from current
            # if date > current_date and abs((date - current_date).days) > 3 and self.earnings_date != date:
            if date > (current_date + BDay(3)).date() and self.earnings_date != date:
                self.earnings_date = date
                break
        
        # return from function, if earnings_date wasn't selected
        if self.earnings_date is None:
            return
        
        for i in slice.OptionChains:
            chains: OptionChains = i.Value
            # get ticker for current chain
            ticker:str = chains.get_Symbol().get_Value()[1:]
            
            # check if current ticker is stored in self.earnings dictionary under self.earnings_date
            if ticker not in self.earnings[self.earnings_date]:
                continue
            
            calls: List[OptionChains] = list(filter(lambda x: x.Right == OptionRight.Call, chains))
            puts: List[OptionChains] = list(filter(lambda x: x.Right == OptionRight.Put, chains))
        
            if not calls or not puts:
                continue
            
            underlying_price: float = chains.Underlying.Price
            expiries: List[datetime.date] = [i.Expiry for i in puts]
            
            expiry_date: datetime.date = None
            for expiry in expiries:
                date: datetime.date = expiry.date()
                
                # pick expiry_date, if difference between expiration date and earnings annoucement date is less than 10 days
                if abs((date - self.earnings_date).days)  self.earnings_date and len(self.selected_for_trade) != 0:
        self.selected_for_trade.clear()
    
    # need to trade 3 days before earnings annoucement            
    if (self.Time + BDay(3)).date() == self.earnings_date and len(self.selected_for_trade) != 0:
        length: int = len(self.selected_for_trade)
        
        for atm_call, atm_put, underlying_price in self.selected_for_trade:
            if (atm_call.Symbol in slice and slice[atm_call.Symbol] and atm_put.Symbol in slice and slice[atm_put.Symbol] and atm_put.UnderlyingSymbol in slice and slice[atm_put.UnderlyingSymbol]):
                options_q: float = int(((self.Portfolio.TotalPortfolioValue*self.percentage_traded) / length) / (underlying_price * 100))
                
                # buy at-the-money straddle
                self.Buy(atm_call.Symbol, options_q)
                self.Buy(atm_put.Symbol, options_q)
                
                self.SetHoldings(atm_put.UnderlyingSymbol, -self.percentage_traded / length)
            
                # increase number of opened equities
                self.opened_equity_count += 1
        
        # clear list after trade
        self.selected_for_trade.clear()
       
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
