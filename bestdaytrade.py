#!/usr/bin/env python3

import sys
import pandas as pd
import numpy as np
import requests
import json
import talib
from datetime import datetime, timedelta

if len(sys.argv) < 2:
    print("Usage: python3 script.py <currency_pair>")
    sys.exit(1)

symbol = sys.argv[1]
interval = '30m'
since = int((datetime.now() - timedelta(days=365*2)).timestamp() * 1000)
initial_balance = 1000
trade_size = 50
leverage = 15

url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&startTime={since}'
response = requests.get(url)
data = json.loads(response.text)

df = pd.DataFrame(data)
df.columns = ['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time', 'Quote_asset_volume', 'Number_of_trades', 'Taker_buy_base_asset_volume', 'Taker_buy_quote_asset_volume', 'Ignore']
df['Open_time'] = pd.to_datetime(df['Open_time'], unit='ms')
df['Close_time'] = pd.to_datetime(df['Close_time'], unit='ms')
df.set_index('Open_time', inplace=True)
for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
    df[col] = df[col].astype(float)

df['OBV'] = talib.OBV(df['Close'], df['Volume'])
df['OBV_EMA'] = talib.EMA(df['OBV'], timeperiod=2 * 60 // int(interval.rstrip('m')))

df['Signal'] = np.where(df['OBV'] > df['OBV_EMA'], 1, 0)
df['Position'] = df['Signal'].diff()

df['Profit'] = np.where(df['Position'] == 1, df['Close'].shift(-1) - df['Close'], 0)

df['Value'] = initial_balance + df['Profit'].cumsum()

df['Position USDT'] = np.where(df['Position'] == 1, trade_size * leverage, np.where(df['Position'] == -1, -trade_size * leverage, 0))

df['Margin Balance'] = df['Value'] + df['Position USDT']

df['Day'] = df.index.day
df['Hour'] = df.index.hour
df['Weekday'] = df.index.strftime('%A')
grouped_data = df.groupby(['Weekday', 'Hour']).agg({'Profit': 'sum', 'Position': 'sum', 'Position USDT': 'sum', 'Margin Balance': 'last'})

grouped_data['Win Rate'] = grouped_data['Profit'] / grouped_data['Position']
grouped_data['Win Rate'].replace(np.nan, 0, inplace=True)
grouped_data['Profit per Trade'] = grouped_data['Profit'] / (grouped_data['Position'] / 2)

most_profitable_long = grouped_data[grouped_data['Profit'] > 0]['Profit per Trade'].idxmax()
most_profitable_short = grouped_data[grouped_data['Profit'] < 0]['Profit per Trade'].idxmin()

weekday_data = grouped_data.reset_index().groupby('Weekday').agg({'Profit': 'sum', 'Position': 'sum', 'Position USDT': 'sum', 'Margin Balance': 'last', 'Win Rate': 'mean', 'Profit per Trade': 'mean'})

most_profitable_day = weekday_data['Profit'].div(initial_balance).sort_values(ascending=False).index[0]
most_profitable_day_profit = weekday_data.loc[most_profitable_day, 'Profit']
most_profitable_day_profit_pct = most_profitable_day_profit / initial_balance * 100


print('Most Profitable Day and Hour for Long Trades:', most_profitable_long)
print('Most Profitable Day and Hour for Short Trades:', most_profitable_short)
print('Most Profitable Day for Trades:', most_profitable_day, f'(Profit: {most_profitable_day_profit_pct:.2f}%)')

print('------------')

print('Weekday Analysis:')
print(weekday_data)

grouped_data.to_csv(f'{symbol}_day_hour_analysis.csv')
weekday_data.to_csv(f'{symbol}_weekday_analysis.csv')
