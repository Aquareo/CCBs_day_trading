'''
获取每日的目标债券,成熟的方式
'''
import pandas as pd
import time
from datetime import datetime,timedelta
import pytz
import akshare as ak
import sys


# 获取年月日（返回 datetime.date 类型）
def get_date():
    local_timezone = pytz.timezone('Asia/Shanghai')  # 设置为你所在的时区（比如中国时间）
    local_time = datetime.now(local_timezone)  # 获取本地时区的当前时间
    
    # 提取日期部分，返回 datetime.date 类型
    return local_time.date()

#获取时分秒
def get_time():
    # 获取本地时间
    local_timezone = pytz.timezone('Asia/Shanghai')  # 设置为你所在的时区（比如中国时间）
    local_time = datetime.now(local_timezone)  # 获取本地时区的当前时间
    
    #这是时分秒
    current_time = local_time.strftime('%H:%M:%S')
    current_time_obj = datetime.strptime(current_time, '%H:%M:%S').time()
    return current_time_obj

def get_all_symbols():
    spot_df = ak.bond_zh_hs_cov_spot()
    symbols = spot_df['symbol'].values
    return symbols


def get_target_symbols(day_n=3,threshod=180000):
    # 目标债券符号列表
    target_symbols = []

    # 获取所有债券符号
    all_symbols = get_all_symbols()


    # 遍历所有债券符号
    for i in all_symbols:
        try:
            # 获取每个债券的历史数据
            temp = ak.bond_zh_hs_cov_daily(symbol=i)

            #先看是否到期
            if temp.iloc[-1].date<get_date() - timedelta(days=1):
                print(f"转债{i}已经到期，跳过此转债。")
                continue

            # 检查历史数据是否存在
            if temp is not None and len(temp) >= day_n:
                # 获取最后三天的成交量数据
                volumes = temp['volume'].tail(day_n).values  # 取最后day_n行的成交量数据
                closes = temp['close'].tail(day_n).values

                #每日日内的浮动大小
                changes=(temp['high'].tail(day_n).values-temp['low'].tail(day_n).values)/temp['open'].tail(day_n).values*100


                # 如果最后day_n天的成交量都大于threshod，加入target_symbols
                if all(volume > threshod for volume in volumes)and all(close <150 for  close in closes)and all( change>2.5 for  change in changes):
                    print(f"债券{i}加入目标")
                    target_symbols.append(i)
            else:
                print(f"债券{i} 的历史数据不足{day_n}天，跳过此债券。")
        
        except Exception as e:
            # 捕获异常并打印错误信息
            print(f"获取债券 {i} 的数据时出错: {e}")

        sys.stdout.flush()
    return target_symbols



def get_symbols(symbols):
    void_symbol=[]
    df = pd.DataFrame()

    for symbol in symbols:
        #print(f"获取 {symbol}")
        try:
            # 尝试获取数据
            temp = ak.bond_zh_hs_cov_min(symbol, period='1')
            temp['symbol']=symbol

            # 只取最后一行，这很关键
            temp = temp.iloc[[-1]]  # 取最后一行，并保持DataFrame格式


            df = pd.concat([df, temp], ignore_index=True)

        except Exception as e:
            # 捕获所有异常，打印错误信息
            void_symbol.append(symbol)
            #print(f"获取 {symbol} 数据时发生错误: {e}")
            continue  # 发生错误时跳过此symbol，继续处理下一个symbol
    return df

def get_target(filtered_df):
    target = filtered_df.loc[filtered_df['成交额'].idxmax()]
    return target['symbol']


def get_filtered_df(symbols):

    df = ak.bond_zh_hs_cov_spot()
    columns_to_convert = ['trade', 'pricechange', 'changepercent', 'buy', 'sell', 'settlement', 'open', 'high', 'low', 'volume', 'amount']

    # 将这些列转换为数值类型，遇到无法转换的会被设置为 NaN
    df[columns_to_convert] = df[columns_to_convert].apply(pd.to_numeric, errors='coerce')

    filtered_df = df[df['symbol'].isin(symbols)]

    return filtered_df


