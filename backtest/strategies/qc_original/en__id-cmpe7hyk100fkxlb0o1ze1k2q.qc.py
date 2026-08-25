# Original QuantConnect / library Python
# locale=en slug="员工情绪与股票回报策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List
import statsmodels.api as sm
import numpy as np
# endregion

class EmployeeSentimentandStockReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2007, 5, 1) # BIL inception date
    self.SetCash(100000)

    self.leverage:int = 5

    self.risk_aversion:float = 3.
    self.allocation_limits:List[float] = [-0.5, 1.5]

    self.tickers:List[str] = [
        'A', 'AA', 'AAPL', 'AXP', 'BA', 'BAC', 'CAT', 'CSCO', 'CVX', 'DD', 
        'DIS', 'GE', 'HD', 'HPQ', 'IBM', 'INTC', 'JNJ', 'KFT', 'KO', 'MRK',
        'MSFT', 'PFE', 'PG', 'TRV', 'UTX', 'VZ', 'XOM'] # MCD, WMT

    self.negative_scores:List[float] = [1., 2.]
    self.positive_scores:List[float] = [4., 5.]

    self.reviews_by_ticker:Dict[str, List[Tuple[datetime.date, float]]] = {}

    self.last_review_date:datetime.date = datetime(1,1,1).date()

    # import employee review data
    for ticker in self.tickers:
        csv_string_file:str = self.Download(f"data.quantpedia.com/backtesting_data/economic/indeed_review/{ticker}.csv")
        lines:List[str] = csv_string_file.split('\r\n')
        for line in lines[1:]: # skip header
            if line == '': continue

            line_split:List[str] = line.split(';')
            date:datetime.date = datetime.strptime(line_split[0], "%d.%m.%Y").date()
            score:float = float(line_split[1])

            # store date of the review with associated score
            if ticker not in self.reviews_by_ticker:
                self.reviews_by_ticker[ticker] = []
            
            self.reviews_by_ticker[ticker].append((date, score))
            
            # mark up last available review date
            if date > self.last_review_date:
                self.last_review_date = date

    # subscribe price data
    data:Equity = self.AddEquity("SPY", Resolution.Daily)
    data.SetLeverage(self.leverage)
    self.market:Symbol = data.Symbol

    data:Equity = self.AddEquity("BIL", Resolution.Daily)
    data.SetLeverage(self.leverage)
    self.t_bills:Symbol = data.Symbol

    # sentiment data
    self.m_period:int = 12
    self.sentiment_data:SentimentData = SentimentData(self.m_period)

    self.SetWarmUp(self.m_period * 30, Resolution.Daily)
                                                        
    self.recent_month:int = -1

def OnData(self, data: Slice) -> None:
    # market data are present in the algorithm
    if self.market not in data or not data[self.market]:
        return

    # monthly rebalance
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month

    last_month:datetime.datetime = self.Time.replace(day=1) - timedelta(days=1)
    
    employee_sentiment:float = 0.
    for ticker, reviews_list in self.reviews_by_ticker.items():
        n_positive_reviews:float = len([x for x in reviews_list if x[1] in self.positive_scores and x[0].month == last_month.month and x[0].year == last_month.year])
        n_negative_reviews:float = len([x for x in reviews_list if x[1] in self.negative_scores and x[0].month == last_month.month and x[0].year == last_month.year])
        firm_employee_sentiment:float = (n_positive_reviews - n_negative_reviews) / (n_positive_reviews + n_negative_reviews) if (n_positive_reviews + n_negative_reviews) != 0. else 0
        employee_sentiment += firm_employee_sentiment
    
    # update sentiment and market data
    employee_sentiment /= len(self.reviews_by_ticker)
    self.sentiment_data.update_data(data[self.market].Value, employee_sentiment)
    
    if self.IsWarmingUp: return

    # no more review data available
    if self.Time.date() > self.last_review_date:
        self.Liquidate()
        return

    if self.sentiment_data.is_ready():
        x:Tuple[np.ndarray, np.ndarray] = self.sentiment_data.get_regression_data()
        model = self.multiple_linear_regression(x[1][:-1], x[0][1:])
        forecast_return:float = model.predict([1, x[1][-1]])[0]
        forecast_variance:float = np.std(x[0]) ** 2 # * np.sqrt(12)
        w_t:float = (1. / self.risk_aversion) * (forecast_return / forecast_variance)
        w_t = min(max(w_t, self.allocation_limits[0]), self.allocation_limits[1])
        t_bill_w:float = 1. - w_t

        self.SetHoldings(self.market, w_t)
        self.SetHoldings(self.t_bills, t_bill_w)

def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray):
    x:np.ndarray = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result

class SentimentData():
def __init__(self, period:int) -> None:
    self._period:int = period
    self._market_prices:RollingWindow = RollingWindow[float](period + 1)
    self._sentiment_index:RollingWindow = RollingWindow[float](period)

def is_ready(self) -> bool:
    return self._market_prices.IsReady and self._sentiment_index.IsReady

def update_data(self, price:float, sentiment_index_value:float) -> None:
    self._market_prices.Add(price)
    self._sentiment_index.Add(sentiment_index_value)

def get_regression_data(self) -> Tuple[np.ndarray, np.ndarray]:
    prices:np.ndarray = np.array(list(self._market_prices))
    returns:np.ndarray = prices[:-1] / prices[1:] - 1

    sentiment_index:np.ndarray = np.array(list(self._sentiment_index))
    return returns[::-1], sentiment_index[::-1]
