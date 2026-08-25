# Original QuantConnect / library Python
# locale=en slug="安东纳奇的双重动量策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion

class AntonaccisDualMomentum(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)  
    self.SetCash(100000)
    
    period:int = 12 * 21
    self.SetWarmUp(period, Resolution.Daily)

    self.treasury_bill:Symbol = self.AddEquity("BIL", Resolution.Daily).Symbol

    # subscribe assets for each module
    self.equities:List[Symbol] = [self.AddEquity(x, Resolution.Daily).Symbol for x in ["SPY", "EFA"]]
    self.bonds:List[Symbol] = [self.AddEquity(x, Resolution.Daily).Symbol for x in ["HYG", "LQD"]]
    self.reits:List[Symbol] = [self.AddEquity(x, Resolution.Daily).Symbol for x in ["MBB", "VNQ"]]
    self.commodities:List[Symbol] = [self.AddEquity(x, Resolution.Daily).Symbol for x in ["TLT", "GLD"]]

    # traded modules
    self.modules:List[List[Symbol]] = [self.equities, self.bonds, self.reits, self.commodities]

    self.momentum:dict[Symbol, RateOfChange] = {}

    self.momentum_treshold:float = 0.

    for module in self.modules:
        for asset in module:
            # subscribe ROC indicator
            self.momentum[asset] = self.ROC(asset, period, Resolution.Daily)

    self.recent_month:int = -1

def OnData(self, data:Slice) -> None:
    if self.IsWarmingUp: return

    # monthly rebalance
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    
    tbill_allocation_count:int = 0
    long:List[Symbol] = []

    for module_index, module in enumerate(self.modules):
        if all(self.momentum[x].IsReady for x in module):
            # select and buy the better-performing asset as representative of the module
            module_perf_values:List[float] = [self.momentum[x].Current.Value for x in module]
            max_module_perf:float = max(module_perf_values)
            best_performing_asset:Symbol = module[module_perf_values.index(max_module_perf)]

            if max_module_perf > self.momentum_treshold:
                long.append(best_performing_asset)
            else:
                tbill_allocation_count += 1
    
    # tbill allocation weight relative to total number of modules with ROC data ready
    traded_asset_count:int = (tbill_allocation_count + len(long))
    tbill_allocation:float = tbill_allocation_count / traded_asset_count if traded_asset_count != 0 else 0

    # liquidate
    invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + [self.treasury_bill]:
            self.Liquidate(symbol)

    # trade etfs
    for symbol in long:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, 1 / traded_asset_count)
    
    # trade tbills
    if self.treasury_bill in data and data[self.treasury_bill]:
        self.SetHoldings(self.treasury_bill, tbill_allocation)
