# Original QuantConnect / library Python
# locale=zh slug="销售季节性溢价"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from collections import deque
from typing import List, Dict, Tuple, Deque
from numpy import isnan
class SalesSeasonalityPremium(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.avg_SEA_threshold:int = 100
    self.max_period:int = 1000
    self.period:int = 13
    self.leverage:int = 10
    self.min_share_price:int = 5
    self.consecutive_quarter_count:int = 6
    self.percentiles:List[int] = [10, 90]
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']	
    self.sea:Dict[Symbol, Deque[Tuple[float]]] = {} # SEA quarterly data
    self.avgsea_alltime:Deque[float] = deque(maxlen=self.max_period)   # All time SEA values.
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.weight:Dict[Symbol, float] = {}
    
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.selection_flag:bool = True
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and x.Market == 'usa' and \
        not isnan(x.FinancialStatements.IncomeStatement.TotalRevenue.ThreeMonths) and x.FinancialStatements.IncomeStatement.TotalRevenue.ThreeMonths != 0 and \
        not isnan(x.FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths) and x.FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths != 0 and \
        not isnan(x.EarningReports.BasicAverageShares.ThreeMonths) and x.EarningReports.BasicAverageShares.ThreeMonths > 0 and \
        not isnan(x.EarningReports.BasicEPS.TwelveMonths) and x.EarningReports.BasicEPS.TwelveMonths > 0 and \
        not isnan(x.ValuationRatios.PERatio) and x.ValuationRatios.PERatio > 0 and \
        x.SecurityReference.ExchangeId in self.exchange_codes and x.MarketCap != 0
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    # Stock which had earnings last month.
    last_month_date:datetime = self.Time - timedelta(days = self.Time.day)
    fine_selected = [x for x in selected if x.EarningReports.FileDate.Value.month == last_month_date.month and x.EarningReports.FileDate.Value.year == last_month_date.year]
    
    avg_sea:Dict[Fundamental, float] = {}
    for stock in fine_selected:
        symbol = stock.Symbol
        
        # store sea data.
        if symbol not in self.sea:
            self.sea[symbol] = deque(maxlen = self.period)
        # SEA calc.
        curr_month:float = stock.EarningReports.FileDate.Value.month
        revenue:float = stock.FinancialStatements.IncomeStatement.TotalRevenue.ThreeMonths
        # annual_revenue = stock.FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths
        annual_revenue:float = (revenue / curr_month) * 12
        
        if annual_revenue != 0:
            self.sea[symbol].append((stock.EarningReports.FileDate.Value, revenue / annual_revenue))
        
        if len(self.sea[symbol]) == self.sea[symbol].maxlen:
            curr_year:int = self.Time.year
            relevant_quarters:List[Tuple[float]] = [x for x in self.sea[symbol] if x[0].year == curr_year - 2 or x[0].year == curr_year - 3]
            # Make sure we have a consecutive seasonal data => 2 years by 4 quarters.
            if len(relevant_quarters) == self.consecutive_quarter_count:
                avgsea:float = np.mean([x[1] for x in relevant_quarters])
                avg_sea[stock] = avgsea
                
                # All time avg_sea values to calculate deciles.
                self.avgsea_alltime.append(avgsea)
    
    if len(avg_sea) != 0:
        # Sort by SEA.
        long:List[Fundamental] = []
        short:List[Fundamental] = []
        
        # Wait for at least 100 last AVGSEA values to estimate percentile values.
        if len(self.avgsea_alltime) > self.avg_SEA_threshold: 
            avgsea_values:List[float] = [x for x in self.avgsea_alltime]
            
            top_decile:float = np.percentile(avgsea_values, self.percentiles[1])
            bottom_decile:float = np.percentile(avgsea_values, self.percentiles[0])
            
            for stock, avgsea in avg_sea.items():
                if avgsea > top_decile:
                    short.append(stock)
                elif avgsea  None:
    self.selection_flag = True

def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
