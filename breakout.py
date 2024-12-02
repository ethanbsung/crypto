import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import dontshare as d
import time

kraken = ccxt.kraken({
    'apiKey': d.API_KEY,
    'secret': d.SECRET_KEY,
})

# Fetch historical OHLCV data
def fetch_ohlcv(symbol, timeframe='1h', limit=500):
    print(f"Fetching data for {symbol}...")
    try:
        ohlcv = kraken.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Error fetching OHLCV data: {e}")
        raise

# Calculate relative volume (RVOL)
def calculate_relative_volume(df):
    df['avg_volume'] = df['volume'].rolling(window=20).mean()
    df['rvol'] = df['volume'] / df['avg_volume']
    return df

# Backtest strategy
def backtest_strategy(df, rvol_threshold=3, initial_balance=1000, trade_amount=100, fee_rate=0.0025):
    balance = initial_balance
    position = 0
    trade_log = []
    equity_curve = []

    for i in range(len(df)):
        if i < 20:  # Skip first 20 periods for RVOL calculation
            equity_curve.append(balance)
            continue
        
        current_rvol = df['rvol'].iloc[i]
        price = df['close'].iloc[i]
        
        # Buy condition: RVOL > threshold and price increasing
        if current_rvol > rvol_threshold and position == 0 and df['close'].iloc[i] > df['close'].iloc[i - 1]:
            position = trade_amount / price
            balance -= trade_amount
            balance -= trade_amount * fee_rate  # Apply fee
            trade_log.append({'timestamp': df['timestamp'].iloc[i], 'type': 'buy', 'price': price, 'amount': position})
        
        # Sell condition: RVOL > threshold and price decreasing
        elif current_rvol > rvol_threshold and position > 0 and df['close'].iloc[i] < df['close'].iloc[i - 1]:
            balance += position * price
            balance -= position * price * fee_rate  # Apply fee
            trade_log.append({'timestamp': df['timestamp'].iloc[i], 'type': 'sell', 'price': price, 'amount': position})
            position = 0

        equity_curve.append(balance + (position * price if position > 0 else 0))

    # Close position at the end
    if position > 0:
        balance += position * df['close'].iloc[-1]
        balance -= position * df['close'].iloc[-1] * fee_rate
        trade_log.append({'timestamp': df['timestamp'].iloc[-1], 'type': 'sell', 'price': df['close'].iloc[-1], 'amount': position})
        position = 0

    return balance, pd.DataFrame(trade_log), equity_curve

# Calculate metrics
def calculate_metrics(trade_log, equity_curve, initial_balance):
    trades = trade_log.groupby('type')
    buy_trades = trade_log[trade_log['type'] == 'buy']
    sell_trades = trade_log[trade_log['type'] == 'sell']

    # Metrics
    gains = []
    losses = []
    for i in range(len(sell_trades)):
        buy_price = buy_trades.iloc[i]['price']
        sell_price = sell_trades.iloc[i]['price']
        profit = sell_price - buy_price
        if profit > 0:
            gains.append(profit)
        else:
            losses.append(profit)
    
    total_trades = len(sell_trades)
    wins = len(gains)
    losses_count = len(losses)

    win_rate = wins / total_trades * 100 if total_trades > 0 else 0
    avg_win = np.mean(gains) if gains else 0
    avg_loss = np.mean(losses) if losses else 0
    total_return = (equity_curve[-1] - initial_balance) / initial_balance * 100
    sharpe_ratio = np.mean(equity_curve) / np.std(equity_curve) if np.std(equity_curve) > 0 else 0
    downside = [min(0, x - np.mean(equity_curve)) for x in equity_curve]
    sortino_ratio = np.mean(equity_curve) / np.std(downside) if np.std(downside) > 0 else 0
    max_drawdown = np.min([min(0, x - initial_balance) for x in equity_curve])
    calmar_ratio = total_return / abs(max_drawdown) if max_drawdown < 0 else 0

    return {
        'win_rate': win_rate,
        'total_return': total_return,
        'average_win': avg_win,
        'average_loss': avg_loss,
        'sharpe_ratio': sharpe_ratio,
        'sortino_ratio': sortino_ratio,
        'calmar_ratio': calmar_ratio
    }

# Plot results
def plot_results(df, trade_log, equity_curve):
    plt.figure(figsize=(14, 7))
    plt.plot(df['timestamp'], equity_curve, label='Equity Curve', color='blue')
    plt.plot(df['timestamp'], df['close'], label='Price', color='orange', alpha=0.6)
    for _, trade in trade_log.iterrows():
        if trade['type'] == 'buy':
            plt.scatter(trade['timestamp'], trade['price'], color='green', label='Buy Signal', marker='^')
        elif trade['type'] == 'sell':
            plt.scatter(trade['timestamp'], trade['price'], color='red', label='Sell Signal', marker='v')
    plt.title('Backtesting Results')
    plt.xlabel('Time')
    plt.ylabel('Equity/Price')
    plt.legend()
    plt.show()

# Main execution
def main():
    symbol = 'XBT/USD'  # Use valid Kraken symbol
    timeframe = '1h'    # Use valid timeframe
    initial_balance = 1000
    
    try:
        # Fetch historical data
        df = fetch_ohlcv(symbol, timeframe)
        df = calculate_relative_volume(df)

        # Backtest the strategy
        final_balance, trade_log, equity_curve = backtest_strategy(df, initial_balance=initial_balance)

        # Calculate metrics
        metrics = calculate_metrics(trade_log, equity_curve, initial_balance)
        print("Metrics:")
        for key, value in metrics.items():
            print(f"{key}: {value}")

        # Plot results
        plot_results(df, trade_log, equity_curve)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()