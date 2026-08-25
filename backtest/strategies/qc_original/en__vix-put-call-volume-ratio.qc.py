# Original QuantConnect / library Python
# locale=en slug="vix-put-call-volume-ratio"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# endregion

class VIXPutCallVolumeRatio(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    
    self.min_expiry = 25
    self.max_expiry = 35
    
    self.period = 21 * 3                # need n daily volumes
    self.min_period_len = 14            # need at least m minute volumes to calculate daily volume
    self.max_missing_days = 5

    self.threshold = 0.75

    self.current_day = -1

    # subscribe to VIX
    security = self.AddIndex('VIX', Resolution.Minute)
    
    # change normalization to raw to allow adding etf contracts
    security.SetDataNormalizationMode(DataNormalizationMode.Raw)
    # set fee model and leverage
    security.SetFeeModel(CustomFeeModel())
    security.SetLeverage(5)
    
    self.vix_symbol = security.Symbol

    self.vix_data = SymbolData(self.period)
    self.subscribed_vix_contracts = None

    # subscribe to Quantpedia future vix contract
    security = self.AddData(QuantpediaFutures, 'CBOE_VX1', Resolution.Daily)
    security.SetFeeModel(CustomFeeModel())
    security.SetLeverage(5)

    self.last_quantpedia_VIX_date = None
    self.quantpedia_VIX_symbol = security.Symbol
    
def OnData(self, data):
    curr_date = self.Time.date()

    # track quantpedia VIX data
    if self.quantpedia_VIX_symbol in data and data[self.quantpedia_VIX_symbol]:
        self.last_quantpedia_VIX_date = curr_date

    # trade on open
    if self.current_day != self.Time.day:
        self.Liquidate()

        # options volumes data has to be ready and quantpedia VIX data has to be still coming
        if self.vix_data.daily_volumes_ready() and (self.last_quantpedia_VIX_date - curr_date).days  self.threshold:
                self.SetHoldings(self.quantpedia_VIX_symbol, -1)

        self.current_day = self.Time.day

    if self.subscribed_vix_contracts is not None:
        # check contracts expirations
        if self.subscribed_vix_contracts.expiry_date - timedelta(days=1)  0 and underlying_price != 0:
            atm_strike = min(strikes, key=lambda x: abs(x-underlying_price))
            itm_strike = min(strikes, key=lambda x: abs(x-(underlying_price*0.95)))
            otm_strike = min(strikes, key=lambda x: abs(x-(underlying_price*1.05)))
            
            # filter calls and puts contracts with one month expiry
            atm_calls, atm_puts = self.FilterContracts(atm_strike, contracts, underlying_price)
            itm_calls, itm_puts = self.FilterContracts(itm_strike, contracts, underlying_price)
            otm_calls, otm_puts = self.FilterContracts(otm_strike, contracts, underlying_price)
            
            # make sure, there is at least one call and put contract
            if len(atm_calls) > 0 and len(atm_puts) > 0 and len(itm_calls) > 0 and len(itm_puts) > 0 and len(otm_calls) > 0 and len(otm_puts) > 0:
                # sort by expiry
                atm_call, atm_put = self.SortByExpiry(atm_calls, atm_puts)
                itm_call, itm_put = self.SortByExpiry(itm_calls, itm_puts)
                otm_call, otm_put = self.SortByExpiry(otm_calls, otm_puts)
                
                atm_call_subscriptions = self.SubscriptionManager.SubscriptionDataConfigService.GetSubscriptionDataConfigs(atm_call.Underlying)
                
                # check if stock's call and put contract was successfully subscribed
                if atm_call_subscriptions:
                    selected_contracts = [atm_call, atm_put, itm_call, itm_put, otm_call, otm_put]
                    
                    for contract in selected_contracts:
                        # add contract
                        self.AddOptionContract(contract, Resolution.Minute)
                        
                    # retrieve expiry date for contracts
                    expiry_date = atm_call.ID.Date.date() if atm_call.ID.Date.date()  max_missing_days:
        # reset rollingwindow, when there is a big gap between storing daily volumes
        self.options_daily_volumes.Reset()

    self.options_daily_volumes.Add(sum(self.options_minute_volumes))
    self.last_update_daily_volumes = curr_date
    self.options_minute_volumes.clear()

def z_score(self):
    daily_volumes = [x for x in self.options_daily_volumes]

    last_daily_volumes = daily_volumes[0]

    return (last_daily_volumes - np.mean(daily_volumes)) / np.std(daily_volumes)
    
def daily_volumes_ready(self):
    return self.options_daily_volumes.IsReady
    
def minute_volumes_ready(self, period):
    return len(self.options_minute_volumes) >= period

class Contracts():
def __init__(self, expiry_date, underlying_price, contracts):
    self.expiry_date = expiry_date
    self.underlying_price = underlying_price
    self.contracts = contracts
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))

# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
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

    return data
