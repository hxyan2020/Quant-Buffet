# Original QuantConnect / library Python
# locale=zh slug="应计项目效应结合价格动量"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from numpy import floor, isnan
from AlgorithmImports import *
from typing import List, Dict
import data_tools
class AccrualsEffectPriceMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.exchange_codes:List[str] = ['NYS', 'ASE']	
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    self.quantile:int = 5
    self.leverage:int = 5
    self.min_share_price:int = 5
    self.months:int = 0
    self.period:int = 6 * 21
    self.holding_period:int = 6
    
    self.data:Dict[Symbol, data_tools.SymbolData] = {}
    self.managed_queue:List[data_tools.RebalanceQueueItem] = []
    
    # Latest accurals data
    self.accural_data:Dict[Symbol, data_tools.AccuralsData] = {}
    
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
    
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and x.Market == 'usa' and x.MarketCap != 0
        and not isnan(x.FinancialStatements.BalanceSheet.CurrentAssets.ThreeMonths) and (x.FinancialStatements.BalanceSheet.CurrentAssets.ThreeMonths > 0) \
        and not isnan(x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.ThreeMonths) and (x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.ThreeMonths) > 0 \
        and not isnan(x.FinancialStatements.BalanceSheet.CurrentLiabilities.ThreeMonths) and (x.FinancialStatements.BalanceSheet.CurrentLiabilities.ThreeMonths) > 0 \
        and not isnan(x.FinancialStatements.BalanceSheet.CurrentDebt.ThreeMonths) and (x.FinancialStatements.BalanceSheet.CurrentDebt.ThreeMonths) > 0 \
        and not isnan(x.FinancialStatements.BalanceSheet.IncomeTaxPayable.ThreeMonths) and (x.FinancialStatements.BalanceSheet.IncomeTaxPayable.ThreeMonths) > 0 \
        and not isnan(x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.ThreeMonths) and (x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.ThreeMonths) > 0 \
        and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            continue
        self.data[symbol] = data_tools.SymbolData(self.period)
        history = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet")
            continue
        closes = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].update(close)
            
    bs_acc:Dict[Symbol, float] = {}
    momentum:Dict[Symbol, float] = {} 
    current_accurals_data:Dict[Symbol, data_tools.AccuralsData] = {}
    
    for stock in selected:
        symbol = stock.Symbol
        
        if not self.data[symbol].is_ready():
            continue
        momentum[symbol] = self.data[symbol].performance()
        
        # Accural calc
        current_accurals_data[symbol] = data_tools.AccuralsData(stock.FinancialStatements.BalanceSheet.CurrentAssets.ThreeMonths, stock.FinancialStatements.BalanceSheet.CashAndCashEquivalents.ThreeMonths,
                                                    stock.FinancialStatements.BalanceSheet.CurrentLiabilities.ThreeMonths, stock.FinancialStatements.BalanceSheet.CurrentDebt.ThreeMonths, stock.FinancialStatements.BalanceSheet.IncomeTaxPayable.ThreeMonths,
                                                    stock.FinancialStatements.IncomeStatement.DepreciationAndAmortization.ThreeMonths, stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths)
    
        if symbol in self.accural_data:
            bs_acc[symbol] = self.CalculateAccurals(current_accurals_data[symbol], self.accural_data[symbol])
    
    # Clear old accruals and set new ones 
    self.accural_data.clear()
    for symbol in current_accurals_data:
        self.accural_data[symbol] = current_accurals_data[symbol]
    
    long:List[Symbol] = []
    short:List[Symbol] = []
        
    if len(momentum) != 0 and len(bs_acc) != 0:
        # Momentum sorting
        sorted_by_mom:List[Tuple[Symbol, float]] = sorted(momentum.items(), key = lambda x: x[1], reverse = True)
        quintile:int = int(len(sorted_by_mom) / self.quantile)
        top_by_mom:List[Symbol] = [x[0] for x in sorted_by_mom[:quintile]]
        low_by_mom:List[Symbol] = [x[0] for x in sorted_by_mom[-quintile:]]

        # Accural sorting
        sorted_by_acc:List[Tuple[Symbol, float]] = sorted(bs_acc.items(), key = lambda x: x[1], reverse = True)
        quintile:int = int(len(sorted_by_acc) / self.quantile)
        top_by_acc:List[Symbol] = [x[0] for x in sorted_by_acc[:quintile]]
        low_by_acc:List[Symbol] = [x[0] for x in sorted_by_acc[-quintile:]]
        
        long = [x for x in top_by_mom if x in low_by_acc]
        short = [x for x in low_by_mom if x in top_by_acc]
        
        if len(long) != 0:
            long_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period / len(long)
            # symbol/quantity collection
            long_symbol_q:List[Tuple[Symbol, int]] = [(x, floor(long_w / self.data[x].LastPrice)) for x in long]
        else:
            long_symbol_q = []

        if len(short) != 0:
            short_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period / len(short)
            # symbol/quantity collection
            short_symbol_q:List[Tuple[Symbol, int]] = [(x, floor(short_w / self.data[x].LastPrice)) for x in short]
        else:
            short_symbol_q = []
            
        self.managed_queue.append(data_tools.RebalanceQueueItem(long_symbol_q, short_symbol_q))
    
    return long + short

