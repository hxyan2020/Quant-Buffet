# Original QuantConnect / library Python
# locale=zh slug="使用五因子法玛-弗伦奇阿尔法的美国行业轮动策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import QuantpediaFamaFrench, CustomFeeModel, FamaFrenchData, \
MultipleLinearRegression, SymbolData
class USSectorRotationFiveFactorFamaFrenchAlphas(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.leverage:int = 10
    self.period:int = 37
    self.total_factor_num:int = 5
    self.max_missing_days:int = 5
    self.min_prices:int = 15
    self.min_daily_perfs:int = 15
    self.recent_month:int = -1
    self.data:dict[Symbol, SymbolData] = {}
    self.long:list[Symbol] = []
    self.fama_french:Symbol = self.AddData(QuantpediaFamaFrench, 'fama_french_5_factor', Resolution.Daily).Symbol
    self.ff_factor_names:list[str] = ['market', 'size', 'value', 'profitability', 'investment']
    self.ff_data:dict[str, FamaFrenchData] = { ff_factor_name: FamaFrenchData(self.period) for ff_factor_name in self.ff_factor_names }
    
    # self.symbols = []
    self.tickers = [
        "VNQ",  # Vanguard Real Estate Index Fund
        "XLK",  # Technology Select Sector SPDR Fund
        "XLE",  # Energy Select Sector SPDR Fund
        "XLV",  # Health Care Select Sector SPDR Fund
        "XLF",  # Financial Select Sector SPDR Fund
        "XLI",  # Industrials Select Sector SPDR Fund
        "XLB",  # Materials Select Sector SPDR Fund
        "XLY",  # Consumer Discretionary Select Sector SPDR Fund
        "XLP",  # Consumer Staples Select Sector SPDR Fund
        "XLU"   # Utilities Select Sector SPDR Fund
    ]
    for symbol in self.tickers:
        data:Security = self.AddEquity(symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage)
        
        self.data[data.Symbol] = SymbolData(self.period)
    
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.settings.daily_precise_end_time = False

def OnData(self, data):
    curr_date:datetime.date = self.Time.date()
    # store FF performance values
    if self.fama_french in data and data[self.fama_french]:
        for ff_factor_name, factor_data in self.ff_data.items():
            ff_factor_value:float = float(data[self.fama_french].GetProperty(ff_factor_name))
            factor_data.update_daily_perfs(ff_factor_value / 100.)
    # store etf prices
    for symbol, symbol_data in self.data.items():
        if symbol in data and data[symbol]:
            price:float = data[symbol].Value
            symbol_data.update_prices(price)
    
    # monthly rebalance
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    if self.securities[self.fama_french].get_last_data() and self.time.date() > QuantpediaFamaFrench.get_last_update_date()[self.fama_french]:
        self.liquidate()
        return
    # check FF data presence
    for ff_factor_name, ff_factor_data in self.ff_data.items():
            
        if ff_factor_data.daily_perfs_ready(self.min_daily_perfs):
            ff_factor_data.update_monthly_perfs()
        ff_factor_data.reset_daily_pefs()
    # regression model
    regression_x:list[list[float]] = [factor_data.get_regression_data(self.period - 1) for _, factor_data in self.ff_data.items() \
        if factor_data.monthly_perfs_ready()]
    for symbol, symbol_data in self.data.items():
        if symbol_data.prices_ready(self.min_prices):
            symbol_data.update_monthly_perfs()
        if symbol_data.monthly_perfs_ready() and len(regression_x) == self.total_factor_num:
            monthly_perfs:list[float] = symbol_data.get_regression_data(self.period - 1)
            regression_model = MultipleLinearRegression(regression_x, monthly_perfs)
            ff5_alpha:float = regression_model.params[0]
            symbol_data.update_ff5_alpha(ff5_alpha)
            if symbol_data.ff5_alpha_ready() and symbol_data.are_all_ff5_alpha_positive():
                self.long.append(symbol)
        else:
            # make sure ff5_alpha are consecutive
            symbol_data.reset_ff5_alpha()
        symbol_data.reset_daily_pefs()
    
    # trade execution
    long_length:int = len(self.long)
    stocks_invested:list[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in stocks_invested:
        if symbol not in self.long:
            self.Liquidate(symbol)
    for symbol in self.long:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, 1 / long_length)
    
    self.long.clear()
