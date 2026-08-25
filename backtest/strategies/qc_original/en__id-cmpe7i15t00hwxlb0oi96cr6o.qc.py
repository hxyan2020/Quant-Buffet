# Original QuantConnect / library Python
# locale=en slug="中国股市中的分行业贝塔策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
from pandas.core.frame import DataFrame
from typing import Dict, List
import statsmodels.api as sm
# endregion
class IndustryRelativeStockBetainChineseEquities(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.weight:dict[Symbol, float] = {}
    self.leverage:float = 10
    self.industry_beta:Dict[str, RollingWindow] = {}
    self.stock_beta:Dict[Symbol, float] = {}
    
    self.period:int = 15
    self.rolling_period:int = 2
    self.traded_percentage:float = .2

    self.market:Symbol = self.AddEquity("FXI", Resolution.Daily).Symbol
    
    self.quantile:int = 10
    self.count:int = 100
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)
    
def OnSecuritiesChanged(self, changes:SecurityChanges):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    # monthly selection
    if not self.selection_flag:
        return Universe.Unchanged
    # self.selection_flag = False
    selected:List[Symbol] = [x.Symbol
        for x in sorted([x for x in coarse if x.HasFundamentalData], 
        key = lambda x: x.DollarVolume, reverse = True)]
    return selected
def FineSelectionFunction(self, fine: List[FineFundamental]) -> List[Symbol]:
    # filter chinese stocks by BusinessCountryID 
    fine:List[FineFundamental] = [x for x in fine if x.AssetClassification.MorningstarIndustryGroupCode != 0 and x.MarketCap != 0 and x.CompanyReference.BusinessCountryID == 'CHN']
    fine = sorted(fine, key=lambda x: x.MarketCap, reverse=True)[:self.count]
    # call history on fine and market
    history:DataFrame = self.History(list(map(lambda x:x.Symbol,fine)) + [self.market], start=self.Time.date() - relativedelta(months=self.period), end=self.Time.date())['close'].unstack(level=0)
    history = history.groupby(pd.Grouper(freq='M')).last()
    
    # sort stocks on industry numbers
    grouped_industries:Dict[MorningstarIndustryGroupCode, List[Symbol]] = {}
    for stock in fine:
        symbol:Symbol = stock.Symbol
        
        industry_group_code:str = str(stock.AssetClassification.MorningstarIndustryGroupCode)
        if not industry_group_code in grouped_industries:
            grouped_industries[industry_group_code] = []
        grouped_industries[industry_group_code].append(symbol)
    if len(history) >= self.period and self.market in history.columns and not history[self.market].isnull().values.any():
        history = history.iloc[-self.period:]
        history.index = history.index.to_pydatetime()
        asset_returns:DataFrame = history.pct_change().iloc[1:]
        stock_returns = asset_returns.loc[:, asset_returns.columns != self.market].tail(-1)
        asset_returns['market_lag_t-1'] = asset_returns[self.market].shift(1)
        asset_returns['market_lag_t+1'] = asset_returns[self.market].shift(-1)
        asset_returns = asset_returns.iloc[1:-1]
        stock_returns = stock_returns.iloc[:-1]
        industry_df:DataFrame = pd.DataFrame(index=asset_returns.index)
        for industry_code in grouped_industries:
            if len(grouped_industries[industry_code]) > 1:
                ind_symbols:List[Symbol] = grouped_industries[industry_code]
                if all(symbol in asset_returns.columns for symbol in ind_symbols):
                    industry_df[industry_code] = asset_returns[ind_symbols].mean(axis=1)
            else:
                stock_returns = stock_returns.drop(stock_returns[grouped_industries[industry_code]], axis=1)
        # run industry regression
        x:np.ndarray = asset_returns[[self.market, 'market_lag_t-1', 'market_lag_t+1']].values
        y:np.ndarray = industry_df.values
        model = self.multiple_linear_regression(x, y)
        beta_values_industry:np.ndarray = sum(model.params[1:])
        for i, industry in enumerate(list(industry_df.columns)):
            if industry not in self.industry_beta:
                self.industry_beta[industry] = RollingWindow[float](self.rolling_period)
            if not np.isnan(beta_values_industry[i]):
                self.industry_beta[industry].Add(beta_values_industry[i])
        # run stock regression
        x:np.ndarray = asset_returns[[self.market, 'market_lag_t-1', 'market_lag_t+1']].values
        y:np.ndarray = stock_returns.values
        model = self.multiple_linear_regression(x, y)
        beta_values_stocks:np.ndarray = sum(model.params[1:])
        for i, asset in enumerate(list(stock_returns.columns)):
            asset_s:Symbol = self.Symbol(asset)
            if not np.isnan(beta_values_stocks[i]):
                self.stock_beta[asset_s] = beta_values_stocks[i]
    irsb_values:Dict[FineFundamental, float] = {}
    # IRSB calculation
    for stock in fine:
        symbol:Symbol = stock.Symbol
        if symbol in self.stock_beta:
            for industry in grouped_industries:
                if industry in self.industry_beta:
                    if symbol in grouped_industries[industry] and self.industry_beta[industry].IsReady:
                        irsb_values[stock] = (self.stock_beta[symbol] - self.industry_beta[industry][1]) / self.industry_beta[industry][1]
    # sorting by IRSB values
    if len(irsb_values) >= self.quantile:
        sorted_by_irsb:List[FineFundamental] = sorted(irsb_values, key=irsb_values.get, reverse=True)
        quantile:int = len(sorted_by_irsb) // self.quantile
        
        # portfolios
        long:List[FineFundamental] = sorted_by_irsb[:quantile]
        short:List[FineFundamental] = sorted_by_irsb[-quantile:]
        # calculate weights based on market cap
        sum_long:float = sum([x.MarketCap for x in long])
        for stock in long:
            self.weight[stock.Symbol] = (stock.MarketCap / sum_long) * self.traded_percentage 
        sum_short:float = sum([x.MarketCap for x in short])
        for stock in short:
            self.weight[stock.Symbol] = (-stock.MarketCap / sum_short) * self.traded_percentage 
    return list(self.weight.keys())
    
def OnData(self, data):
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    stocks_invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in stocks_invested:
        if symbol not in self.weight:
            self.Liquidate(symbol)
            
    for symbol, w in self.weight.items():
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, w)
        
    self.weight.clear()
    
def Selection(self):
    self.selection_flag = True
def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray):
    # x:np.ndarray = np.array(x).T
    x = sm.add_constant(x, prepend=True)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
