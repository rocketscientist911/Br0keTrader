import requests
import json
from datetime import datetime, timedelta
import pandas as pd

symbol = 'BTCBUSD'
interval = '30m'
max_trade_hours = 2
long_day_hour = ('Friday', 6)
short_day_hour = ('Friday', 4)
initial_balance = 1000
max_trade_amount = 30
max_stop_loss_pct = 1.1
max_leverage = 5
position_mode = 'CROSSED'

total_trades = 0
success_trades = 0
profit_loss = 0

while True:
    try:
        endpoint = 'https://api.binance.com/api/v3/klines'
        start_time = datetime.utcnow() - timedelta(hours=max_trade_hours*2)
        end_time = datetime.utcnow()
        start_time = int(start_time.timestamp() * 1000)
        end_time = int(end_time.timestamp() * 1000)
        payload = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_time,
            'endTime': end_time
        }
        response = requests.get(endpoint, params=payload)
        raw_data = json.loads(response.text)
        df = pd.DataFrame(raw_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.set_index('timestamp')
        df['obv'] = 0.0
        for i in range(1, len(df)):
            if df.loc[df.index[i], 'close'] > df.loc[df.index[i-1], 'close']:
                df.loc[df.index[i], 'obv'] = df.loc[df.index[i-1], 'obv'] + float(df.loc[df.index[i], 'volume'])
            elif df.loc[df.index[i], 'close'] < df.loc[df.index[i-1], 'close']:
                df.loc[df.index[i], 'obv'] = df.loc[df.index[i-1], 'obv'] - float(df.loc[df.index[i], 'volume'])
            else:
                df.loc[df.index[i], 'obv'] = df.loc[df.index[i-1], 'obv']

        utc_now = datetime.utcnow()
        utc_day = utc_now.strftime('%A')
        utc_hour = utc_now.hour

        if utc_day == long_day_hour[0] and utc_hour == long_day_hour[1]:
            if df.loc[df.index[-1], 'obv'] > df.loc[df.index[-2], 'obv']:
                entry_price = float(df.loc[df.index[-1], 'close'])
                trade_amount = min(max_trade_amount, initial_balance)
                stop_loss_price = entry_price * max_stop_loss_pct
                take_profit_price = entry_price * (1 + (trade_amount / initial_balance) * 0.01)
                leverage = min(max_leverage, int(initial_balance / trade_amount))
                if leverage == 0:
                    print('Skipping long trade: Insufficient balance to trade.')
                else:
                    endpoint = 'https://api.binance.com/api/v3/order'
                    payload = {
                        'symbol': symbol,
                        'side': 'BUY',
                        'type': 'MARKET',
                        'quoteOrderQty': trade_amount,
                        'newOrderRespType': 'FULL',
                        'timestamp': int(datetime.utcnow().timestamp() * 1000),
                        'leverage': leverage,
                        'positionSide': position_mode
                    }
                    response = requests.post(endpoint, params=payload)
                    result = json.loads(response.text)
                    if 'code' in result:
                        print('Failed to execute long trade: ' + result['msg'])
                    else:
                        print('Executed long trade: ' + str(result))
                        initial_balance = initial_balance - trade_amount
                        total_trades += 1
                        success_trades += 1
                        profit_loss += (1 - float(result['cummulativeQuoteQty']) / trade_amount) * 100

        elif utc_day == short_day_hour[0] and utc_hour == short_day_hour[1]:
            if df.loc[df.index[-1], 'obv'] < df.loc[df.index[-2], 'obv']:
                entry_price = float(df.loc[df.index[-1], 'close'])
                trade_amount = min(max_trade_amount, initial_balance)
                stop_loss_price = entry_price * (2 - max_stop_loss_pct)
                take_profit_price = entry_price * (1 - (trade_amount / initial_balance) * 0.01)
                leverage = min(max_leverage, int(initial_balance / trade_amount))
                if leverage == 0:
                    print('Skipping short trade: Insufficient balance to trade.')
                else:
                    endpoint = 'https://api.binance.com/api/v3/order'
                    payload = {
                        'symbol': symbol,
                        'side': 'SELL',
                        'type': 'MARKET',
                        'quoteOrderQty': trade_amount,
                        'newOrderRespType': 'FULL',
                        'timestamp': int(datetime.utcnow().timestamp() * 1000),
                        'leverage': leverage,
                        'positionSide': position_mode
                    }
                    response = requests.post(endpoint, params=payload)
                    result = json.loads(response.text)
                    if 'code' in result:
                        print('Failed to execute short trade: ' + result['msg'])
                    else:
                        print('Executed short trade: ' + str(result))
                        initial_balance = initial_balance + float(result['executedQty']) * float(result['avgPrice'])
                        total_trades += 1
                        success_trades += 1
                        profit_loss += (1 - float(result['cummulativeQuoteQty']) / trade_amount) * 100

        else:
            pass  # no trades executed at this time

        if total_trades > 0:
            print(f'Total Trades: {total_trades}, Success Trades: {success_trades}, '
                  f'Profit/Loss Percentage: {profit_loss/total_trades:.2f}%')

    except KeyboardInterrupt:
        print('\nExiting the script...')
        break

    except Exception as e:
        print(f'Error occurred: {e}. Retrying...')
        continue
