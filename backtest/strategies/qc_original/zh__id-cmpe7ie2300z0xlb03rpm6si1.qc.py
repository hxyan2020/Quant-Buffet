# Original QuantConnect / library Python
# locale=zh slug="增强型套息策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import data_tools
from AlgorithmImports import *
from itertools import combinations
from numpy.linalg import inv
from scipy import stats
class CarryOnEnhancedCarryStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2002, 1, 1)
    self.SetCash(100000)
    
    # Source: https://www.quandl.com/data/OECD-Organisation-for-Economic-Co-operation-and-Development
    # NOTE: interest rate quandl data is available only once a month
    self.symbols = {
        "CME_AD1" : "IR3TIB01AUM156N",   # Australian Dollar Futures, Continuous Contract #1
        "CME_CD1" : "IR3TIB01CAM156N",   # Canadian Dollar Futures, Continuous Contract #1
        "CME_EC1" : "IR3TIB01EZM156N",   # Euro FX Futures, Continuous Contract #1
        "CME_JY1" : "IR3TIB01JPM156N",   # Japanese Yen Futures, Continuous Contract #1  # IR data since 2002
        "CME_MP1" : "IR3TIB01MXM156N",   # Mexican Peso Futures, Continuous Contract #1
        "CME_NE1" : "IR3TIB01NZM156N",   # New Zealand Dollar Futures, Continuous Contract #1  # price data since 2006
        "CME_SF1" : "IR3TIB01CHM156N"    # Swiss Franc Futures, Continuous Contract #1
    }
    
    self.leverage:int = 10
    self.volatility_period:int = 2 * 12 * 21
    self.performance_period:int = 3 * 12 * 21
    self.data = {}
    self.SetWarmUp(self.performance_period, Resolution.Daily)
    self.top_diff_pairs_cnt:int = 19  # number of pairs with top interest rate difference to pick
    self.top_vol_pairs_cnt:int = 6    # number of pairs with top volatility to pick
    
    turbulance_sma_period:int = 30
    turbulance_sma_hist_period:int = 3*12*21
    self.turbulance_sma: SimpleMovingAverage = SimpleMovingAverage(turbulance_sma_period)
    self.turbulance_sma_history: RollingWindow = RollingWindow[float](turbulance_sma_hist_period)
    
    for symbol, rate_symbol in self.symbols.items():
        self.AddData(data_tools.InterestRate3M, rate_symbol, Resolution.Daily)
        data = self.AddData(data_tools.QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        
        self.data[symbol] = data_tools.SymbolData(self.volatility_period, self.performance_period)
    
    # construct currency pairs
    symbols = list(self.symbols.keys())
    self.pairs = list(combinations(symbols, 2))
    
    self.rebalance_flag = False
    self.Schedule.On(self.DateRules.MonthEnd(symbols[0]), self.TimeRules.At(0, 0), self.Rebalance)

def Rebalance(self) -> None:
    self.rebalance_flag = True
    
def OnData(self, data: Slice) -> None:
    ir_last_update_date:Dict[str, datetime.date] = data_tools.InterestRate3M.get_last_update_date()
    qp_futures_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()
    symbols_to_delete:List[str] = []
    # data is still coming in
    if all([self.Securities[x].GetLastData() for x in self.symbols.keys()]) and any([self.Time.date() >= qp_futures_last_update_date[x] for x in self.symbols.keys()]) \
        and all([self.Securities[x].GetLastData() for x in self.symbols.values()]) and any([self.Time.date() >= ir_last_update_date[x] for x in self.symbols.values()]):
        self.Liquidate()
        return
    # store daily data
    for symbol, ir in self.symbols.items():
        if symbol in data and data[symbol]:
            price = data[symbol].Value
            self.data[symbol].update_price(price)
    
    if self.IsWarmingUp: return
    
    carry_weight = None
    
    S_dict = { x : self.data[x].daily_performance() for x in self.symbols if self.data[x].is_ready() }
    # data for every symbol is ready
    if len(S_dict) == len(self.symbols):
        # turbulance calculation
        y = np.array([[ self.data[x].abs_performance() for x in self.symbols ]]) # row vector
        u = np.array([[ self.data[x].avg_performance() for x in self.symbols ]]) # row vector
        A = y - u
        A_t = np.transpose(A)
        S = inv(pd.DataFrame(S_dict).cov())
        N = len(S_dict)
        t_ = np.dot(np.dot(A, S), A_t)
        turbulance = (t_ / N)[0][0]
        
        # update turbulance SMA indicator daily
        self.turbulance_sma.Update(self.Time, turbulance)
        
        # turbulance SMA is ready
        if self.turbulance_sma.IsReady:
            turb_sma = self.turbulance_sma.Current.Value
            # update turbulance SMA history
            self.turbulance_sma_history.Add(turb_sma)
            
            # turbulance SMA history is ready
            if self.turbulance_sma_history.IsReady:
                # percent rank of moving average versus its five-year history
                percentile_score = stats.percentileofscore([x for x in self.turbulance_sma_history][1:], turb_sma)
                
                # floor to nearest 20 score
                percent_rank_floored = math.floor(percentile_score / 20) * 20
                
                # assign carry strategy weight
                if percent_rank_floored == 0:
                    carry_weight = 1
                elif percent_rank_floored == 20:
                    carry_weight = .75
                elif percent_rank_floored == 40:
                    carry_weight = .5
                elif percent_rank_floored == 60:
                    carry_weight = .25
                elif percent_rank_floored == 80:
                    carry_weight = 0
                    
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    
    # carry weight is not set
    if not carry_weight:
        return

    # calculate interest rate differentials and align each currency pair such 
    # that a long position corresponds to a positive interest rate differential
    ir_diff_pos = {
        x : data[self.symbols[x[0]]].Value - data[self.symbols[x[1]]].Value
        for x in self.pairs if 
        self.symbols[x[0]] in data and data[self.symbols[x[0]]] and
        self.symbols[x[1]] in data and data[self.symbols[x[1]]] and
        data[self.symbols[x[0]]].Value >= data[self.symbols[x[1]]].Value
    }
    ir_diff_neg = {
        (x[1], x[0]) : data[self.symbols[x[1]]].Value - data[self.symbols[x[0]]].Value
        for x in self.pairs if 
        self.symbols[x[0]] in data and data[self.symbols[x[0]]] and
        self.symbols[x[1]] in data and data[self.symbols[x[1]]] and
        data[self.symbols[x[0]]].Value = self.top_diff_pairs_cnt:
        pair_volatility = { x : (self.data[x[0]].volatility() + self.data[x[1]].volatility()) / 2 for x in interest_rate_diff   \
                            if x[0] in self.data and x[1] in self.data and self.data[x[0]].is_ready() and self.data[x[1]].is_ready() }
        
        # sort pairs by currency interest rate difference
        sorted_by_diff = sorted(interest_rate_diff.items(), key = lambda x:x[1], reverse=True)
        top_by_diff = [x[0] for x in sorted_by_diff[:self.top_diff_pairs_cnt]]
        
        # sort pairs by volatility
        sorted_by_vol = sorted([x for x in top_by_diff if x in pair_volatility], key = lambda x:pair_volatility[x], reverse=True)
        if len(sorted_by_vol) >= self.top_vol_pairs_cnt:
            top_by_vol = [x for x in sorted_by_vol[:self.top_vol_pairs_cnt]]
            
            # trade carry strategy
            self.Liquidate()
            
            equity_used = self.Portfolio.TotalPortfolioValue * carry_weight
            pair_count = len(top_by_vol)
            for pair in top_by_vol:
                # calculate traded quantity
                q1 = equity_used / pair_count / self.data[pair[0]].recent_price()
                q2 = equity_used / pair_count / self.data[pair[1]].recent_price()
                self.MarketOrder(pair[0], q1)
                self.MarketOrder(pair[1], -q2)
