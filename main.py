import pandas as pd
import akshare as ak
import numpy as np
from datetime import datetime
import time
#import matplotlib.pyplot as plt 
import pytz

symbol="sz123124"
period="5"

# 获取上一个交易日的历史数据
def historical_in_day_data(symbol, period):
    try:
        # 获取1分钟数据
        bond_zh_hs_cov_min_df = ak.bond_zh_hs_cov_min(symbol, period)

        # 检查数据是否为空
        if bond_zh_hs_cov_min_df is None or bond_zh_hs_cov_min_df.empty:
            raise ValueError(f"没有获取到有效数据: {symbol}")

        # 处理数据，转换时间为datetime格式
        bond_zh_hs_cov_min_df['时间'] = pd.to_datetime(bond_zh_hs_cov_min_df['时间'])

        # 重命名 '收盘' 为 '最新价'
        if period=="5":
            bond_zh_hs_cov_min_df = bond_zh_hs_cov_min_df.rename(columns={'收盘': '最新价'})


        # 选择需要的列
        bond_zh_hs_cov_min_df = bond_zh_hs_cov_min_df[['时间', '开盘', '最高', '最低', '成交量', '成交额', '最新价']]

        return bond_zh_hs_cov_min_df

    except Exception as e:
        print(f"Error occurred while fetching data for {symbol}: {e}")
        return None


# 获取实时可转债价格
def get_realtime_data(symbol):
    try:
        bond_zh_hs_cov_spot_df = ak.bond_zh_hs_cov_spot()
        bond_zh_hs_cov_spot_df.rename(columns={
            'name': '名称',
            'trade': '最新价',
            'pricechange': '涨跌额',
            'changepercent': '涨跌幅',
            'buy': '买入价',
            'sell': '卖出价',
            'settlement': '结算价',
            'open': '开盘',
            'high': '最高',
            'low': '最低',
            'volume': '成交量',
            'amount': '成交额',
            'code': '债券代码',
            'ticktime': '时间'
        }, inplace=True)

        # 根据 symbol 筛选出对应的行
        bond_symbol_df = bond_zh_hs_cov_spot_df[bond_zh_hs_cov_spot_df['symbol'] == symbol]
        return bond_symbol_df

    except Exception as e:
        print(f"Error fetching real-time data: {e}")
        return None


# 策略 1: 移动平均交叉策略
def moving_average_strategy(data, short_window=5, long_window=20):
    signals = pd.DataFrame(index=data.index)
    signals['signal'] = 0
    signals['short_mavg'] = data['最新价'].rolling(window=short_window, min_periods=1).mean()
    signals['long_mavg'] = data['最新价'].rolling(window=long_window, min_periods=1).mean()
    signals['signal'] = np.where(signals['short_mavg'] > signals['long_mavg'], 1, -1)
    return signals['signal']

