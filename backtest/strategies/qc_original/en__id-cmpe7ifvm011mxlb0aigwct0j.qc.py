# Original QuantConnect / library Python
# locale=en slug="现金盈利预测收益回报投资策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from collections import deque
from typing import Dict, List
import data_tools
from pandas.tseries.offsets import BDay
from dateutil.relativedelta import relativedelta
from numpy import isnan
from functools import reduce
# endregion

class CashOperatingProfitabilityPredictsEarningsAnnouncementReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2008, 1, 1)
    self.SetCash(100000)

    self.quantile:int = 10
    self.leverage:int = 5
    self.long_num:int = 5
    self.short_num:int = 5
    self.holding_period:int = 5
    self.DR_period:int = 2

    self.financial_statement_names:List[str] = [
        'FinancialStatements.IncomeStatement.TotalRevenue.TwelveMonths',
        'FinancialStatements.IncomeStatement.CostOfRevenue.TwelveMonths',
        'FinancialStatements.IncomeStatement.GeneralAndAdministrativeExpense.TwelveMonths',
        'FinancialStatements.IncomeStatement.ResearchAndDevelopment.TwelveMonths',
        'FinancialStatements.CashFlowStatement.ChangeInReceivables.TwelveMonths',
        'FinancialStatements.CashFlowStatement.ChangeInInventory.TwelveMonths',
        'FinancialStatements.CashFlowStatement.ChangeInPrepaidAssets.TwelveMonths',
        'FinancialStatements.BalanceSheet.CurrentDeferredRevenue.TwelveMonths',
        'FinancialStatements.CashFlowStatement.ChangeInAccountPayable.TwelveMonths',
        'FinancialStatements.CashFlowStatement.ChangeInAccruedExpense.TwelveMonths',
    ]

    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    self.DR_data:Dict[Symbol, float] = {}  

    self.earnings_data:Dict[datetime.date, List[str]] = {} 
    self.tickers:Set(str) = set()

    self.first_date:Union[datetime.date, None] = None
    
    earnings_data:str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json:list[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date:datetime.date = datetime.strptime(obj['date'], '%Y-%m-%d').date()

        self.earnings_data[date] = []

        if not self.first_date: self.first_date = date
        
        for stock_data in obj['stocks']:
            ticker:str = stock_data['ticker']

            self.tickers.add(ticker)
            self.earnings_data[date].append(ticker)

    # 5 equally weighted brackets for traded symbols. - 5 symbols long, 5 symbols short, 5 days of holding
    self.trade_manager:TradeManager = data_tools.TradeManager(self, self.long_num, self.short_num, self.holding_period)

    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.selection_month:int = 4
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]: 
    # yearly selection
    if self.selection_flag:
        self.selection_flag = False

        COP_stocks:Dict[Fundamental, float] = {}
        selected:List[Fundamental] = [x for x in fundamental if x.Symbol.Value in self.tickers and \
                    all((not isnan(self.rgetattr(x, statement_name)) and self.rgetattr(x, statement_name) != 0) for statement_name in self.financial_statement_names)]

        for stock in selected:
            symbol:Symbol = stock.Symbol

            if symbol not in self.DR_data:
                self.DR_data[symbol] = data_tools.DRChangeManager(self.DR_period)
            self.DR_data[symbol].update_data(stock.FinancialStatements.BalanceSheet.CurrentDeferredRevenue.TwelveMonths)
            
            if not self.DR_data[symbol].is_ready():
                continue
            
            DR_change = self.DR_data[symbol].get_DR_change()
            sales, COGS, SG_A, R_D, REC_change, INV_change, XPP_change, DR_change, AP_change, XACC_change = [self.rgetattr(stock, statement_name) for statement_name in self.financial_statement_names]

            # calculate COP value on stocks
            if stock not in COP_stocks:
                COP_stocks[symbol] = sales - COGS - (SG_A - R_D) - REC_change - INV_change - XPP_change + DR_change + AP_change + XACC_change            

        # sort and divide to quantiles
        if len(COP_stocks) >= self.quantile:
            sorted_COP = sorted(COP_stocks, key=COP_stocks.get, reverse=True)
            quantile:int = int(len(sorted_COP) / self.quantile)
            self.long = sorted_COP[:quantile]
            self.short = sorted_COP[-quantile:]       
    
    return self.long + self.short

def OnData(self, data: Slice) -> None:
    # liquidate opened symbols after five days
    self.trade_manager.TryLiquidate()

    date_to_lookup:datetime.date = (self.Time + BDay(2)).date()
    
    # if there is no earnings data yet
    if date_to_lookup  None:
    if self.Time.month == self.selection_month:
        self.selection_flag = True
        
        self.long.clear()
        self.short.clear()

# https://gist.github.com/wonderbeyond/d293e7a2af1de4873f2d757edd580288
def rgetattr(self, obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))
