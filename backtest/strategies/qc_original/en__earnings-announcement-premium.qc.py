# Original QuantConnect / library Python
# locale=en slug="earnings-announcement-premium"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from collections import deque
from AlgoLib import *
from typing import List, Dict, Tuple

class EarningsAnnouncementPremium(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000) 

    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.period:int = 21
    self.month_period:int = 48
    self.leverage:int = 10
    self.quantile:int = 5
    self.selection_sorting_key = lambda x: x.MarketCap

    # Volume daily data.
    self.data:Dict[Symbol, RollingWindow[float]] = {}

    # Volume monthly data.
    self.monthly_volume:Dict[Symbol, float] = {}

    self.fundamental_count:int = 3000
    self.weight:Dict[Symbol, float] = {}
    
    self.selection_flag:bool = True
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].Add(stock.Volume)
        
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0 and \
                ((x.SecurityReference.ExchangeId == "NYS") or (x.SecurityReference.ExchangeId == "NAS") or (x.SecurityReference.ExchangeId == "ASE"))]
    
    if len(selected) > self.fundamental_count:
        selected = [x
            for x in sorted([x for x in selected], key = self.selection_sorting_key, reverse = True)[:self.fundamental_count]]
            
    fine_symbols:List[Symbol] = [x.Symbol for x in selected]

    volume_concentration_ratio:Dict[Fundamental, float] = {}

    # Warmup volume rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        # Warmup data.
        if symbol not in self.data:
            self.data[symbol] = RollingWindow[float](self.period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Debug(f"No history for {symbol} yet")
                continue
            if 'volume' not in history.columns:
                continue
            volumes:Series = history.loc[symbol].volume
            for _, volume in volumes.items():
                self.data[symbol].Add(volume)
        
        # Ratio/market cap pair.
        if not self.data[symbol].IsReady:
            continue

        if symbol not in self.monthly_volume:
            self.monthly_volume[symbol] = deque(maxlen = self.month_period)

        monthly_vol:float = sum([x for x in self.data[symbol]])
        last_month_date:datetime = self.Time - timedelta(days = self.Time.day)
        last_file_date:datetime = stock.EarningReports.FileDate.Value # stock annoucement day
        was_announcement_month:Tuple[int] = (last_file_date.year == last_month_date.year and last_file_date.month == last_month_date.month)    # Last month was announcement date.
        self.monthly_volume[symbol].append(VolumeData(last_month_date, monthly_vol, was_announcement_month))
        
        # 48 months of volume data is ready.
        if len(self.monthly_volume[symbol]) == self.monthly_volume[symbol].maxlen:
            # Volume concentration ratio calc.
            announcement_count:int = 12
            announcement_volumes:List[float] = [x.Volume for x in self.monthly_volume[symbol] if x.WasAnnouncementMonth][-announcement_count:]

            if len(announcement_volumes) == announcement_count:
                announcement_months_volume:float = sum(announcement_volumes)
                total_volume:float = sum([x.Volume for x in self.monthly_volume[symbol]])
                
                if announcement_months_volume != 0 and total_volume != 0:
                    # Store ratio, market cap pair.
                    volume_concentration_ratio[stock] = announcement_months_volume / total_volume
    
    # Volume sorting.
    if len(volume_concentration_ratio) > self.quantile:
        sorted_by_volume:List[Tuple[Fundamental, float]] = sorted(volume_concentration_ratio.items(), key = lambda x: x[1], reverse=True)
        quintile:int = int(len(sorted_by_volume) / self.quantile)
        high_volume:List[Fundamental] = [x[0] for x in sorted_by_volume[:quintile]]
            
        # Filering announcers and non-announcers.
        month_to_lookup:int = self.Time.month
        year_to_lookup:int = self.Time.year - 1
            
        long:List[Fundamental] = []
        short:List[Fundamental] = []
        for stock in high_volume:
            symbol:Symbol = stock.Symbol
            
            announcement_dates:List[List[int]] = [[x.Date.year, x.Date.month] for x in self.monthly_volume[symbol] if x.WasAnnouncementMonth]
            if [year_to_lookup, month_to_lookup] in announcement_dates:
                long.append(stock)
            else:
                short.append(stock)

        # Delete not updated symbols.
        symbols_to_remove:List[Symbol] = []
        for symbol in self.monthly_volume:
            if symbol not in fine_symbols:
                symbols_to_remove.append(symbol)
        for symbol in symbols_to_remove:
            del self.monthly_volume[symbol]
            
        # Market cap weighting.
        for i, portfolio in enumerate([long, short]):
            mc_sum:float = sum(list(map(lambda stock: stock.MarketCap , portfolio)))
            for stock in portfolio:
                self.weight[stock.Symbol] = (((-1)**i) * stock.MarketCap / mc_sum)

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

# Monthly volume data.
class VolumeData():
def __init__(self, date, monthly_volume, was_announcement_month):
    self.Date = date
    self.Volume = monthly_volume
    self.WasAnnouncementMonth = was_announcement_month

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
