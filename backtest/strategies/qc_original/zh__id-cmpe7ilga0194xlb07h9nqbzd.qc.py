# Original QuantConnect / library Python
# locale=zh slug="趋势跟随与溢出效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
class TrendFollowingandSpilloverEﬀect(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    # Symbols - currency, index and bond futures.
    self.symbols = [
        ('CME_AD1', 'ASX_YAP1', 'ASX_XT1'),          # Australian Dollar Futures, Continuous Contract #1
        ('CME_BP1', 'LIFFE_Z1', 'LIFFE_R1'),         # British Pound Futures, Continuous Contract #1
        ('CME_CD1', 'LIFFE_FCE1', 'MX_CGB1'),        # Canadian Dollar Futures, Continuous Contract #1
        ('CME_EC1', 'EUREX_FSTX1', 'EUREX_FGBL1'),   # Euro FX Futures, Continuous Contract #1
        ('CME_JY1', 'SGX_NK1', 'SGX_JB1'),           # Japanese Yen Futures, Continuous Contract #1
        ('CME_DX1', 'CME_ES1', 'CME_TY1')           # US Dollar Index Futures, Continuous Contract #1
        # ('CME_SF1', 'EUREX_FSMI1', '')            # Swiss Franc Futures, Continuous Contract #1
        # ('CME_MP1', '', '')                       # Mexican Peso Futures, Continuous Contract #1
        # ('CME_NE1', '', '')                       # New Zealand Dollar Futures, Continuous Contract #
    ]
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # Daily ROC data.
    self.data = {}
   
    self.period = 36 * 21
    self.SetWarmUp(self.period)
    
    for futures_symbols in self.symbols:
        for symbol in futures_symbols:
            data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
            
            self.data[symbol] = SymbolData(self.period)
            
            data.SetFeeModel(CustomFeeModel())
            data.SetLeverage(5)
        
    self.rebalance_flag: bool = False
    self.Schedule.On(self.DateRules.WeekStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Rebalance)
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.

def OnData(self, data):
    for futures_symbols in self.symbols:
        for symbol in futures_symbols:
            if self.securities[symbol].get_last_data() and self.time.date() > QuantpediaFutures.get_last_update_date()[symbol]:
                self.liquidate(symbol)
                self.data[symbol].reset()
                continue
            if symbol in data and data[symbol]:
                price = data[symbol].Value
                self.data[symbol].update(price)
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    weight = {}
    traded_asset_classs_count = 0
    
    for futures_symbols in self.symbols:
        fx = futures_symbols[0]
        eq = futures_symbols[1]
        bond = futures_symbols[2]
        
        if self.data[fx].is_ready() and self.data[eq].is_ready() and self.data[bond].is_ready():
            fx_perf = self.data[fx].performance()
            eq_perf = self.data[eq].performance()
            bond_perf = self.data[bond].performance()
            
            bond_w = 0
            fx_w = 0
            eq_w = 0
            
            # Bonds have a negative eﬀect on FX and positive eﬀect on Equities
            bond_signum = np.sign(bond_perf)
            fx_w -= bond_signum
            eq_w += bond_signum
            
            # Equities have a negative eﬀect on Bonds and negative eﬀect on FX
            eq_signum = np.sign(eq_perf)
            bond_w -= eq_signum
            fx_w -= eq_signum
            
            # FX has a positive eﬀect on Equities and positive eﬀect on Bonds
            fx_signum = np.sign(fx_perf)
            eq_w += fx_signum
            bond_w += fx_signum
            # inverse volatility sum of traded symbols
            total_volatility = sum([ 1/self.data[x[0]].volatility() for x in [(fx,fx_w), (eq,eq_w), (bond, bond_w)] if x[1] != 0 ])
            
            # volatility weighting
            if total_volatility != 0:
                weight[fx] = ((1/self.data[fx].volatility()) / total_volatility) * np.sign(fx_w)
                weight[eq] = ((1/self.data[eq].volatility()) / total_volatility) * np.sign(eq_w)
                weight[bond] = ((1/self.data[bond].volatility()) / total_volatility) * np.sign(bond_w)
            
            traded_asset_classs_count += 1
        
    portfolio: List[PortfolioTarget] = []
    if traded_asset_classs_count != 0:
        weight_ratio = 1 / traded_asset_classs_count
        portfolio = [PortfolioTarget(symbol, weight_ratio * w) for symbol, w in weight.items() if data.contains_key(symbol) and data[symbol]]
    
    self.SetHoldings(portfolio, True)
def Rebalance(self):
    self.rebalance_flag = True
class SymbolData():
def __init__(self, period):
    self.price = RollingWindow[float](period)
    self.period = period
    
def update(self, value) -> None:
    self.price.Add(value)

def performance(self) -> float:
    result = self.price[0] / self.price[self.period-1] - 1
    return result
def volatility(self) -> float:
    prices = np.array([x for x in self.price][:60])
    result = prices[:-1] / prices[1:] - 1
    result = np.std(result) * np.sqrt(252)
    return result
    
def reset(self) -> None:
    self.price.reset()
def is_ready(self) -> bool:
    return self.price.IsReady
    
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
_last_update_date:Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return QuantpediaFutures._last_update_date
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/futures/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaFutures()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['back_adjusted'] = float(split[1])
    data['spliced'] = float(split[2])
    data.Value = float(split[1])
    if config.Symbol.Value not in QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol.Value]:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = data.Time.date()
    return data
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
