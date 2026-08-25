# Original QuantConnect / library Python
# locale=en slug="the-effect-of-market-returns-on-factor-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import List, Dict
import numpy as np
import pandas as pd
# endregion

class TheEffectofMarketReturnsonFactorReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
 
    self.fundamental_count:int = 3000
    self.leverage:int = 5
    self.quantile:int = 5
    self.daily_period:int = 252
    self.monthly_period:int = 12

    self.tickers_to_ignore:List[str] = ['SGA']
    self.data:Dict[Symbol, SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}

    self.selection_flag:bool = False
    self.rebalance_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)

    self.current_year:int = -1

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # store daily stock prices
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        if symbol in self.data:
            self.data[symbol].update_daily_return(stock.AdjustedPrice)

    # monthly selection
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False

    # store monthly market prices
    if self.market in self.data:
        self.data[self.market].update_monthly_return(self.Securities[self.market].Price, 0)

    # store monthly stock prices
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        if stock.Volume != 0:
            volume:float = stock.Volume
        else:
            continue

        if symbol in self.data:
            self.data[symbol].update_monthly_return(stock.AdjustedPrice, volume)

    fundamental:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.MarketCap != 0 and x.Market == 'usa' \
                            and not np.isnan(x.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths) and x.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths != 0 \
                            and not np.isnan(x.FinancialStatements.IncomeStatement.GrossProfit.TwelveMonths) and x.FinancialStatements.IncomeStatement.GrossProfit.TwelveMonths != 0 \
                            and not np.isnan(x.FinancialStatements.IncomeStatement.OperatingExpense.TwelveMonths) and x.FinancialStatements.IncomeStatement.OperatingExpense.TwelveMonths != 0 \
                            and not np.isnan(x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.TwelveMonths) and x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.TwelveMonths != 0 \
                            and ((x.SecurityReference.ExchangeId == "NYS") or (x.SecurityReference.ExchangeId == "NAS") or (x.SecurityReference.ExchangeId == "ASE")) \
                            and x.Symbol.Value not in self.tickers_to_ignore]

    if len(fundamental) > self.fundamental_count:
        selection = {x.Symbol:x for x in sorted(fundamental, key=lambda x:x.MarketCap, reverse=True)[:self.fundamental_count]}
    else:
        selection = {x.Symbol:x for x in fundamental}

    # price warmup
    for symbol in list(selection.keys()):
        if symbol in self.data:
            continue
        
        self.data[symbol] = data_tools.SymbolData(self.daily_period, self.monthly_period)
        history:DataFrame = self.History(symbol, self.daily_period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        data:pd.DataFrame = history.loc[symbol]
        monthly_data = data.groupby(pd.Grouper(freq='MS')).last()
        for time, row in monthly_data.iterrows():
            self.data[symbol].update_monthly_return(row.close, row.volume)
        for time, row in data.iterrows():
            self.data[symbol].update_daily_return(row.close)

    if self.market not in self.data:
        self.data[self.market] = data_tools.SymbolData(self.daily_period, self.monthly_period)
        history:DataFrame = self.History(self.market, self.daily_period, Resolution.Daily)
        if not history.empty:
            data:pd.DataFrame = history.loc[self.market].groupby(pd.Grouper(freq='MS')).last()
            for time, row in data.iterrows():
                self.data[self.market].update_monthly_return(row.close, 0)
        else:
            self.Log(f"Not enough data for {symbol} yet.")
     
    if self.Time.year != self.current_year:
        self.current_year = self.Time.year
        [self.data[sym].update_total_assets(selection[sym].FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths) for sym in selection]

    # stock returns
    returns_by_stock:Dict[Symbol, List[Tuple[datetime, float]]] = {sym : sym_data.get_monthly_returns() for sym, sym_data in self.data.items() if sym_data.is_ready() and sym_data.total_asset_is_ready() and sym in selection.keys() and sym != self.market}
    stock_returns:List = list(zip(*[[i for i in x] for x in returns_by_stock.values()]))

    market_returns:np.ndarray = np.array(self.data[self.market].get_monthly_returns())

    if len(stock_returns) == 0:
        return Universe.Unchanged

    # run stock regression
    x:np.ndarray = market_returns
    y:np.ndarray = np.array(stock_returns)
    model = data_tools.multiple_linear_regression(x, y)
    beta_values:np.ndarray = model.params[1]
    resid = model.resid

    data:Dict[str, float] = {}
    
    # get all factors
    data['symbols'] = [sym for sym in list(returns_by_stock.keys())]
    data['betas'] =  [beta_values[n] for n, sym in enumerate(list(returns_by_stock.keys()))]
    data['VOL'] = [self.data[sym].get_volatility() for sym in list(returns_by_stock.keys())]
    data['CORR'] =  [np.corrcoef(market_returns, self.data[sym].get_monthly_returns())[0, 1] for sym in list(returns_by_stock.keys())]
    data['IVOL'] = [np.std(resid.T[n]) for n, sym in enumerate(list(returns_by_stock.keys()))]
    data['ME'] = [selection[sym].MarketCap for sym in list(returns_by_stock.keys())]
    data['BM'] = [selection[sym].ValuationRatios.PBRatio for sym in list(returns_by_stock.keys())] 
    data['OP'] = [(selection[sym].FinancialStatements.IncomeStatement.GrossProfit.TwelveMonths - selection[sym].FinancialStatements.IncomeStatement.OperatingExpense.TwelveMonths - selection[sym].FinancialStatements.IncomeStatement.DepreciationAndAmortization.TwelveMonths) for sym in list(returns_by_stock.keys())]
    data['AG'] = [self.data[sym].get_asset_growth() for sym in list(returns_by_stock.keys())]
    data['MOM'] = [self.data[sym].get_momentum() for sym in list(returns_by_stock.keys())]
    data['STR'] = [self.data[sym].get_str() for sym in list(returns_by_stock.keys())]
    data['MAX'] = [self.data[sym].get_max() for sym in list(returns_by_stock.keys())]
    data['M1'] = [self.data[sym].get_m1() for sym in list(returns_by_stock.keys())]
    data['ILLIQ'] = [self.data[sym].get_illiquidity() for sym in list(returns_by_stock.keys())]

    # create dataframe from factors
    df = pd.DataFrame(data)

    # rank stocks by percentile
    df = df.dropna(axis=0)
    df[df.columns[1:]] = df[df.columns[1:]].rank(axis=0, pct=True)
    df['average_percentile'] = df[df.columns[1:]].mean(axis=1)

    # sort by average percentile and divide to quantiles
    if len(df) >= self.quantile:
        sorted_symbols:List[Symbol] = df.sort_values(by='average_percentile', ascending=True).symbols.values
        quantile:int = int(len(sorted_symbols) / self.quantile)
        long:List[FineFundamental] = list(sorted_symbols)[:quantile]
        short:List[FineFundamental] = list(sorted_symbols)[-quantile:]

        # calculate weights based on values
        sum_long:float = sum([selection[x].MarketCap for x in long])
        for stock in long:
            self.weight[stock] = selection[stock].MarketCap / sum_long

        sum_short:float = sum([selection[x].MarketCap for x in short])
        for stock in short:
            self.weight[stock] = -selection[stock].MarketCap / sum_short
        
        self.rebalance_flag = True

    return list(selection.keys())

def OnData(self, data: Slice) -> None:
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False

    # trade execution
    if self.data[self.market].get_last_month_return()
