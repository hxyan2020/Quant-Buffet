# Original QuantConnect / library Python
# locale=en slug="climate-policy-uncertainty-and-the-cross-section-of-stock-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import statsmodels.api as sm
import data_tools
# endregion

class ClimatePolicyUncertaintyAndTheCrossSectionOfStockReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5

    self.period:int = 21
    self.regression_period:int = 60
    self.max_missing_months:int = 2
    self.quantile:int = 10  

    self.weights:dict[Symbol, float] = {}    
    self.prices:dict[Symbol, RollingWindow] = {}

    self.exchanges:list[str] = ['NYS', 'NAS', 'ASE']

    self.cpu_index:Symbol = self.AddData(data_tools.CPUIndex, 'CPU_INDEX', Resolution.Daily).Symbol        
    self.fama_french:Symbol = self.AddData(data_tools.QuantpediaFamaFrench, 'fama_french_3_factor_monthly', Resolution.Daily).Symbol
    
    self.market_symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.prev_market_price:float = None

    self.regression_data:RegressionData = data_tools.RegressionData(self.regression_period)        

    self.coarse_count:int = 1000
    self.recent_month:int = -1
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)

def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse):
    if not self.selection_flag:
        return Universe.Unchanged

    if self.coarse_count = 2 and x.Price = 2 and x.Price = 5000000 and x.SecurityReference.ExchangeId in self.exchanges]

    if len(fine) > self.coarse_count:
        sorted_by_market_cap:list = sorted(fine, key = lambda x: x.MarketCap, reverse=True)
        fine:list = sorted_by_market_cap[:self.coarse_count]

    cpu_beta:dict = {}
    regression_x:list = self.regression_data.regression_x()

    for stock in fine:
        symbol:Symbol = stock.Symbol

        prices:np.array = np.array([x for x in self.prices[symbol]])
        regression_y:np.array = (prices[:-1] / prices[1:]) - 1

        regression_model = self.MultipleLinearRegression(regression_x, regression_y)
        cpu_beta_value:float = regression_model.params[1]
        cpu_beta[stock] = cpu_beta_value
    
    # make sure there are enough stocks for selection
    if len(cpu_beta)
