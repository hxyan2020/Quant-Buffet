# Original QuantConnect / library Python
# locale=en slug="using-intensity-of-book-to-market-to-identify-growth-premium"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from numpy import isnan
class UsingIntensityofBooktoMarkettoIdentifyGrowthPremium(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.rebalance_month:int = 4
    self.quantile:int = 5
    self.leverage:int = 5
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.weight:Dict[Symbol, float] = {}
    self.bm_data:Dict[Symbol, RollingWindow] = {}
    self.bm_period:int = 8
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.month:int = 12
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
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
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchange_codes and \
        not isnan(x.ValuationRatios.PBRatio) and x.ValuationRatios.PBRatio != 0 and not isnan(x.MarketCap) and x.MarketCap != 0
        ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # BM intensity.
    bm_intensity:Dict[Fundamental, float] = {}
    for stock in selected:
        symbol:Symbol = stock.Symbol
        # BM ratio calc
        if symbol not in self.bm_data:
            self.bm_data[symbol] = RollingWindow[float](self.bm_period)
        
        bm:float = 1. / stock.ValuationRatios.PBRatio
        
        if self.bm_data[symbol].IsReady:
            # Intensity calc.
            bms:List[float] = list(self.bm_data[symbol])
            avg_bm:float = np.mean(bms)
            std_bm:float = np.std(bms)
            intensity:float = (bm - avg_bm) / std_bm
            
            bm_intensity[stock] = intensity
            
        self.bm_data[symbol].Add(bm)
    
    if len(bm_intensity) >= self.quantile ** 2:
        # Market cap sorting
        sorted_by_market_cap = sorted(bm_intensity.items(), key = lambda x: x[0].MarketCap, reverse = True)
        quantile:int = int(len(sorted_by_market_cap) / self.quantile)
        top_by_market_cap:List = [x for x in sorted_by_market_cap[:quantile]]
        # Intensity sorting
        sorted_by_intesity:List = sorted(top_by_market_cap, key = lambda x: x[1], reverse = True)
        quantile = int(len(sorted_by_intesity) / self.quantile)
        short:List[Fundamental] = [x[0] for x in sorted_by_intesity[:quantile]]
        long:List[Fundamental] = [x[0] for x in sorted_by_intesity[-quantile:]]
        # Market cap weighting.
        for i, portfolio in enumerate([long, short]):
            mc_sum:float = sum(map(lambda x: x.MarketCap, portfolio))
            for stock in portfolio:
                self.weight[stock.Symbol] = ((-1) ** i) * stock.MarketCap / mc_sum
    return list(self.weight.keys())
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
def Selection(self) -> None:
    self.selection_flag = True
    if self.month % 3 == 0:
        self.selection_flag = True

    self.month += 1
    if self.month > 12:
        self.month = 1
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
