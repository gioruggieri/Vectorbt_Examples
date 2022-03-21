import vectorbt as vbt
import pandas as pd
import numpy as np
from datetime import datetime
from numba import njit
import talib


data = vbt.BinanceData.download(
    ['BTCUSDT'], 
    start='2022-03-01',
    end='2022-03-21',
    interval='1h'
)

high = data.get('High')
low = data.get('Low')
close = data.get('Close')

#average = input.string(title="Source MA Type", defval="EMA",options=["EMA","SMA"])
len = 27 # title="Source MA Length")
slopeFlen = 5
slopeSlen= 10

trendfilter=True # title="Trend Filter")
trendfilterperiod= 200 # title="Trend Filter MA Period")
#trendfiltertype=input.string(title="Trend Filter MA Type", defval="EMA",options=["EMA","SMA"])

volatilityfilter=False # title="Volatility Filter")
volatilitystdevlength= 20 # title="Vol Filter STDev Length")
volatilitystdevmalength= 30 #title="Vol Filter STDev MA Length")

# //variabili

# if average == "EMA":
def emaSlope(high, low, close, len = 27, 
             slopeFlen = 5, 
             slopeSlen= 10, 
             trendfilter=True, 
             trendfilterperiod= 200, 
             volatilityfilter=False,
             volatilitystdevlength= 20,
             volatilitystdevmalength= 30):

    out = vbt.MA.run(close,len, ewm=True)
    out = out.ma

    out.columns.names = (None,None)
    # else:
    #     out = vbt.MA.run(close,len)
        
    slp = out.shift()/out
    
    emaslopeF = vbt.MA.run(slp,slopeFlen, ewm=True)
    emaslopeS = vbt.MA.run(slp,slopeSlen, ewm=True)

    TrendConditionL = close>(vbt.MA.run(close,trendfilterperiod, ewm=True)).ma
    
    TrendConditionS = close<(vbt.MA.run(close,trendfilterperiod, ewm=True)).ma
       
    # VolatilityCondition=ta.stdev(close,volatilitystdevlength)>ta.sma(ta.stdev(close,volatilitystdevlength),volatilitystdevmalength)
    VolatilityCondition = talib.STDDEV(close.flatten(),volatilitystdevlength)>talib.SMA(talib.STDDEV(close.flatten(),volatilitystdevlength),volatilitystdevmalength)
    
    
    if trendfilter == True:
        if volatilityfilter == True:
            ConditionEntryL= (np.array(emaslopeF.ma.values.tolist()))>np.array(emaslopeS.ma.values.tolist()).tolist() and np.array(TrendConditionL.values.tolist()).tolist() and np.array(VolatilityCondition.values.tolist()).tolist()
        else:
            ConditionEntryL= (np.array(emaslopeF.ma.values.tolist())>np.array(emaslopeS.ma.values.tolist())).tolist() and np.array(TrendConditionL.values.tolist())    
    else:
        if volatilityfilter == True:
            ConditionEntryL= (np.array(emaslopeF.ma.values.tolist())>np.array(emaslopeS.ma.values.tolist())).tolist() and np.array(VolatilityCondition.values.tolist()).tolist()
        else:
            ConditionEntryL= np.array(emaslopeF.ma.values.tolist())>np.array(emaslopeS.ma.values.tolist())
    
    # Condizioni di entrata short
    if trendfilter == True:
        if volatilityfilter == True:
           ConditionEntryS= (np.array(emaslopeF.ma.values.tolist())<np.array(emaslopeS.ma.values.tolist())).tolist() and np.array(TrendConditionS.values.tolist()).tolist() and np.array(VolatilityCondition.values.tolist()).tolist()
        else: 
            ConditionEntryS= (np.array(emaslopeF.ma.values.tolist())<np.array(emaslopeS.ma.values.tolist())).tolist() and np.array(TrendConditionS.values.tolist()).tolist()
    else:
        if volatilityfilter == True:
            ConditionEntryS= (np.array(emaslopeF.ma.values.tolist())<np.array(emaslopeS.ma.values.tolist())).tolist() and np.array(VolatilityCondition.values.tolist()).tolist()
        else:
            ConditionEntryS= np.array(emaslopeF.ma.values.tolist())<np.array(emaslopeS.ma.values.tolist())
    
    # Condizioni di uscita
    ConditionExitL=emaslopeF.ma_crossed_below(emaslopeS)
    ConditionExitS=emaslopeF.ma_crossed_above(emaslopeF,emaslopeS)
    return ConditionEntryL, ConditionEntryS, ConditionExitL, ConditionExitS


ema_Slope = vbt.IndicatorFactory(
    class_name='emaSlope',
    short_name='eS',
    input_names=['high', 'low', 'close'],
    param_names=['len', 
             'slopeFlen', 
             'slopeSlen', 
             'trendfilter', 
             'trendfilterperiod', 
             'volatilityfilter',
             'volatilitystdevlength',
             'volatilitystdevmalength'],
    output_names=['ConditionEntryL', 'ConditionEntryS', 'ConditionExitL', 'ConditionExitS']
).from_apply_func(
    emaSlope,
    len = 27, 
    slopeFlen = 5, 
    slopeSlen= 10, 
    trendfilter=True, 
    trendfilterperiod= 200, 
    volatilityfilter=False,
    volatilitystdevlength= 20,
    volatilitystdevmalength= 30,
    param_product=True #all combination, False no combination
)

    
tw = ema_Slope.run(high, low, close, len = 27, 
                    slopeFlen = 5, 
                    slopeSlen= 10, 
                    trendfilter=True, 
                    trendfilterperiod= 200, 
                    volatilityfilter=False,
                    volatilitystdevlength= 20,
                    volatilitystdevmalength= 30)
    
  
pf = vbt.Portfolio.from_signals(
    close=close, 
    entries=tw.ConditionEntryL, 
    exits=tw.ConditionExitL,
    short_entries=tw.ConditionEntryS,
    short_exits=tw.ConditionExitS,
    fees=0.001, # commission of 0.1%
    sl_stop=0.005, tp_stop = 0.01,
    freq='1h'
)