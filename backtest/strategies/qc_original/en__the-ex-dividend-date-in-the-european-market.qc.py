# Original QuantConnect / library Python
# locale=en slug="the-ex-dividend-date-in-the-european-market"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class TheExDividendDateInTheEuropeanMarket(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    tickers = []
    self.symbols = []
    self.dividends_data = {}
    
    self.invested_data = {}

    self.first_date = None
    # Data source: https://www.nasdaq.com/market-activity/dividends
    dividend_data:str = self.Download('data.quantpedia.com/backtesting_data/economic/dividend_dates.json')
    dividend_data_json:Dict[str] = json.loads(dividend_data)
        
    for obj in dividend_data_json:
        date:datetime.date = datetime.strptime(obj['date'], "%Y-%m-%d").date()
        
        self.dividends_data[date] = []
        
        for stock_data in obj['stocks']:
            if ' ' in stock_data['ticker']:
                continue
            ticker:str = stock_data['ticker']
            if ticker not in tickers:
                security = self.AddEquity(ticker, Resolution.Daily)
                security.SetFeeModel(CustomFeeModel())
                security.SetLeverage(self.leverage)
                
                tickers.append(ticker)
                
                self.symbols.append(security.Symbol)
                
            self.dividends_data[date].append(ticker)
    self.long = []
    self.long_size = 80
def OnData(self, data):
    current_date = self.Time.date()
    date_to_lookup = (self.Time + timedelta(days=5)).date()
    if current_date in self.invested_data:
        self.LiquidateChosenSymbols(self.invested_data[current_date])
        del self.invested_data[current_date]
    # Open new trades.
    if date_to_lookup in self.dividends_data:
        for symbol in self.symbols:
            if symbol.Value in self.dividends_data[date_to_lookup]:
                if symbol in data and data[symbol]:
                    if self.Add(symbol):
                        if date_to_lookup not in self.invested_data:
                            self.invested_data[date_to_lookup] = []
                            
                        self.invested_data[date_to_lookup].append(symbol)

def Add(self, symbol):
    if len(self.long)
