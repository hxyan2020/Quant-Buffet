# Original QuantConnect / library Python
# locale=en slug="absolute-delta-beta-strategy-in-chinese-equities"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import QuantpediaCSI300, CustomFeeModel, SymbolData, MultipleLinearRegression
# endregion

class AbsoluteDeltaBetaStrategyInChineseEquities(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)   # CSI 300 data starts in 2005
    self.SetCash(100000)

    self.leverage:int = 10
    self.quantile:int = 10

    self.min_prices:int = 15

    self.weights:dict[Symbol, float] = {}
    self.data:dict[Symbol, SymbolData] = {}

    self.benchmark:Symbol = self.AddData(QuantpediaCSI300, 'CSI_300', Resolution.Daily).Symbol
    self.benchmark_data = SymbolData()

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.selection_flag = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.BeforeMarketClose(self.market, 0), self.Selection)

def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse):
    curr_date:datetime.date = self.Time.date()

    for stock in coarse:
        symbol:Symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].update_price_with_date(stock.AdjustedPrice, curr_date)
    
    # monthly rebalance
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected_symbols = [x.Symbol for x in coarse if x.HasFundamentalData]
    
    return selected_symbols

def FineSelectionFunction(self, fine):
    csi_rets_with_dates:list[datetime.date, float]|None = self.benchmark_data.get_rets_with_dates() \
        if self.benchmark_data.is_ready(self.min_prices) else None

    if csi_rets_with_dates == None:
        return Universe.Unchanged

    fine = list(filter(lambda stock: stock.MarketCap != 0 and stock.CompanyReference.BusinessCountryID == 'CHN', fine))
    
    # Exclude 30% of lowest stocks by MarketCap
    sorted_by_market_cap = sorted(fine, key = lambda x: x.MarketCap)
    fine = sorted_by_market_cap[int(len(sorted_by_market_cap) * 0.3):]

    ADB:dict[Symbol, float] = {}

    for stock in fine:
        symbol:Symbol = stock.Symbol
        market_cap:float = stock.MarketCap

        if symbol not in self.data:
            self.data[symbol] = SymbolData()

        if self.data[symbol].is_ready(self.min_prices):
            stock_rets_with_dates:list[datetime.date, float] = self.data[symbol].get_rets_with_dates()
            rising_x, rising_y, declining_x, declining_y = ([] for i in range(4))

            for (csi_ret, csi_date), (stock_ret, stock_date) in zip(csi_rets_with_dates, stock_rets_with_dates):
                if csi_date == stock_date:
                    if stock_ret > 0:
                        rising_x.append(csi_ret)
                        rising_y.append(stock_ret)
                    else:
                        declining_x.append(csi_ret)
                        declining_y.append(stock_ret)

            if len(rising_x) != 0 and len(declining_x) != 0:
                regression_model = MultipleLinearRegression(rising_x, rising_y)
                rising_market_beta:float = regression_model.params[0]

                regression_model = MultipleLinearRegression(declining_x, declining_y)
                declining_market_beta:float = regression_model.params[0]

                ADB[stock] = abs(rising_market_beta - declining_market_beta)
        
        self.data[symbol].reset_data()

    if len(ADB)
