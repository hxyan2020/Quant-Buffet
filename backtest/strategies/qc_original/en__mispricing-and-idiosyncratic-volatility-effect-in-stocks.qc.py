# Original QuantConnect / library Python
# locale=en slug="mispricing-and-idiosyncratic-volatility-effect-in-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import statsmodels.api as sm
import data_tools
#endregion
class MispricingAndIdiosyncraticVolatilityEffectInStocks(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2002, 1, 1)
    self.SetCash(100_000)
    
    self.tickers_to_ignore: List[str] = ['ADC']
    self.data: Dict[Symbol, data_tools.SymbolData] = {}
    self.weights: Dict[str, float] = {}
    
    self.period: int = 21 # need n daily prices
    self.leverage: int = 10
    self.quantile: int = 4
    self.max_missing_days = 5
    
    self.fama_french_data: Dict[str, RollingWindow] = {
        'market': RollingWindow[float](self.period - 1),
        'size': RollingWindow[float](self.period - 1),
        'value': RollingWindow[float](self.period - 1)
    }
    
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.fama_french_symbol: Symbol = self.AddData(data_tools.QuantpediaFamaFrench, 'fama_french_3_factor', Resolution.Daily).Symbol
    self.misp_score_symbol: Symbol = self.AddData(data_tools.QuantpediaMispScore, 'MISP_SCORE', Resolution.Daily).Symbol
    
    self.selection_flag: boll = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.BeforeMarketClose(market, 0), self.Selection)
    
    # warm up fama french values for idiosyncratic volatility
    self.SetWarmup(self.period, Resolution.Daily)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update prices on daily basis
    for stock in fundamental:
        ticker: str = stock.Symbol.Value
        
        if ticker in self.data:
            self.data[ticker].update_closes(stock.AdjustedPrice)
    
    custom_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.LastDateHandler.get_last_update_date()
    # custom data is still comming in
    if any(self.Securities[x].GetLastData() and self.Time.date() > custom_data_last_update_date[x] for x in [self.fama_french_symbol, self.misp_score_symbol]):
        return Universe.Unchanged
    # rebalance monthly, when fama french data are ready
    if not self.selection_flag or not self.fama_french_data['market'].IsReady or \
        not self.fama_french_data['size'] or not self.fama_french_data['value'].IsReady:
        return Universe.Unchanged
    
    # filter stocks which hase misp score value
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.MarketCap != 0 
        and x.Symbol.Value in self.data
        and x.Symbol.Value not in self.tickers_to_ignore
    ]
    misp_score: Dict[Fundamental, float] = {}
    idiosyncratic_vol: Dict[Fundamental, float] = {}
    
    # prepare regression x for idiosyncratic volatility
    regression_x: List[List[float]] = [
        [x for x in self.fama_french_data['market']],
        [x for x in self.fama_french_data['size']],
        [x for x in self.fama_french_data['value']],
    ]
    
    for stock in selected:
        ticker: str = stock.Symbol.Value
        
        if not self.data[ticker].is_ready():
            continue
        # calculate idiosyncratic volatility factor
        daily_returns: np.ndarray = self.data[ticker].daily_returns()
        regression_model = self.MultipleLinearRegression(regression_x, daily_returns)
        idiosyncratic_vol[stock] = np.std(regression_model.resid)
        misp_score[stock] = self.data[ticker].misp_score
        
    # make sure there are enough data for two quantile selections
    if len(idiosyncratic_vol)  None:
    # update fama french values on daily basis
    if slice.contains_key(self.fama_french_symbol) and slice[self.fama_french_symbol]:
        self.fama_french_data['value'].Add(slice[self.fama_french_symbol].Value)
        self.fama_french_data['size'].Add(slice[self.fama_french_symbol].Size)
        self.fama_french_data['market'].Add(slice[self.fama_french_symbol].Market)
    
    # update misp_score values   
    if slice.contains_key(self.misp_score_symbol) and slice[self.misp_score_symbol]:
        tickers = [x for x in slice[self.misp_score_symbol].get_Item('tickers')]
        
        for ticker in tickers:
            if ticker not in self.data:
                self.data[ticker] = data_tools.SymbolData(self.period)
                
            misp_score_value = slice[self.misp_score_symbol].get_Item(ticker)
            self.data[ticker].update_misp_score(misp_score_value)
    
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weights.items() if slice.contains_key(symbol) and slice[symbol]]
    self.SetHoldings(portfolio, True)
    self.weights.clear()
    
def MultipleLinearRegression(self, x: np.ndarray, y: np.ndarray):
    x: np.ndarray = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
    
def Selection(self) -> None:
    self.selection_flag = True