# 策略 2: 相对强弱指数（RSI）策略
def rsi_strategy(data, window=14, overbought=70, oversold=30):
    delta = data['最新价'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    signals = pd.Series(0, index=data.index)
    signals[rsi > overbought] = -1  # 卖出信号
    signals[rsi < oversold] = 1    # 买入信号
    return signals

# 综合策略: 简单加权平均
def combined_strategy(ma_signals, rsi_signals):
    return (ma_signals + rsi_signals) / 2


def plot_balance_history(balance_history):
    plt.figure(figsize=(10, 6))
    plt.plot(balance_history, label="Portfolio Value")
    plt.title("Portfolio Value Over Time")
    plt.xlabel("Time Step")
    plt.ylabel("Portfolio Value (USD)")
    plt.legend()
    plt.show()

# 将portfolio_value保存到CSV
def save_to_csv(time, portfolio_value, filename='portfolio_value.csv'):
    df = pd.DataFrame({'时间': [time], '资产总值': [portfolio_value]})
    df.to_csv(filename, mode='a', header=False, index=False)


# 将portfolio_value保存到TXT文件
def save_to_txt(time, portfolio_value, filename='portfolio_value.txt'):
    with open(filename, 'a') as file:
        file.write(f"{time}, {portfolio_value}\n")


# 主交易函数
def trade(symbol, initial_balance=100000):
    strategies = {
        "Moving Average": {"balance": initial_balance, "shares": 0, "history": []},
        "RSI": {"balance": initial_balance, "shares": 0, "history": []},
        "Combined": {"balance": initial_balance, "shares": 0, "history": []}
    }
    timestamps = []

    short_window = 5
    long_window = 20
    rsi_window = 14

    # 获取历史数据
    historical_data = historical_in_day_data(symbol,period)

    try:
        with open('backtest.txt', 'r') as file:
            pass
    except FileNotFoundError:
        with open('backtest.txt', 'w') as file:
            file.write("时间, Moving Average, RSI, Combined\n")

    while True:
        try:
            # 获取当前时间
            china_tz = pytz.timezone('Asia/Shanghai')
            current_time = datetime.now(china_tz)
            formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"当前时间: {formatted_time}\n")

            #检查交易时间（9:30到11:30 &&13:00到15:00）
            if (current_time.hour < 9 or (current_time.hour == 9 and current_time.minute < 30)) or \
               (current_time.hour == 11 and current_time.minute > 30) or \
               current_time.hour > 15:
                time.sleep(60)
                print("非交易时间")
                continue

            # 获取实时数据
            df = get_realtime_data(symbol)
            df['时间'] = pd.to_datetime(df['时间'])
            data = df[['时间', '开盘', '最高', '最低', '成交量', '成交额', '最新价']].copy()
            # 确保 '最新价' 是浮点数
            data['最新价'] = pd.to_numeric(data['最新价'], errors='coerce')
            
            # 更新历史数据
            historical_data = pd.concat([historical_data, data]).drop_duplicates(subset='时间', keep='last')

            # 计算策略信号
            ma_signals = moving_average_strategy(historical_data, short_window, long_window)
            rsi_signals = rsi_strategy(historical_data, rsi_window)
            combined_signals = combined_strategy(ma_signals, rsi_signals)

            # 获取最新价格和信号
            current_price = historical_data['最新价'].iloc[-1]
            latest_signals = {
                "Moving Average": ma_signals.iloc[-1],
                "RSI": rsi_signals.iloc[-1],
                "Combined": combined_signals.iloc[-1]
            }

            # 遍历策略执行交易
            for strategy_name, strategy_data in strategies.items():
                signal = latest_signals[strategy_name]
                balance = strategy_data["balance"]
                shares = strategy_data["shares"]

                if signal > 0:  # 买入信号
                    shares_to_buy = balance // current_price
                    strategy_data["balance"] -= shares_to_buy * current_price
                    strategy_data["shares"] += shares_to_buy
                    print(f"{strategy_name}: 执行买入操作: 买入 {shares_to_buy} 股")

                elif signal < 0:  # 卖出信号
                    strategy_data["balance"] += shares * current_price
                    strategy_data["shares"] = 0
                    print(f"{strategy_name}: 执行卖出操作: 清仓")

                else:
                    print(f"{strategy_name}: 不执行买卖操作")

                # 更新资产总值
                portfolio_value = strategy_data["balance"] + strategy_data["shares"] * current_price
                strategy_data["history"].append(portfolio_value)
                print(f"{strategy_name}: 当前资产总值: {portfolio_value}")

                print("   ")

            # 保存数据
            timestamps.append(formatted_time)
            portfolio_values = ", ".join(
                str(round(strategies[s]["history"][-1], 2)) for s in strategies
            )
            save_to_txt(formatted_time, portfolio_values, filename='backtest.txt')

            time.sleep(10)  # 模拟实时交易的间隔

        except Exception as e:
            print(f"交易过程中出现错误: {e}")
            time.sleep(10)


# 调用交易函数
trade(symbol)
