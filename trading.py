'''
获取每日的目标债券,成熟的方式
'''
import pandas as pd
import time
from datetime import datetime
import pytz
import akshare as ak
import sys

# 初始债券符号列表

# 获取所有债券符号的函数
def get_time():
    # 获取本地时间
    local_timezone = pytz.timezone('Asia/Shanghai')  # 设置为你所在的时区（比如中国时间）
    local_time = datetime.now(local_timezone)  # 获取本地时区的当前时间

    # 获取本地时间的时分秒部分
    current_time = local_time.strftime('%H:%M:%S')
    current_time_obj = datetime.strptime(current_time, '%H:%M:%S').time()
    return current_time_obj

def get_all_symbols():
    spot_df = ak.bond_zh_hs_cov_spot()
    symbols = spot_df['symbol'].values
    return symbols

def get_target_symbols(day_n=3,threshod=100000):
    # 目标债券符号列表
    target_symbols = []

    # 获取所有债券符号
    all_symbols = get_all_symbols()



    # 遍历所有债券符号
    for i in all_symbols:
        try:
            # 获取每个债券的历史数据
            temp = ak.bond_zh_hs_cov_daily(symbol=i)
            temp['changepercent'] = temp['close'].pct_change() * 100

            # 检查历史数据是否存在
            if temp is not None and len(temp) >= day_n:
                # 获取最后三天的成交量数据
                volumes = temp['volume'].tail(day_n).values  # 取最后day_n行的成交量数据
                closes = temp['close'].tail(day_n).values

                #changes=temp['changepercent'].tail(day_n).values

                #每日日内的浮动大小
                changes=(temp['high'].tail(day_n).values-temp['low'].tail(day_n).values)/temp['open'].tail(day_n).values*100

                #if i=='sh113569':
                    #print("注意!!!")
                    #print(volumes)
                    #print(closes)
                    #print(changes)


                # 如果最后day_n天的成交量都大于threshod，加入target_symbols
                if all(volume > threshod for volume in volumes)and all( close <150 for  close in closes)and all( change>2.5 for  change in changes):
                    print(f"债券{i}加入目标")
                    target_symbols.append(i)
            else:
                print(f"债券{i} 的历史数据不足{day_n}天，跳过此债券。")
        
        except Exception as e:
            # 捕获异常并打印错误信息
            print(f"获取债券 {i} 的数据时出错: {e}")
    return target_symbols


#symbols=get_target_symbols()

symbols=['sh111001', 'sh113030', 'sh113537', 'sh113582', 'sh113685', 'sh118003', 'sh118026', 'sz123035', 'sz123078', 'sz123103', 'sz123184', 'sz123190', 'sz123209', 'sz123227', 'sz123228', 'sz123248', 'sz127035', 'sz127072', 'sz127087', 'sz128044', 'sz128076', 'sz128083', 'sz128109',  'sz128118']

# 打印符合条件的债券符号
print("符合条件的债券符号:")
print(symbols)


#根据symbols的票选出实时的target，返回一个向量，包含symbol，交易量，成交价之类的数据
def get_temp(symbols):
    # 用于存储所有symbol的最后一行数据
    all_dfs = []

    # 遍历每个symbol，获取数据并取最后一行
    for symbol in symbols:
        try:
            # 获取数据
            df = ak.bond_zh_hs_cov_min(symbol, period='1', adjust='', start_date="1979-09-01 09:32:00", end_date="2222-01-01 09:32:00")
            
            # 如果数据非空，取最后一行数据
            if not df.empty:
                df = df.iloc[-1]
                # 添加symbol作为一列来区分不同债券
                df['symbol'] = symbol
                # 将每个df添加到all_dfs列表
                all_dfs.append(df)
            else:
                print(f"No data found for symbol: {symbol}")
        except Exception as e:
            # 捕捉异常并输出错误信息
            print(f"Error occurred for symbol {symbol}: {e}")

    # 将所有的df合并成一个DataFrame
    if all_dfs:
        temp = pd.concat(all_dfs, axis=1).T
        temp = temp.reset_index(drop=True)
        
        # 尝试转换为 float，遇到错误时将其设置为 NaN
        temp['最新价'] = pd.to_numeric(temp['最新价'], errors='coerce')
        temp['成交额'] = pd.to_numeric(temp['成交额'], errors='coerce')
        #target = temp.loc[temp['成交额'].idxmax()]  # Choose bond with highest volume
        return temp
        # 打印结果
        #print(temp)
        #print(target)
    else:
        print("No valid data collected.")
        return pd.DataFrame()



def online_day_trading():
    
    # Initial Setup
    initial = 10000  # Initial capital
    share = 0  # Shares held
    asset = initial  # Portfolio value
    backtest = []  # Store backtest results

    today = datetime.today().strftime('%Y-%m-%d')  # Set today's date
    print("今天:", today)
    sys.stdout.flush()
           
    # Set up logging file path
    log_file = f"{today} 成交量策略 交易过程.txt"

    i = 0

    while True:
        # Get the current time
        current_time = get_time()

        # Check if current time is within the allowed trading hours
        # Morning: 09:30 - 11:30, Afternoon: 13:00 - 15:00
        if (current_time >= datetime.strptime('09:30', '%H:%M').time() and current_time <= datetime.strptime('11:30', '%H:%M').time()) or \
        (current_time >= datetime.strptime('13:00', '%H:%M').time() and current_time <= datetime.strptime('15:00', '%H:%M').time()):

            #选出target
            temp=get_temp(symbols)
            target = temp.loc[temp['成交额'].idxmax()]

            if i == 0:
                # First buy
                old_price = target['最新价']
                old_symbol = target['symbol']
                share = asset // old_price  # Calculate how many shares can be bought
                
                output = f"时间为：{current_time}\n买入 {old_symbol} {share} 股 总资产: {asset}\n\n"
                print(output)


            else:
                # Update asset based on price change and possibly switch bond
                current_price = target['最新价']
                current_symbol = target['symbol']
                new_price = temp.loc[temp['symbol'] == old_symbol]['最新价'].values[0]
                asset += share * (new_price - old_price)  # Update asset value

                if current_symbol != old_symbol:
                    # Sell old and buy new bond
                    share = asset // current_price  # Recalculate shares for new bond
                    
                    output = f"时间为：{current_time}\n清仓 {old_symbol} 买入 {current_symbol} {int(share)} 股 总资产: {asset:.2f}\n\n"
                    print(output)

                old_price = current_price
                old_symbol = current_symbol

            i += 1
            backtest.append(asset)  # Append updated asset
            print("可转债价格为:",old_price )
            print("时间为:", current_time, "总资产为：", asset)

            # Pause for 60 seconds before the next transaction
            time.sleep(30)  # Pause for 30 seconds

        else:
            # If it's outside of trading hours, wait and check again after a short interval
            print("不在交易时间，等待下一个检查...")
            time.sleep(60)  # Pause for 60 seconds before checking again
        sys.stdout.flush()

online_day_trading()
