# Br0keTrader

This is a Python script that uses the Binance API to execute trades on the BTCBUSD trading pair. It uses the OBV (On Balance Volume) indicator to determine when to enter long or short trades. The script runs continuously, executing trades only on specified days and hours, and prints out information about the total number of trades, success trades, and profit/loss percentage.

The script first sets some parameters such as the trading symbol (BTCBUSD), the time interval (30m), the maximum trading hours (2), the day and hour for long trades (Friday, 6), the day and hour for short trades (Friday, 4), the initial balance (1000), the maximum trade amount (30), the maximum stop loss percentage (1.1), the maximum leverage (5), and the position mode (CROSSED).

The script then enters into a while loop that runs continuously, until the script is interrupted by a keyboard interrupt (ctrl+c) or an exception occurs. Within the while loop, the script first calls the Binance API to get the historical trading data for the specified time interval. It then calculates the OBV indicator for each data point in the data frame.

The script then checks the current day and hour against the specified long and short trade days and hours. If the current day and hour match the specified long trade day and hour, the script checks if the OBV indicator has increased since the last data point. If it has, the script executes a long trade by calling the Binance API to place a market buy order for the specified trade amount using the specified leverage and position mode. If the current day and hour match the specified short trade day and hour, the script checks if the OBV indicator has decreased since the last data point. If it has, the script executes a short trade by calling the Binance API to place a market sell order for the specified trade amount using the specified leverage and position mode.

If a trade is executed, the script updates the initial balance, the total number of trades, the number of successful trades, and the profit/loss percentage. The script then prints out information about the total number of trades, successful trades, and profit/loss percentage.

If an exception occurs, the script prints out an error message and continues with the next iteration of the while loop. If the script is interrupted by a keyboard interrupt, the script prints out a message and exits the while loop.

```
webadmin@elasticsearch:~$ python3 test.py BTCUSDT
Most Profitable Day and Hour for Long Trades: ('Friday', 1)
Most Profitable Day and Hour for Short Trades: ('Friday', 2)
Most Profitable Day for Trades: Thursday (Profit: 57.82%)


Weekday Analysis:
            Profit  Position  Position USDT  Margin Balance  Win Rate  Profit per Trade
Weekday
Friday      141.39      -1.0           -250          152.38       NaN               NaN
Monday      -16.22       0.0              0          923.32       NaN               NaN
Saturday   -243.25       1.0            250          608.78       NaN               NaN
Sunday    -1021.76       0.0              0          689.54       NaN               NaN
Thursday    578.20       1.0            250          750.20       NaN               NaN
Tuesday    -263.58      -1.0           -250          159.74       NaN               NaN
Wednesday    14.00       0.0              0          173.74       NaN               NaN`


