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
    
    # //variabili accessorie e condizioni
    
    # if trendfiltertype == "EMA":
    #     close>ta.ema(close,trendfilterperiod)
    # else
    #     close>ta.sma(close,trendfilterperiod)
    # trendfiltertype == "EMA"
        
    # TrendConditionS=if trendfiltertype =="EMA"
    #     close<ta.ema(close,trendfilterperiod)
    # else
    #     close<ta.sma(close,trendfilterperiod)

    TrendConditionL = close>(vbt.MA.run(close,trendfilterperiod, ewm=True)).ma
    
    TrendConditionS = close<(vbt.MA.run(close,trendfilterperiod, ewm=True)).ma
       
    # VolatilityCondition=ta.stdev(close,volatilitystdevlength)>ta.sma(ta.stdev(close,volatilitystdevlength),volatilitystdevmalength)
    VolatilityCondition = talib.STDDEV(close.flatten(),volatilitystdevlength)>talib.SMA(talib.STDDEV(close.flatten(),volatilitystdevlength),volatilitystdevmalength)
    
    # Condizioni di entrata Long 
    
    # ConditionEntryL= if trendfilter == true
    #     if volatilityfilter == true
    #         emaslopeF>emaslopeS and TrendConditionL and VolatilityCondition
    #     else
    #         emaslopeF>emaslopeS and TrendConditionL
    # else
    #     if volatilityfilter == true
    #         emaslopeF>emaslopeS and VolatilityCondition
    #     else 
    #         emaslopeF>emaslopeS
    
    
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




# //plot

# plot (slp, color=color.white)
# plot (emaslopeF,color=color.yellow)
# plot (emaslopeS,color=color.red)

# //ingressi e uscite


# // INPUT VARIABILI

# TAKE_PROFIT = input.float(3.7, title="TAKE PROFIT 1",step = 0.01)
# TAKE_PROFIT_2=input.float(5.4, title="TAKE PROFIT 2",step = 0.01)
# STOP_LOSS = input.float(3.5,title="STOP LOSS",step = 0.01)


# useDateRange = input.bool(defval=true, title="Limit backtesting by date", group="Limit by date")
# rangeType = input.string(defval="Custom", title="Date range:", options=["Custom", "Today", "30 Days", "90 Days", "180 Days", "Year to Date"], group="Limit by date", tooltip="If set to other than custom, this overrides any set dates.")

# startDate = input.time(title="Start Date (YYYY/DD/MM)", defval=timestamp("1 Jan 2022 1:01 -0400"), group="Limit by date")
# endDate =   input.time(title="End Date (YYYY/DD/MM)  ",defval=timestamp("31 Dec 2100 19:59 -0400"), group="Limit by date", tooltip="You likely want to leave this far in the future.")

# // subtract number of days (in milliseconds) from current time
# startDate := rangeType == "Custom" ? startDate :
#      rangeType == "Today" ? timenow - (timenow-10) :   
#      rangeType == "30 Days" ? timenow - 2592000000 :   
#      rangeType == "90 Days" ? timenow - 7776000000 :    
#      rangeType == "180 Days" ? timenow - 15552000000 :
#      rangeType == "Year to Date" ? timestamp(syminfo.timezone, year(timenow), 01, 01, 00, 01) : na

# inDateRange = (time >= startDate) and (time < endDate)
# inDateRange := useDateRange ? inDateRange : 1



# //if ConditionExitS
#   //  if strategy.position_size < 0
#     //    strategy.close("SLPShort")

# //if ConditionExitL
#   //  if strategy.position_size > 0
#     //    strategy.close("SLPLong")

# //if ConditionEntryL
#   //  strategy.entry("SLPLong",strategy.long)
    
# //if ConditionEntryS
#   //  strategy.entry("SLPShort",strategy.short)
    

# if(inDateRange)

#     var price=0
    
#     if (ConditionExitS)
#         strategy.close("My Short Entry Id",qty_percent=100)
    
#     if (ConditionEntryL and strategy.opentrades==0)

#         tp=close+(close*TAKE_PROFIT/100)         
#         tp2=close+(close*TAKE_PROFIT_2/100)
#         sl=close-(close*STOP_LOSS/100)
#         OFFSET =1
#         tickerid=syminfo.mintick
        
        
#         float offsetTP = switch tickerid
#             0.00001 => offsetTP=(tp*OFFSET/100)*100000
#         	0.0001 => offsetTP=(tp*OFFSET/100)*10000
#             0.001 => offsetTP=(tp*OFFSET/100)*1000
#     	    0.01 => offsetTP=(tp*OFFSET/100)*100
#             0.1 => offsetTP=(tp*OFFSET/100)*10
            
#         strategy.entry("My Long Entry Id", strategy.long)
#         strategy.exit("My Long Exit Id", "My Long Entry Id", limit=tp , stop=sl ,qty_percent=50)
#         //strategy.exit("My Long Exit Id 2", "My Long Entry Id", limit=tp2 , stop=sl,qty_percent=100, trail_price=tp, trail_offset=offsetTP)
#         strategy.exit("My Long Exit Id 2", "My Long Entry Id", limit=tp2 , stop=sl ,qty_percent=100)
    
#     //5 CANDELE ROSSE DI FILA
#     fiveRedBar=(close[4] < open[4]) and (close[3] < open[3]) and (close[2] < open[2]) and (close[1] < open[1]) and (close < open) 
    
    
#     if (ConditionExitL or fiveRedBar)
#         strategy.close("My Long Entry Id",qty_percent=100)
        
#     if (ConditionEntryS and strategy.opentrades==0)
#         tp=close-(close*TAKE_PROFIT/100)  
#         tp2=close-(close*TAKE_PROFIT_2/100)
#         sl=close+(close*STOP_LOSS/100)
#         OFFSET = 1
#         tickerid=syminfo.mintick
        
#         float offsetTP = switch tickerid
#             0.00001 => offsetTP=(tp*OFFSET/100)*100000
#         	0.0001 => offsetTP=(tp*OFFSET/100)*10000
#             0.001 => offsetTP=(tp*OFFSET/100)*1000
#     	    0.01 => offsetTP=(tp*OFFSET/100)*100
#             0.1 => offsetTP=(tp*OFFSET/100)*10
            
          
#         strategy.entry("My Short Entry Id", strategy.short)
#         strategy.exit("My Short Exit Id", "My Short Entry Id", limit=tp , stop=sl ,qty_percent=50)
#         //strategy.exit("My Short Exit Id 2", "My Short Entry Id", limit=tp2 , stop=sl ,qty_percent=100, trail_price=tp, trail_offset=offsetTP)
#         strategy.exit("My Short Exit Id 2", "My Short Entry Id", limit=tp2 , stop=sl ,qty_percent=100)
    
    
