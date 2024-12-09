'''
获取每日的目标债券,成熟的方式
'''

import time
from datetime import datetime
import pytz
import akshare as ak

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




symbols=['sh111001', 'sh113030', 'sh113537', 'sh113582', 'sh113685', 'sh118003', 'sh118026', 'sz123035', 'sz123078', 'sz123103', 'sz123184', 'sz123190', 'sz123209', 'sz123227', 'sz123228', 'sz123248', 'sz127035', 'sz127072', 'sz127087', 'sz128044', 'sz128076', 'sz128083', 'sz128085', 'sz128100', 'sz128109', 'sz128114', 'sz128118']


# 打印符合条件的债券符号
print("符合条件的债券符号:")
print(symbols)

def online_day_trading():
    
    # Initial Setup
    initial = 10000  # Initial capital
    share = 0  # Shares held
    asset = initial  # Portfolio value
    backtest = []  # Store backtest results

    today = datetime.today().strftime('%Y-%m-%d')  # Set today's date
    print("今天:", today)

    # Set up logging file path
    log_file = f"{today} 成交量策略 回测过程.txt"

    i = 0
    # Open file to write backtest process
    with open(log_file, 'a', encoding='utf-8') as f:  # Use 'a' to append to the file
        while True:
            # Get the current time
            current_time = get_time()

            # Check if current time is within the allowed trading hours
            # Morning: 09:30 - 11:30, Afternoon: 13:00 - 15:00
            if (current_time >= datetime.strptime('09:30', '%H:%M').time() and current_time <= datetime.strptime('11:30', '%H:%M').time()) or \
            (current_time >= datetime.strptime('13:00', '%H:%M').time() and current_time <= datetime.strptime('15:00', '%H:%M').time()):

                temp = ak.bond_zh_hs_cov_spot()  # Get data for time t
                temp = temp[temp['symbol'].isin(symbols)]
                temp.rename(columns={'trade': '最新价', 'amount': '成交额'}, inplace=True)
                # 尝试转换为 float，遇到错误时将其设置为 NaN
                temp['最新价'] = pd.to_numeric(temp['最新价'], errors='coerce')
                temp['成交额'] = pd.to_numeric(temp['成交额'], errors='coerce')


                target = temp.loc[temp['成交额'].idxmax()]  # Choose bond with highest volume

                if i == 0:
                    # First buy
                    old_price = target['最新价']
                    old_symbol = target['symbol']
                    share = asset // old_price  # Calculate how many shares can be bought
                    output = f"时间为：{current_time}\n买入 {old_symbol} {share} 股 总资产: {asset}\n\n"
                    print(output)
                    f.write(output)  # Write to log

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
                        f.write(output)  # Write to log

                    old_price = current_price
                    old_symbol = current_symbol

                i += 1
                backtest.append(asset)  # Append updated asset
                print("可转债价格为:",old_price )
                print("时间为:", current_time, "总资产为：", asset)

                # Pause for 60 seconds before the next transaction
                time.sleep(60)  # Pause for 30 seconds

            else:
                # If it's outside of trading hours, wait and check again after a short interval
                print("不在交易时间，等待下一个检查...")
                time.sleep(60)  # Pause for 60 seconds before checking again


online_day_trading()
