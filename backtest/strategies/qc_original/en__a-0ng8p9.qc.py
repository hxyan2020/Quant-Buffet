# Original QuantConnect / library Python
# locale=en slug="a股自信因素策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import statsmodels.api as sm
import data_tools
# endregion

class OverconfidenceFactorInChina(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2009, 1, 1)
    self.SetCash(100000)

    self.tickers:list[str] = [
        '0001', '0002', '0004', '0006', '0011', '0012', '0016', '0017',
        '0019', '0020', '0027', '0066', '0083', '0101', '0135', '0144', '0151',
        '0175', '0241', '0267', '0268', '0270', '0288', '0291', '0316', '0322',
        '0384', '0388', '0489', '0586', '0656', '0669', '0688', '0700', '0762',
        '0788', '0836', '0868', '0881', '0883', '0916', '0960', '0968', '0981',
        '0992', '1038', '1044', '1093', '1099',

        # data error: '0003'

        # '1109', '1113', '1177', '1193',
        # '1299', '1308', '1359', '1378', '1810', '1876', '1913', '1928', '1929',
        # '1972', '1997', '2007', '2020', '2066', '2269', '2313', '2319', '2328',
        # '2331', '2382', '2388', '2638', '2688', '3311', '3323', '3690', '3692',
        # '3799', '3800', '6098', '6823', '6862'
    ]

    self.min_volumes:int = 15           # need atleast n daily volumes for one month
    self.regression_period:int = 12     # need m monthly data
    self.quantile:int = 2
    self.leverage:int = 5
    self.data:dict[Symbol, data_tools.SymbolData] = {}

    # NOTE: Download method is rate-limited to 100 calls (https://github.com/QuantConnect/Documentation/issues/345)
    for ticker in self.tickers:
        security = self.AddData(data_tools.ChineseStock, ticker, Resolution.Daily)
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

        stock_symbol:Symbol = security.Symbol
        income_statement_symbol:Symbol = self.AddData(data_tools.IncomeStatement, ticker, Resolution.Daily).Symbol
        self.data[stock_symbol] = data_tools.SymbolData(income_statement_symbol, self.regression_period)

    self.recent_month:int = -1

def OnData(self, data):
    curr_date:datetime.date = self.Time.date()

    # daily data update
    # price and average shares are retrieved and stored separately, because they might not come at the same time
    for symbol, symbol_obj in self.data.items():
        if symbol in data and data[symbol]:
            if data[symbol].GetProperty('volume') != 0:
                volume:float = data[symbol].GetProperty('volume')
                
                symbol_obj.update_daily_volumes(volume)
            
            if data[symbol].Value != 0: 
                price:float = data[symbol].Value

                symbol_obj.update_last_price(price)

        income_statement_symbol:Symbol = symbol_obj.income_statement_symbol
        if income_statement_symbol in data and data[income_statement_symbol] and \
            data[income_statement_symbol].GetProperty('weightedAverageShsOutDil') != 0:

            average_shares:float = data[income_statement_symbol].GetProperty('weightedAverageShsOutDil')

            symbol_obj.update_last_average_shares(average_shares)

    # rebalance monthly
    if self.recent_month == curr_date.month:
        return
    self.recent_month = curr_date.month

    filtered_symbols:list[Symbol] = []
    regression_x:np.array = np.zeros(self.regression_period)

    for symbol, symbol_obj in self.data.items():
        if symbol_obj.are_daily_volumes_ready(self.min_volumes):
            symbol_obj.update_monthly_volumes()
            symbol_obj.reset_daily_volumes()
        else:
            # data have to be consecutive
            symbol_obj.reset_volumes()

        if symbol_obj.are_regression_data_ready() and symbol_obj.are_data_for_market_cap_ready():
            regression_x += np.array(symbol_obj.get_monthly_volumes())

            filtered_symbols.append(symbol)

    ATV_by_symbol:dict[Symbol, float] = {}
    market_cap_by_symbol:dict[Symbol, float] = {}

    for symbol in filtered_symbols:
        market_cap:float = self.data[symbol].get_market_cap()
        regression_y:list[float] = self.data[symbol].get_monthly_volumes()

        regression_model = self.MultipleLinearRegression(regression_x, regression_y)

        ATV:float = np.mean(regression_model.resid)
        ATV_by_symbol[symbol] = ATV
        market_cap_by_symbol[symbol] = market_cap

    # big and small cap will be sorted into halfs by ATV values and there has to be enough stocks
    if len(ATV_by_symbol)
