# Original QuantConnect / library Python
# locale=en slug="未售出内部持股效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import pandas as pd
from io import StringIO
#endregion

class NotSoldInsiderHoldingsEffect(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.last_date = None
    
    self.insiders_by_symbol = {}    # storing list of insiders keyed by symbols for trading
    self.managed_queue = []
    
    self.holding_period = 12        # holding each stock for 12 months

    self.insiders_trading = {}      # list of insiders data keyed by date

    sp100_stocks = ['AAPL','MSFT','AMZN','FB','BRKB','GOOGL','GOOG','JPM','JNJ','V','PG','XOM','UNH','BAC','MA','T','DIS','INTC','HD','VZ','MRK','PFE','CVX','KO','CMCSA','CSCO','PEP','WFC','C','BA','ADBE','WMT','CRM','MCD','MDT','BMY','ABT','NVDA','NFLX','AMGN','PM','PYPL','TMO','COST','ABBV','ACN','HON','NKE','UNP','UTX','NEE','IBM','TXN','AVGO','LLY','ORCL','LIN','SBUX','AMT','LMT','GE','MMM','DHR','QCOM','CVS','MO','LOW','FIS','AXP','BKNG','UPS','GILD','CHTR','CAT','MDLZ','GS','USB','CI','ANTM','BDX','TJX','ADP','TFC','CME','SPGI','COP','INTU','ISRG','CB','SO','D','FISV','PNC','DUK','SYK','ZTS','MS','RTN','AGN','BLK']
    
    for symbol in sp100_stocks:
        data = self.AddEquity(symbol, Resolution.Daily)
        data.SetLeverage(10)
        data.SetFeeModel(CustomFeeModel())

        csv_string_file = self.Download(f'data.quantpedia.com/backtesting_data/economic/insiders_trading/{symbol}.csv')
        if csv_string_file == "":
            continue
        
        parser = lambda x: pd.datetime.strptime(x, "%Y-%m-%d")
        df = pd.read_csv(StringIO(csv_string_file), sep=';', parse_dates=['Tran.Date'], date_parser=parser)
        
        # this is only possible, because index consists of numbers in sequence
        for index in range(df.shape[0]):
            date = df.loc[index, 'Tran.Date'].date()
            
            data_dict = df.loc[index, ['Symbol', 'Filer Name', 'Relation', 'Action']].to_dict()
            
            if date not in self.insiders_trading:
                self.insiders_trading[date] = []
            self.insiders_trading[date].append(data_dict)
            
            if self.last_date is None or self.last_date
