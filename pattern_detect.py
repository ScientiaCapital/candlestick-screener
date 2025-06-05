import ta
import yfinance as yf

data = yf.download("SPY", start="2020-01-01", end="2020-08-01")

morning_star = ta.pattern.CDL_MORNINGSTAR(data)

engulfing = ta.pattern.CDL_ENGULFING(data)

data['Morning Star'] = morning_star
data['Engulfing'] = engulfing

engulfing_days = data[data['Engulfing'] != 0]

print(engulfing_days)