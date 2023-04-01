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

api_key = '<your testnet API key>'
api_secret = '<your testnet API secret>'

endpoint = 'https://testnet.binance.vision/api/v3/klines'
endpoint = 'https://testnet.binance.vision/api/v3/order'

def generate_signature(data):
    import hmac
    import hashlib
    return hmac.new(api_secret.encode(), data.encode(), hashlib.sha256).hexdigest()

  while True:
    try:
        # Get historical trading data for specified time interval
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

        # Check if it's time to execute a trade
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
                    print('Simulated long trade executed')
                    initial_balance = initial_balance - trade_amount
                    total_trades += 1
                    success_trades += 1
                    profit_loss += (1 - trade_amount / initial_balance) * 100

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
                    print('Simulated short trade executed')
                    initial_balance = initial_balance + trade_amount * entry_price / take_profit_price
                    total_trades += 1
                    success_trades += 1
                    profit_loss += (1 - trade_amount / initial_balance) * 100

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
        
if leverage == 0:
    print('Skipping long trade: Insufficient balance to trade.')
else:
    print('Simulated long trade executed')
    # Generate the signature for the request
    data = f'symbol={symbol}&side=BUY&type=MARKET&quoteOrderQty={trade_amount}&timestamp={int(datetime.utcnow().timestamp() * 1000)}'
    signature = generate_signature(data)
    # Send the request with the API key and signature
    endpoint = 'https://testnet.binance.vision/api/v3/order'
    payload = {
        'symbol': symbol,
        'side': 'BUY',
        'type': 'MARKET',
        'quoteOrderQty': trade_amount,
        'newOrderRespType': 'FULL',
        'timestamp': int(datetime.utcnow().timestamp() * 1000),
        'leverage': leverage,
        'positionSide': position_mode,
        'recvWindow': 5000,
        'signature': signature,
    }
    headers = {
        'X-MBX-APIKEY': api_key
    }
    
      response = requests.post(endpoint, params=payload, headers=headers)
    result = json.loads(response.text)
    if 'code' in result:
        print('Failed to execute long trade: ' + result['msg'])
    else:
        initial_balance = initial_balance - trade_amount
        total_trades += 1
        success_trades += 1
        profit_loss += (1 - float(result['cummulativeQuoteQty']) / trade_amount) * 100
if leverage == 0:
    print('Skipping short trade: Insufficient balance to trade.')
else:
    print('Simulated short trade executed')
    # Generate the signature for the request
    data = f'symbol={symbol}&side=SELL&type=MARKET&quoteOrderQty={trade_amount}&timestamp={int(datetime.utcnow().timestamp() * 1000)}'
    signature = generate_signature(data)
    # Send the request with the API key and signature
    endpoint = 'https://testnet.binance.vision/api/v3/order'
    payload = {
        'symbol': symbol,
        'side': 'SELL',
        'type': 'MARKET',
        'quoteOrderQty': trade_amount,
        'newOrderRespType': 'FULL',
        'timestamp': int(datetime.utcnow().timestamp() * 1000),
        'leverage': leverage,
        'positionSide': position_mode,
        'recvWindow': 5000,
        'signature': signature,
    }
    headers = {
        'X-MBX-APIKEY': api_key
    }
    response = requests.post(endpoint, params=payload, headers=headers)
    result = json.loads(response.text)
    if 'code' in result:
        print('Failed to execute short trade: ' + result['msg'])
    else:
        initial_balance = initial_balance + trade_amount * float(result['avgPrice'])
        total_trades += 1
        success_trades += 1
        profit_loss += (1 - float(result['cummulativeQuoteQty']) / trade_amount) * 100
if leverage == 0:
    print('Skipping long trade: Insufficient balance to trade.')
else:
    # Calculate the maximum trade amount based on the available balance and leverage
    max_trade_amount = min(initial_balance / leverage, max_trade_amount)
    # Calculate the trade amount as a percentage of the available balance
    trade_amount = min(max_trade_amount, initial_balance)
    print('Simulated long trade executed')
    # Generate the signature for the request
    data = f'symbol={symbol}&side=BUY&type=MARKET&quoteOrderQty={trade_amount}&timestamp={int(datetime.utcnow().timestamp() * 1000)}'
    signature = generate_signature(data)
    # Send the request with the API key and signature
    endpoint = 'https://testnet.binance.vision/api/v3/order'
    payload = {
        'symbol': symbol,
        'side': 'BUY',
        'type': 'MARKET',
        'quoteOrderQty': trade_amount,
        'newOrderRespType': 'FULL',
        'timestamp': int(datetime.utcnow().timestamp() * 1000),
        'leverage': leverage,
        'positionSide': position_mode,
        'recvWindow': 5000,
        'signature': signature,
    }
    headers = {
        'X-MBX-APIKEY': api_key
    }
    response = requests.post(endpoint, params=payload, headers=headers)
    result = json.loads(response.text)
    if 'code' in result:
        print('Failed to execute long trade: ' + result['msg'])
    else:
        initial_balance = initial_balance - trade_amount
        total_trades += 1
        success_trades += 1
        profit_loss += (1 - float(result['cummulativeQuoteQty']) / trade_amount) * 100
if leverage == 0:
    print('Skipping short trade: Insufficient balance to trade.')
else:
    # Calculate the maximum trade amount based on the available balance and leverage
    max_trade_amount = min(initial_balance / leverage, max_trade_amount)
    # Calculate the trade amount as a percentage of the available balance
    trade_amount = min(max_trade_amount, initial_balance)
    print('Simulated short trade executed')
    # Generate the signature for the request
    data = f'symbol={symbol}&side=SELL&type=MARKET&quoteOrderQty={trade_amount}&timestamp={int(datetime.utcnow().timestamp() * 1000)}'
    signature = generate_signature(data)
    # Send the request with the API key and signature
    endpoint = 'https://testnet.binance.vision/api/v3/order'
    payload = {
        'symbol': symbol,
        'side': 'SELL',
        'type': 'MARKET',
        'quoteOrderQty': trade_amount,
        'newOrderRespType': 'FULL',
        'timestamp': int(datetime.utcnow().timestamp() * 1000),
        'leverage': leverage,
        'positionSide': position_mode,
        'recvWindow': 5000,
        'signature': signature,
    }
    headers = {
        'X-MBX-APIKEY': api_key
    }
    response = requests.post(endpoint, params=payload, headers=headers)
    result = json.loads(response.text)
    if 'code' in result:
        print('Failed to execute short trade: ' + result['msg'])
    else:
        initial_balance = initial_balance + trade_amount * float(result['avgPrice']) / take_profit_price
        total_trades += 1
        success_trades += 1
        profit_loss += (1 - trade_amount / initial_balance) * 100
if total_trades > 0:
    print(f'Total Trades: {total_trades}, Success Trades: {success_trades}, '
          f'Profit/Loss Percentage: {profit_loss/total_trades:.2f}%')

       
       
