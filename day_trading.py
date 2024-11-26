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


# 定义交易策略：移动平均交叉策略
def moving_average_strategy(data, short_window=5, long_window=20):
    signals = pd.DataFrame(index=data.index)
    signals['signal'] = 0
    signals['short_mavg'] = data['最新价'].rolling(window=short_window, min_periods=1, center=False).mean()
    signals['long_mavg'] = data['最新价'].rolling(window=long_window, min_periods=1, center=False).mean()
    signals.loc[short_window:, 'signal'] = np.where(signals['short_mavg'][short_window:] > signals['long_mavg'][short_window:], 1, 0)
    signals['positions'] = signals['signal'].diff()
    return signals

def plot_balance_history(balance_history):
    plt.figure(figsize=(10, 6))
    plt.plot(balance_history, label="Portfolio Value")
    plt.title("Portfolio Value Over Time")
    plt.xlabel("Time Step")
    plt.ylabel("Portfolio Value (USD)")
    plt.legend()
    plt.show()

# 将portfolio_value保存到CSV
def save_to_csv(time, portfolio_value, filename='backtest.csv'):
    df = pd.DataFrame({'时间': [time], '资产总值': [portfolio_value]})
    df.to_csv(filename, mode='a', header=False, index=False)


# 将portfolio_value保存到TXT文件
def save_to_txt(time, portfolio_value, filename='backtest.txt'):
    with open(filename, 'a') as file:
        file.write(f"{time}, {portfolio_value}\n")


# 主交易函数
def trade(symbol):

    # 初始化资金和持仓
    initial_balance = 100000.0  # 初始资金 100,000
    balance = initial_balance  # 当前余额
    shares = 0  # 当前持有的股票数量
    portfolio_value = initial_balance  # 投资组合的总价值（现金 + 股票市值）

    # 记录资金变化的列表
    balance_history = []

    # 设置短期和长期均线窗口
    short_window = 5
    long_window = 20

    # 获取历史数据
    historical_data = historical_in_day_data(symbol, period)


    
    # 初始化CSV文件，如果文件不存在，创建文件并添加标题行
    #try:
        #df = pd.read_csv('portfolio_value.csv')
    #except FileNotFoundError:
       # df = pd.DataFrame(columns=['时间', '资产总值'])
       # df.to_csv('portfolio_value.csv', index=False)
    # 初始化TXT文件，如果文件不存在，创建文件并添加标题行
    try:
        with open('backtest.txt', 'r') as file:
            pass
    except FileNotFoundError:
        with open('backtest.txt', 'w') as file:
            file.write("时间, 资产总值\n")
    
    while True:
        try:
            # 获取中国标准时间 (CST, UTC+8)
            china_tz = pytz.timezone('Asia/Shanghai')

            # 获取当前时间并转换为指定时区
            current_time = datetime.now(china_tz)
            formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')


            print(f"当前时间: {formatted_time}")


            #检查交易时间（9:30到11:30 &&13:00到15:00）
            if (current_time.hour < 9 or (current_time.hour == 9 and current_time.minute < 30)) or \
               (current_time.hour == 11 and current_time.minute > 30) or \
               current_time.hour > 15:
                time.sleep(60)
                continue

            # 获取实时数据
            df = get_realtime_data(symbol)


            # 取需要的列并处理
            df['时间'] = pd.to_datetime(df['时间'])
            data = df[['时间', '开盘', '最高', '最低', '成交量', '成交额', '最新价']].copy()
            data['最新价'] = pd.to_numeric(data['最新价'], errors='coerce')
            
            # 将实时数据合并到历史数据中（防止重复）
            historical_data = pd.concat([historical_data, data]).drop_duplicates(subset='时间', keep='last')

            # 执行策略
            signals = moving_average_strategy(historical_data, short_window, long_window)

            # 获取最新的信号
            latest_signal = signals.iloc[-1]

            #print("最新信号:", latest_signal)

            # 根据策略信号和持仓状态做出交易决策
            current_price = historical_data['最新价'].iloc[-1];
            current_price=float(current_price);
            # 根据策略信号和持仓状态做出交易决策
    
            if latest_signal['positions'] == 1:  # 买入信号
                
                # 全仓买入：用所有余额买入
                shares_to_buy = balance // current_price  # 根据余额买入最大数量的股票
                balance -= shares_to_buy * current_price  # 更新余额
                shares += shares_to_buy  # 更新持仓
        
                print(f"执行买入操作: 买入 {shares_to_buy} 股")
        
            elif latest_signal['positions'] == -1:  # 卖出信号
        
                balance += shares * current_price  # 卖出所有持仓
                shares = 0  # 清空持仓
        
                print(f"执行卖出操作: 卖出 {shares} 股")
            else:
                print("不执行买卖操作")



            #print(type(balance))        # 确保是 int 或 float
            #print(type(shares))         # 确保是 int 或 float
            #print(type(current_price))  # 确保是 int 或 float

            
            # 更新投资组合的总价值
            portfolio_value = balance + shares * current_price

            print("资产总值",portfolio_value)

            # 记录资金变化
            balance_history.append(portfolio_value)

            # 绘制资金曲线
            #plot_balance_history(balance_history)
            
            # 保存到CSV
            #save_to_csv(formatted_time, portfolio_value)
            
            # 保存到TXT文件
            #save_to_txt(formatted_time, portfolio_value)
            save_to_txt(formatted_time, portfolio_value, filename='backtest.txt')

            
            # 等待一段时间后继续
            time.sleep(10)

        except Exception as e:
            print(f"交易过程中出现错误: {e}")
            time.sleep(10)


# 调用交易函数
trade(symbol)
