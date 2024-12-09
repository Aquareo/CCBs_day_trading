'''
获取每日的目标债券,成熟的方式
'''
import pandas as pd
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




symbols=['sh111001', 'sh113030', 'sh113537', 'sh113582', 'sh113685', 'sh118003', 'sh118026', 'sz123035', 'sz123078', 'sz123103', 'sz123184', 'sz123190', 'sz123209', 'sz123227', 'sz123228', 'sz123248', 'sz127035', 'sz127072', 'sz127087', 'sz128044', 'sz128076', 'sz128083', 'sz128109',  'sz128118']

# 打印符合条件的债券符号
print("符合条件的债券符号:")
print(symbols)



