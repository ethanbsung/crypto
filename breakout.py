import ccxt
import pandas as pd
import numpy as np
import dontshare as d
import time

kraken = ccxt.kraken({
    'apiKey': d.API_KEY,
    'secret': d.SECRET_KEY,
})

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

def calculate_relative_volume(df):
    df['avg_volume'] = df['volume'].rolling(window=20).mean()
    df['rvol'] = df['volume'] / df['avg_volume']
    return df

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
        
        if current_rvol > rvol_threshold and position == 0 and df['close'].iloc[i] > df['close'].iloc[i - 1]:
            position = trade_amount / price
            balance -= trade_amount
            balance -= trade_amount * fee_rate  # Apply fee
            trade_log.append({'timestamp': df['timestamp'].iloc[i], 'type': 'buy', 'price': price, 'amount': position})
        
        elif current_rvol > rvol_threshold and position > 0 and df['close'].iloc[i] < df['close'].iloc[i - 1]:
            balance += position * price
            balance -= position * price * fee_rate  # Apply fee
            trade_log.append({'timestamp': df['timestamp'].iloc[i], 'type': 'sell', 'price': price, 'amount': position})
            position = 0

        equity_curve.append(balance + (position * price if position > 0 else 0))

    if position > 0:
        balance += position * df['close'].iloc[-1]
        balance -= position * df['close'].iloc[-1] * fee_rate
        trade_log.append({'timestamp': df['timestamp'].iloc[-1], 'type': 'sell', 'price': df['close'].iloc[-1], 'amount': position})
        position = 0

    return balance, pd.DataFrame(trade_log), equity_curve

def calculate_metrics(trade_log, equity_curve, initial_balance):
    buy_trades = trade_log[trade_log['type'] == 'buy']
    sell_trades = trade_log[trade_log['type'] == 'sell']

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

    peak_equity = max(equity_curve)
    trough_equity = min(equity_curve)
    max_drawdown = (trough_equity - peak_equity) / peak_equity * 100

    win_rate = wins / total_trades * 100 if total_trades > 0 else 0
    avg_win = np.mean(gains) if gains else 0
    avg_loss = np.mean(losses) if losses else 0
    total_return = (equity_curve[-1] - initial_balance) / initial_balance * 100
    sharpe_ratio = np.mean(equity_curve) / np.std(equity_curve) if np.std(equity_curve) > 0 else 0
    downside = [min(0, x - np.mean(equity_curve)) for x in equity_curve]
    sortino_ratio = np.mean(equity_curve) / np.std(downside) if np.std(downside) > 0 else 0
    calmar_ratio = total_return / abs(max_drawdown) if max_drawdown < 0 else 0

    return {
        'win_rate': f"{win_rate:.2f}%",
        'total_return': total_return,
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses_count,
        'max_drawdown': f"{max_drawdown:.2f}%",
        'average_win': avg_win,
        'average_loss': avg_loss,
        'sharpe_ratio': sharpe_ratio,
        'sortino_ratio': sortino_ratio,
        'calmar_ratio': calmar_ratio
    }

def has_not_increased_significantly(df, threshold=0.1):
    initial_price = df['close'].iloc[0]
    final_price = df['close'].iloc[-1]
    price_increase = (final_price - initial_price) / initial_price
    return price_increase < threshold

def main():
    symbols = ['XBTUSDT', 'ETHUSDT', 'LTCUSDT', 'SOLUSDT']  # Add more symbols as needed
    timeframe = '1h'
    initial_balance = 1000
    threshold = 0.1  # 10% increase threshold

    for symbol in symbols:
        try:
            df = fetch_ohlcv(symbol, timeframe)
            df = calculate_relative_volume(df)

            if has_not_increased_significantly(df, threshold):
                final_balance, trade_log, equity_curve = backtest_strategy(df, initial_balance=initial_balance)
                metrics = calculate_metrics(trade_log, equity_curve, initial_balance)
                print(f"Metrics for {symbol}:")
                for key, value in metrics.items():
                    print(f"{key}: {value}")
                print("\n")
            else:
                print(f"{symbol} has increased significantly in price, skipping...\n")

        except Exception as e:
            print(f"An error occurred for {symbol}: {e}")

if __name__ == "__main__":
    main()