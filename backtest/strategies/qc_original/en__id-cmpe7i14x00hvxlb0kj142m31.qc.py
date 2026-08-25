# Original QuantConnect / library Python
# locale=en slug="跨行业离散因子策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
from collections import deque
from pandas.core.frame import DataFrame
import statsmodels.api as sm
from dateutil.relativedelta import relativedelta
# endregion
class CrossIndustryDispersionFactor(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.stock_price_data:Dict[Symbol, deque] = {}
    self.ff_price_data:Dict[Symbol, deque] = {}
    
    self.leverage:int = 3
    self.month_period:int = 2 * 12
    self.period:int = self.month_period * 30
    self.quantile:int = 5  
    self.SetWarmup(self.period, Resolution.Daily)
    
    self.market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.ff_industry:Symbol = self.AddData(QuantpediaFamaFrench, "fama_french_49_industry_VW", Resolution.Daily).Symbol
    self.weight:Dict[Symbol, float] = {}
    self.coarse_count:int = 1000
    self.selection_flag:bool = False
    self.exchanges:List[str] = ['NYS', 'NAS', 'ASE']
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)
def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    # update price every day
    for stock in coarse:
        symbol = stock.Symbol
        if symbol in self.stock_price_data:
            self.stock_price_data[symbol].append((self.Time, stock.AdjustedPrice))
    if not self.selection_flag:
        return Universe.Unchanged
    if self.coarse_count = 1],
                key=lambda x: x.DollarVolume, reverse=True)[:self.coarse_count]
    else:
        selected:list = [x for x in coarse if x.HasFundamentalData and x.AdjustedPrice >= 1]
    
    # warmup prices
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol in self.stock_price_data:
            continue
        
        self.stock_price_data[symbol] = deque(maxlen=self.period)
        history = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes = history.loc[symbol].close
        for time, close in closes.iteritems():
            self.stock_price_data[symbol].append((time, close))
        
    return [x.Symbol for x in selected if len(self.stock_price_data[x.Symbol]) == self.stock_price_data[x.Symbol].maxlen]

def FineSelectionFunction(self, fine:List[FineFundamental]) -> List[Symbol]:
    # filter fine
    fine:Dict[Symbol, FineFundamental] = {x.Symbol : x for x in fine if x.MarketCap != 0 and x.SecurityReference.ExchangeId in self.exchanges }
    if len(fine) >= self.coarse_count:
        fine = {x[0] : x[1] for x in sorted(fine.items(), key = lambda x: x[1].MarketCap, reverse=True)[:self.coarse_count]}
    # create FF df out of deques
    assets:Dict = {symbol : [i[1] for i in deq] for symbol, deq in self.ff_price_data.items()}
    ff_df:DataFrame = pd.DataFrame(assets, index=[i[0] for i in list(self.ff_price_data.values())[0]])
    
    # daily FF returns to daily equity
    ff_df[QuantpediaFamaFrench._columns] = (1 + ff_df[QuantpediaFamaFrench._columns]).cumprod()
    
    # calculate monthly return
    ff_df = ff_df.groupby(pd.Grouper(freq='M')).last()
    ff_df = ff_df.pct_change().iloc[-self.month_period-1:-1]
    CID:DataFrame = abs(ff_df[QuantpediaFamaFrench._columns].sub(ff_df[self.market], axis=0)).mean(axis=1)
    # create stock df out of deques
    assets:Dict = {symbol : [i[1] for i in self.stock_price_data[symbol]] for symbol, _  in fine.items()}
    stock_df:DataFrame = pd.DataFrame(assets, index=[i[0] for i in list(self.stock_price_data.values())[0]])
    
    # calculate monthly stock returns
    stock_df = stock_df.groupby(pd.Grouper(freq='M')).last()
    stock_df = stock_df.pct_change().iloc[-self.month_period-1:-1]
    # run regression
    x:np.ndarray = CID.values
    y:np.ndarray = stock_df.values
    model = self.multiple_linear_regression(x, y)
    beta_values:np.ndarray = model.params[1]
    asset_cols:List[str] = list(stock_df.columns)
    # store beta by symbol
    beta_by_symbol:Dict[Symbol, float] = {}
    for i, beta in enumerate(beta_values):
        beta_by_symbol[fine[asset_cols[i]]] = beta
    if len(beta_by_symbol) >= self.quantile:
        # sort by beta
        sorted_beta:List[Tuple] = sorted(beta_by_symbol, key=beta_by_symbol.get, reverse=True)
        quantile:int = len(sorted_beta) // self.quantile
        long:List[FineFundamental] = sorted_beta[-quantile:]
        short:List[FineFundamental] = sorted_beta[:quantile]
        total_market_cap_long:float = sum([x.MarketCap for x in long])
        total_market_cap_short:float = sum([x.MarketCap for x in short])
        
        for stock in long:
            self.weight[stock.Symbol] = stock.MarketCap / total_market_cap_long
        for stock in short:
            self.weight[stock.Symbol] = -stock.MarketCap / total_market_cap_short
    return list(self.weight.keys())
def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def OnData(self, data: Slice) -> None:
    # store FF industry data and market data
    if data.ContainsKey(self.ff_industry) and data[self.ff_industry]:
        if data.ContainsKey(self.market) and data[self.market]:
            # init deques
            for symbol in [self.market] + QuantpediaFamaFrench._columns:
                if symbol not in self.ff_price_data:
                    self.ff_price_data[symbol] = deque(maxlen=self.period)
            # FF daily returns
            for col in QuantpediaFamaFrench._columns:
                self.ff_price_data[col].append((self.Time, data[self.ff_industry].GetProperty(col) / 100.))
            
            # market daily prices
            self.ff_price_data[self.market].append((self.Time, data[self.market].Value))
    if not self.selection_flag:
        return
    self.selection_flag = False
    # liquidate
    stocks_invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in stocks_invested:
        if symbol not in self.weight:
            self.Liquidate(symbol)
    # trade execution
    for symbol, w in self.weight.items():
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, w)
    self.weight.clear()
def Selection(self) -> None:
    if self.ff_price_data:
        if all(len(self.ff_price_data[col]) == self.period for col in QuantpediaFamaFrench._columns) and \
            len(self.ff_price_data[self.market]) == self.period:
            self.selection_flag = True
def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray):
    # x = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
    
# Quantpedia data
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFamaFrench(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/equity/fama_french/fama_french_49_industry_VW.csv", SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)

_last_update_date:datetime.date = datetime(1,1,1).date()
_columns:List[str] = list()
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return QuantpediaFamaFrench._last_update_date
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaFamaFrench()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit():
        QuantpediaFamaFrench._columns = line.split(',')[1:] # skip 'Date' columns
        return None
    
    split = line.split(',')
    
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + relativedelta(months=1)
    if data.Time.date() > QuantpediaFamaFrench._last_update_date:
        QuantpediaFamaFrench._last_update_date = data.Time.date()
    for i, col_name in enumerate(QuantpediaFamaFrench._columns):
        data[col_name] = float(split[i+1]) 
    return data
# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