#策略：找出来成交额最大的target,返回一个series,包含trade,pricechange,changepercent,volume,amount 等字段
def get_series_by_strategy(filtered_df):
    target = filtered_df.loc[filtered_df['amount'].idxmax()]
    return target

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
    trading_cost=0
    while True:
        # Get the current time
        current_time = get_time()
        
        # Check if current time is within the allowed trading hours
        # Morning: 09:30 - 11:30, Afternoon: 13:00 - 15:00
        if (current_time >= datetime.strptime('09:30', '%H:%M').time() and current_time <= datetime.strptime('11:30', '%H:%M').time()) or \
        (current_time >= datetime.strptime('13:00', '%H:%M').time() and current_time <= datetime.strptime('15:00', '%H:%M').time()):

            print("时间为:", current_time)
            print(" ")
            
            #选出代码集合symbols的实时行情
            filtered_df = get_symbols(symbols)

            #根据策略找出来成交额最大的target_symbol,这样就可以编写一个策略了
            target_symbol = get_target(filtered_df)


            #获取实时行情
            spot = ak.bond_zh_hs_cov_spot()
            columns_to_convert = ['trade', 'pricechange', 'changepercent', 'buy', 'sell', 'settlement', 'open', 'high', 'low', 'volume', 'amount']

            # 将这些列转换为数值类型，遇到无法转换的会被设置为 NaN
            spot[columns_to_convert] = spot[columns_to_convert].apply(pd.to_numeric, errors='coerce')


            target=spot.loc[spot['symbol']==  target_symbol].squeeze()


            #最新价的字段名字
            price_symbol='trade'

            #首次交易
            if i == 0:
                # First buy
                old_price = target[price_symbol]
                old_symbol = target['symbol']


                """
                买入操作
                """

                share = asset // old_price  # Calculate how many shares can be bought
                trading_cost+=share*old_price*0.0003
                output = f"时间为：{current_time}\n买入 {old_symbol} {share} 股 总资产: {asset}\n\n"
                print(output)

            else:
                # Update asset based on price change and possibly switch bond
                current_price = target[price_symbol]
                current_symbol = target['symbol']
                new_price = spot.loc[spot['symbol'] == old_symbol][price_symbol].values[0]
                asset += share * (new_price - old_price)  # Update asset value

                #如果需要换持有转债

                """
                买入操作+卖出操作
                """

                if current_symbol != old_symbol:
                    # Sell old and buy new bond
                    share = asset // current_price  # Recalculate shares for new bond
                    trading_cost+=share*current_price *0.0003
                    
                    output = f"时间为：{current_time}\n清仓 {old_symbol} 买入 {current_symbol} {int(share)} 股 总资产: {asset:.2f}\n\n"
                    print(output)
                    
                old_price = current_price
                old_symbol = current_symbol


                print("目前持有可转债代码: ",old_symbol,",价格为:",old_price )
                print("总资产为：", asset)
                print("trading cost",trading_cost)


            #一次迭代完成
            i += 1
            backtest.append(asset)  # Append updated asset

            # Pause for 25 seconds before the next transaction
            # time.sleep(20)  # Pause for 30 seconds

        else:
            # If it's outside of trading hours, wait and check again after a short interval
            print("不在交易时间，等待下一个检查...")
            time.sleep(60)  # Pause for 60 seconds before checking again

        print(" ")
        sys.stdout.flush()


print("获取目标可转债池中...")
symbols=get_target_symbols()

#symbols=['sh110052', 'sh111012', 'sh111016', 'sh113549', 'sh113569', 'sh113582', 'sh113597', 'sh113678', 'sh113688', 'sh118007', 'sh118026', 'sh118043', 'sz123067', 'sz123089', 'sz123099', 'sz123103', 'sz123131', 'sz123138', 'sz123147', 'sz123160', 'sz123163', 'sz123166', 'sz123184', 'sz123226', 'sz123228', 'sz123231', 'sz123237', 'sz123239', 'sz123245', 'sz123248', 'sz123249', 'sz127033', 'sz127051', 'sz128072', 'sz128083', 'sz128109']
# 打印符合条件的债券符号

print("符合条件的债券符号为:")
print(symbols)

online_day_trading()
