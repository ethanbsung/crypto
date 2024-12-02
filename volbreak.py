import pandas as pd
import numpy as np

def calculate_relative_volume(df):
    df['avg_volume'] = df['volume'].rolling(window=20).mean()
    df['rvol'] = df['volume'] / df['avg_volume']
    return df

def backtest_strategy(df, rvol_threshold=3, initial_balance=1000, trade_amount=100, fee_rate=0.0025):
    balance = initial_balance
    position = 0
    entry_price = 0
    trade_log = []
    equity_curve = []

    for i in range(len(df)):
        if i < 20:  # Skip first 20 periods for RVOL calculation
            equity_curve.append(balance)
            continue
        
        current_rvol = df['rvol'].iloc[i]
        price = df['close'].iloc[i]
        
        # Buy condition
        if current_rvol > rvol_threshold and position == 0 and df['close'].iloc[i] > df['close'].iloc[i - 1]:
            position = trade_amount / price
            entry_price = price
            balance -= trade_amount
            balance -= trade_amount * fee_rate  # Apply fee
            trade_log.append({'datetime': df['datetime'].iloc[i], 'type': 'buy', 'price': price, 'amount': position})
        
        # Sell condition based on price doubling or falling 20%
        elif position > 0:
            if price >= 2 * entry_price or price <= 0.8 * entry_price:
                balance += position * price
                balance -= position * price * fee_rate  # Apply fee
                trade_log.append({'datetime': df['datetime'].iloc[i], 'type': 'sell', 'price': price, 'amount': position})
                position = 0

        equity_curve.append(balance + (position * price if position > 0 else 0))

    # Final exit if position is still open
    if position > 0:
        balance += position * df['close'].iloc[-1]
        balance -= position * df['close'].iloc[-1] * fee_rate
        trade_log.append({'datetime': df['datetime'].iloc[-1], 'type': 'sell', 'price': df['close'].iloc[-1], 'amount': position})
        position = 0

    return balance, pd.DataFrame(trade_log), equity_curve

def calculate_metrics(trade_log, equity_curve, initial_balance, df):
    if trade_log.empty:
        return {
            'win_rate': "0.00%",
            'total_return': "0.00%",
            'final_balance': initial_balance,
            'buy_and_hold_return': "0.00%",
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'max_drawdown': "0.00%",
            'average_win': "0.00%",
            'average_loss': "0.00%",
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'calmar_ratio': 0
        }

    buy_trades = trade_log[trade_log['type'] == 'buy']
    sell_trades = trade_log[trade_log['type'] == 'sell']

    gains = []
    losses = []
    for i in range(len(sell_trades)):
        buy_price = buy_trades.iloc[i]['price']
        sell_price = sell_trades.iloc[i]['price']
        profit = sell_price - buy_price
        if profit > 0:
            gains.append(profit / buy_price * 100)  # Convert to percentage
        else:
            losses.append(profit / buy_price * 100)  # Convert to percentage
    
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
    final_balance = equity_curve[-1]
    
    # Buy and hold return
    initial_price = df['close'].iloc[0]
    final_price = df['close'].iloc[-1]
    buy_and_hold_return = (final_price - initial_price) / initial_price * 100

    sharpe_ratio = np.mean(equity_curve) / np.std(equity_curve) if np.std(equity_curve) > 0 else 0
    downside = [min(0, x - np.mean(equity_curve)) for x in equity_curve]
    sortino_ratio = np.mean(equity_curve) / np.std(downside) if np.std(downside) > 0 else 0
    calmar_ratio = total_return / abs(max_drawdown) if max_drawdown < 0 else 0

    return {
        'win_rate': f"{win_rate:.2f}%",
        'total_return': f"{total_return:.2f}%",
        'final_balance': final_balance,
        'buy_and_hold_return': f"{buy_and_hold_return:.2f}%",
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses_count,
        'max_drawdown': f"{max_drawdown:.2f}%",
        'average_win': f"{avg_win:.2f}%",
        'average_loss': f"{avg_loss:.2f}%",
        'sharpe_ratio': sharpe_ratio,
        'sortino_ratio': sortino_ratio,
        'calmar_ratio': calmar_ratio
    }

def main():
    # Load data from CSV instead of fetching from the exchange
    filename = '/Users/ethansung/quant/memebot/Data/XBTUSDT_60.csv'
    df = pd.read_csv(filename)

    # Ensure the datetime is in datetime format
    df['datetime'] = pd.to_datetime(df['datetime'], unit='s')

    # Filter data for a specific period
    start_date = '2023-01-01'  # Example start date
    end_date = '2023-12-31'    # Example end date
    df = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]

    # Calculate relative volume
    df = calculate_relative_volume(df)

    # Set initial parameters
    initial_balance = 1000

    # Print statement indicating the backtest is running
    print("Running backtest...")

    # Run backtest
    final_balance, trade_log, equity_curve = backtest_strategy(df, initial_balance=initial_balance)

    # Calculate metrics
    metrics = calculate_metrics(trade_log, equity_curve, initial_balance, df)
    print(f"Metrics for XBTUSDT:")
    for key, value in metrics.items():
        print(f"{key}: {value}")
    print("\n")

if __name__ == "__main__":
    main()