def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    remove_item = None
    
    # Rebalance portfolio
    for item in self.managed_queue:
        if item.holding_period == self.holding_period + 1: # All portfolios are held for six months (month 2 to 7)
            
            # Selling long on Liquidate
            for symbol, quantity in item.long_symbol_q:
                self.MarketOrder(symbol, -quantity)
                        
            # Buying short on Liquidate
            for symbol, quantity in item.short_symbol_q:
                self.MarketOrder(symbol, quantity)
            
            remove_item = item
        
        # Trade execution    
        if item.holding_period == 1: # All portfolios are held for six months (month 2 to 7)
            open_long_symbol_q:List[Tuple[Symbol, int]] = []
            open_short_symbol_q:List[Tuple[Symbol, int]] = []
            
            for symbol, quantity in item.long_symbol_q:
                if self.Securities[symbol].Price != 0 and self.Securities[symbol].IsTradable:
                    self.MarketOrder(symbol, quantity)
                    open_long_symbol_q.append((symbol, quantity))
                        
            for symbol, quantity in item.short_symbol_q:
                if self.Securities[symbol].Price != 0 and self.Securities[symbol].IsTradable:
                    self.MarketOrder(symbol, -quantity)
                    open_short_symbol_q.append((symbol, quantity))
            
            # Only opened orders will be closed        
            item.long_symbol_q = open_long_symbol_q
            item.short_symbol_q = open_short_symbol_q
            
        item.holding_period += 1
        
    # We need to remove closed part of portfolio after loop. Otherwise it will miss one item in self.managed_queue.
    if remove_item:
        self.managed_queue.remove(remove_item)
    
def Selection(self) -> None:
    self.selection_flag = True
def CalculateAccurals(self, current_accural_data, prev_accural_data):
    delta_assets:float = current_accural_data.CurrentAssets - prev_accural_data.CurrentAssets
    delta_cash:float = current_accural_data.CashAndCashEquivalents - prev_accural_data.CashAndCashEquivalents
    delta_liabilities:float = current_accural_data.CurrentLiabilities - prev_accural_data.CurrentLiabilities
    delta_debt:float = current_accural_data.CurrentDebt - prev_accural_data.CurrentDebt
    delta_tax:float = current_accural_data.IncomeTaxPayable - prev_accural_data.IncomeTaxPayable
    dep:float = current_accural_data.DepreciationAndAmortization
    avg_total:float = (current_accural_data.TotalAssets + prev_accural_data.TotalAssets) / 2
    
    bs_acc:float = ((delta_assets - delta_cash) - (delta_liabilities - delta_debt-delta_tax) - dep) / avg_total
    return bs_acc
