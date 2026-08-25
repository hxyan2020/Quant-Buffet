# Original QuantConnect / library Python
# locale=en slug="流动性、机构持股与彩票效应对股票的影响"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
from dateutil.relativedelta import relativedelta
# endregion
class InfluenceofLiquidityInstitutionalOwnershipLotteryEffectonStocks(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2004, 1, 1)
    self.SetCash(100000)
    
    data_delay_months:int = 3
    file_contents:str = self.Download('data.quantpedia.com/backtesting_data/economic/institutional_ownership/institutional_ownership_in_percents.csv')
    lines:List[str] = file_contents.split('\r\n')
    self.tickers:List[str] = lines[0].split(',')[1:]
    dict_list:List[Dict[str, float]] = []
    
    for line in lines[1:]:
        line_split:List[str] = line.split(',')
        date = (datetime.strptime(line_split[0], "%Y-%m-%d") + relativedelta(months=data_delay_months)).date()
        temp_dict:Dict[str, float] = { 'date' : date }
        for i in range(1, len(line_split)):
            ticker:str = self.tickers[i-1]
            temp_dict[ticker] = float(line_split[i]) if line_split[i] != '' else 0.
        
        dict_list.append(temp_dict)
    
    io_df:DataFrame = pd.DataFrame(dict_list, columns=['date'] + self.tickers)
    self.io_df:DataFrame = io_df.set_index('date')
    self.leverage:int = 3
    self.selection_month:int = 12
    self.period:int = 12 * 21
    self.quantile:int = 3
    self.price_data:Dict[Symbol, RollingWindow] = {}
    self.weight:Dict[Symbol, float] = {}
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)
def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    # store daily stock prices
    for stock in coarse:
        symbol:Symbol = stock.Symbol.Value
        if symbol in self.price_data:
            self.price_data[symbol].Add(stock.AdjustedPrice)
    # monthly selection
    if not self.selection_flag:
        return Universe.Unchanged
    
    selection:List[Symbol] = [x.Symbol for x in coarse if x.HasFundamentalData and x.Symbol.Value in list(self.io_df.columns)]
    # warmup price rolling windows
    for symbol in selection:
        if symbol in self.price_data:
            continue
        
        self.price_data[symbol] = RollingWindow[float](self.period)
       
        history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes:pd.Series = history.loc[symbol].close
        for time, close in closes.iteritems():
            self.price_data[symbol].Add(close)
    return [x for x in selection if self.price_data[x].IsReady]
def FineSelectionFunction(self, fine:List[FineFundamental]) -> List[Symbol]:
    stock_by_ticker:Dict[str, FineFundamental] = { x.Symbol.Value : x for x in fine }
    # filter stocks
    if not self.io_df.empty and len(stock_by_ticker) != 0:
        last_io_values_sorted:DataFrame = self.io_df[self.io_df.index  MAX_median]
            # value weighting
            market_cap_long:float = sum([x.MarketCap for x in long])
            market_cap_short:float = sum([x.MarketCap for x in short])
            for stock in long:
                self.weight[stock.Symbol] = stock.MarketCap / market_cap_long
            for stock in short:
                self.weight[stock.Symbol] = -stock.MarketCap / market_cap_short
    return list(self.weight.keys())
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # trade execution
    invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in self.weight:
            self.Liquidate(symbol)
    for symbol, w in self.weight.items():
        self.SetHoldings(symbol, w)
    
    self.weight.clear()

def Selection(self) -> None:
    if self.Time.month == self.selection_month:
        self.selection_flag = True
# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
