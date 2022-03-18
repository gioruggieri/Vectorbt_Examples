import vectorbt as vbt
import pandas as pd
import numpy as np
from datetime import datetime
from numba import njit
import talib


data = vbt.BinanceData.download(
    ['BTCUSDT'], 
    start='2021-09-01',
    end='2022-03-11',
    interval='1h'
)

high = data.get('High')
low = data.get('Low')
close = data.get('Close')


def get_basic_bands(med_price, atr, multiplier):
    matr = multiplier * atr
    upper = med_price + matr
    lower = med_price - matr
    return upper, lower

@njit
def get_final_bands_nb(close, upper, lower):
    trend = np.full(close.shape, np.nan)
    dir_ = np.full(close.shape, 1)
    long = np.full(close.shape, np.nan)
    short = np.full(close.shape, np.nan)

    for i in range(1, close.shape[0]):
        if close[i] > upper[i - 1]:
            dir_[i] = 1
        elif close[i] < lower[i - 1]:
            dir_[i] = -1
        else:
            dir_[i] = dir_[i - 1]
            if dir_[i] > 0 and lower[i] < lower[i - 1]:
                lower[i] = lower[i - 1]
            if dir_[i] < 0 and upper[i] > upper[i - 1]:
                upper[i] = upper[i - 1]

        if dir_[i] > 0:
            trend[i] = long[i] = lower[i]
        else:
            trend[i] = short[i] = upper[i]

    return trend, dir_, long, short

def faster_supertrend_talib(high, low, close, period=7, multiplier=3):
    high = high.flatten()
    low = low.flatten()
    close = close.flatten()
    avg_price = talib.MEDPRICE(high, low)
    atr = talib.ATR(high, low, close, period)
    upper, lower = get_basic_bands(avg_price, atr, multiplier)
    return get_final_bands_nb(close, upper, lower)

def theWorks(high, low, close, period,  period1,  period2, multiplier, multiplier1, multiplier2, ema_len, rsi_len):
    high = high.flatten()
    low = low.flatten()
    close = close.flatten()
    supert, superd, superl, supers = faster_supertrend_talib(high, low, close, period, multiplier)
    supert1, superd1, superl1, supers1 = faster_supertrend_talib(high, low, close, period1, multiplier1)    
    supert2, superd2, superl2, supers2 = faster_supertrend_talib(high, low, close, period2, multiplier2)
    ema = vbt.MA.run(close, window=ema_len, ewm = True, short_name='ema')
    rsi = vbt.RSI.run(close, window=rsi_len)
    superSupl = pd.DataFrame(np.sort(((np.array([superl, superl1, superl2])).transpose()))[:,1:2])
    superSups = pd.DataFrame(np.sort(((np.array([supers, supers1, supers2])).transpose()))[:,1:2])
    long = pd.DataFrame(close) > superSupl
    short = pd.DataFrame(close) < superSups
    longema = close > ema.ma
    shortema = close > ema.ma
    longrsi = rsi.rsi < 20
    shortrsi = rsi.rsi > 70
    entries = long.iloc[:, 0].values.tolist() and longema.tolist() and longrsi.tolist()
    exits = short.iloc[:, 0].values.tolist() and shortema.tolist() and shortrsi.tolist()
    return entries, exits

the_Works = vbt.IndicatorFactory(
    class_name='theWorks',
    short_name='tw',
    input_names=['high', 'low', 'close'],
    param_names=['period', 'period1', 'period2', 'multiplier', 'multiplier1', 'multiplier2', 'ema_len', 'rsi_len'],
    output_names=['entries', 'exits']
).from_apply_func(
    theWorks, 
    period=7,
    period1=8,
    period2=9,
    multiplier=3,
    multiplier1=4,
    multiplier2=5,
    ema_len=200,
    rsi_len=14,
    param_product=True #all combination, False no combination
)
 
periods = np.arange(50, 200, 50)
ema_lenght = np.arange(20,250,30)
rsi_lenght = np.arange(10, 20, 2)
tw = the_Works.run(high, low, close, period=periods, period1=periods, period2=periods, ema_len=ema_lenght, rsi_len=rsi_lenght)

pf = vbt.Portfolio.from_signals(
    close=close, 
    entries=tw.entries, 
    short_entries=tw.exits, 
    fees=0.001, # commission of 0.1%
    sl_stop=0.005, tp_stop = 0.01,
    freq='1h'
)
pf.stats()
metric = 'total_return'
perf = pf.deep_getattr(metric)
print(perf.idxmax())