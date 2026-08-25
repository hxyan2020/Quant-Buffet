# Original QuantConnect / library Python
# locale=en slug="cross-section-of-stock-returns-predicted-by-commitment-of-traders-information"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from functools import reduce
from typing import List, Dict, Tuple
from numpy import isnan
class CrossSectionOfStockReturnsPredictedByCommitmentOfTradersInformation(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100000)
    
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']	
    
    self.min_share_price:int = 5
    self.leverage:int = 5
    self.SIC_stocks = {}    # storing list of stocks symbols keyed by SIC code
    
    self.COT_tickers_SICs:List[Tuple[List]] = [
        (['QHG'], [1020, 1021, 3331]), # Copper
        (['QGC'], [1040, 1041]), # Gold
        (['QSI'], [1044]), # Silver
        (['QLB'], [2400]), # Lumber
        (['QGO', 'QCL'], [1310, 1311]), # Gas, Oil
        (['QPL', 'QPA'], [3449, 3491, 3492, 3493, 3494, 3495, 3496, 3497, 3498, 3499]), # Platinum, Palladium
    ]
    
    # create 1D list from SIC codes
    self.SIC_universe:List[int] = map(lambda x: x[1], self.COT_tickers_SICs)
    self.SIC_universe:List[int] = reduce(lambda x,y: x+y , self.SIC_universe)
    
    self.last_long_prop:Dict[str, None] = {
        'QHG': None,
        'QGC': None,
        'QSI': None,
        'QLB': None,
        'QGO': None,
        'QCL': None,
        'QPL': None,
        'QPA': None
    }
    
    # subscribe to COT data
    for cot_ticker, _ in self.last_long_prop.items():
        data = self.AddData(CommitmentsOfTraders, cot_ticker, Resolution.Daily)
        
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol, 0), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # selection on monthly basis
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    # filter all symbol of stocks
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price \
        and not isnan(x.AssetClassification.SIC != 0) and (x.AssetClassification.SIC != 0) \
        and (x.AssetClassification.SIC in self.SIC_universe) and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    
    selected_symbols:List[Symbol] = []
    # firstly clear stocks from old selection
    self.SIC_stocks.clear()
    
    # store relevant stocks symbols into their basket according to SIC code
    for stock in selected:
        symbol = stock.Symbol
        SIC_code = stock.AssetClassification.SIC
        
        # make sure list for stocks is initialized
        if SIC_code not in self.SIC_stocks:
            self.SIC_stocks[SIC_code] = []
        
        # add stock's symbol to it's basket based on SIC code
        self.SIC_stocks[SIC_code].append(symbol)
    
        selected_symbols.append(symbol)
        
    return selected_symbols
    
def OnData(self, data: Slice) -> None:
    COT_data_last_update_date:Dict[Symbol, datetime.date] = CommitmentsOfTraders.get_last_update_date()
    # storing tuples (SIC_list, long_proportion_growth_value)
    long_proportion_growth:List[Tuple[List, float]] = []
    rebalance_flag:bool = False
    
    for COT_ticker_list, SIC_list in self.COT_tickers_SICs:
        
        long_proportion_growth_values:List[float] = []
        
        for COT_ticker in COT_ticker_list:
            
            if self.Securities[COT_ticker].GetLastData() and self.Time.date()  0:
                long += self.SIC_stocks[SIC]
            else:
                short += self.SIC_stocks[SIC]
    
    return long, short
    
def Selection(self) -> None:
    self.selection_flag = True
# Commitments of Traders data.
# NOTE: IMPORTANT: Data order must be ascending (datewise).
# Data source: https://commitmentsoftraders.org/cot-data/
# Data description: https://commitmentsoftraders.org/wp-content/uploads/Static/CoTData/file_key.html
class CommitmentsOfTraders(PythonData):
_last_update_date:Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return CommitmentsOfTraders._last_update_date
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/futures/cot/{0}.PRN".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
# File example.
# DATE   OPEN     HIGH        LOW       CLOSE     VOLUME   OI
# ----   ----     ----        ---       -----     ------   --
# DATE   LARGE    SPECULATOR  COMMERCIAL HEDGER   SMALL TRADER
#        LONG     SHORT       LONG      SHORT     LONG     SHORT
def Reader(self, config, line, date, isLiveMode):
    data = CommitmentsOfTraders()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(',')
    
    # Prevent lookahead bias.
    data.Time = datetime.strptime(split[0], "%Y%m%d") + timedelta(days=1)
    
    data['LARGE_SPECULATOR_LONG'] = int(split[1])
    data['LARGE_SPECULATOR_SHORT'] = int(split[2])
    data['COMMERCIAL_HEDGER_LONG'] = int(split[3])
    data['COMMERCIAL_HEDGER_SHORT'] = int(split[4])
    data['SMALL_TRADER_LONG'] = int(split[5])
    data['SMALL_TRADER_SHORT'] = int(split[6])
    data.Value = int(split[1])
    if config.Symbol.Value not in CommitmentsOfTraders._last_update_date:
        CommitmentsOfTraders._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > CommitmentsOfTraders._last_update_date[config.Symbol.Value]:
        CommitmentsOfTraders._last_update_date[config.Symbol.Value] = data.Time.date()
    return data
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
