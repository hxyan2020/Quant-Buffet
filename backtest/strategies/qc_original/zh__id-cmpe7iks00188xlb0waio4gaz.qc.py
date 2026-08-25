# Original QuantConnect / library Python
# locale=zh slug="价值不确定性溢价"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from numpy import isnan
from typing import List, Dict
class TheValueUncertaintyPremium(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100_000)
    self.exchange_codes: List[str] = ['NYS']
    self.weight: Dict[Symbol, float] = {}
    self.quantile: int = 10
    self.leverage: int = 10
    self.bm_by_symbol: Dict[Symbol, RollingWindow] = {}
    
    self.m_period: int = 12
    self.required_estimate_quarter: int = 4
    self.universe_selection_period: int = 12
    self.recent_EPS_estimate: Dict[Symbol, Dict[int, List[float]]] = {}
    
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.already_subscribed:list[Symbol] = []
    self.last_fundamental: List[Symbol] = []
    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    self.rebalance_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
    
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    # select new universe once a period
    if self.Time.month % self.universe_selection_period == 0:
        selected: List[Fundamental] = [
            x for x in fundamental 
            if x.HasFundamentalData 
            and x.Market == 'usa' 
            and x.MarketCap != 0 
            and x.SecurityReference.ExchangeId in self.exchange_codes 
            and not isnan(x.ValuationRatios.ForwardDividend) and x.ValuationRatios.ForwardDividend
            and not isnan(x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths) and x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths != 0 
            and not isnan(x.EarningReports.BasicAverageShares.ThreeMonths) and x.EarningReports.BasicAverageShares.ThreeMonths != 0 
            and not isnan(x.FinancialStatements.BalanceSheet.CurrentLiabilities.ThreeMonths) and x.FinancialStatements.BalanceSheet.CurrentLiabilities.ThreeMonths
        ]
        if len(selected) > self.fundamental_count:
            selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        for stock in selected:
            symbol: Symbol = stock.Symbol
            if symbol not in self.already_subscribed:
                self.AddData(EstimizeEstimate, symbol)
                self.already_subscribed.append(symbol)
        
        self.last_fundamental = selected
    self.rebalance_flag = True
    UNC: Dict[Symbol, float] = {}
    for stock in self.last_fundamental:
        symbol: Symbol = stock.Symbol
        
        # store pb value
        if symbol not in self.bm_by_symbol:
            self.bm_by_symbol[symbol] = RollingWindow[float](self.m_period)
        # calculate UNC
        if self.bm_by_symbol[symbol].IsReady:
            bm_values: List[float] = [x for x in self.bm_by_symbol[symbol]]
            bm_std: float = np.std(bm_values)
            pb_mean: float = np.mean(bm_values)
            UNC[stock] = bm_std / pb_mean
        # get net income estimate
        if symbol.Value in self.recent_EPS_estimate and self.Time.year in self.recent_EPS_estimate[symbol.Value]:
            current_be: float = stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths - stock.FinancialStatements.BalanceSheet.CurrentLiabilities.ThreeMonths
            
            # NOTE Expected net income for the end of fiscal year y, given the information available up to day d, is estimated as the product of expected earnings per share given by the mean of analysts’ forecasts up to day d and the total number of shares outstanding.
            estimated_net_income: float = np.mean(self.recent_EPS_estimate[symbol.Value][self.Time.year]) * stock.EarningReports.BasicAverageShares.ThreeMonths
            
            expected_dividend: float = stock.ValuationRatios.ForwardDividend
            expected_be: float = current_be + estimated_net_income - expected_dividend
            bm: float = expected_be / stock.MarketCap
            self.bm_by_symbol[symbol].Add(bm)
        else:
            if self.bm_by_symbol[symbol].Count != 0:
                self.bm_by_symbol[symbol].Reset()
    if len(UNC) >= self.quantile:
        sorted_by_perf: List[Tuple[Symbol, float]] = sorted(UNC.items(), key = lambda x:x[1], reverse=True)
        quantile: int = int(len(sorted_by_perf) / self.quantile)
        long: List[Fundamental] = [x[0] for x in sorted_by_perf[:quantile]]
        short: List[Fundamental] = [x[0] for x in sorted_by_perf[-quantile:]]
        # market cap weighting
        for i, portfolio in enumerate([long, short]):
            mc_sum: float = sum(list(map(lambda stock: stock.MarketCap, portfolio)))
            for stock in portfolio:
                self.weight[stock.Symbol] = ((-1)**i) * stock.MarketCap / mc_sum
    return list(self.weight.keys())
    
def OnData(self, slice: Slice) -> None:
    # store latest EPS Estimize estimate
    estimize: Dict[Symbol, float] = slice.Get(EstimizeEstimate)
    for symbol, value in estimize.items():
        ticker: str = symbol.Value
        # store eond of the year estimates indexed by fiscal year
        if value.FiscalQuarter == self.required_estimate_quarter:
            if ticker not in self.recent_EPS_estimate:
                self.recent_EPS_estimate[ticker] = {}
            if value.FiscalYear not in self.recent_EPS_estimate[ticker]:
                self.recent_EPS_estimate[ticker][value.FiscalYear] = []
            self.recent_EPS_estimate[ticker][value.FiscalYear].append(value.Eps)
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if slice.contains_key(symbol) and slice[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()

def Selection(self) -> None:
    self.selection_flag = True
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
