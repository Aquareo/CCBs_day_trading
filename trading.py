import time
from datetime import datetime
import pytz
import akshare as ak
import pandas as pd

symbols = [
    'sh110090', 'sh110092', 'sh111008', 'sh111020', 'sh113534', 'sh113537',
    'sh113569', 'sh113662', 'sh113671', 'sh113685', 'sh118026', 'sz123078',
    'sz123092', 'sz123135', 'sz123141', 'sz123162', 'sz123190', 'sz123215',
    'sz123220', 'sz123225', 'sz123245', 'sz123250', 'sz127019', 'sz127033',
    'sz127051', 'sz127075', 'sz127078', 'sz127093', 'sz127096', 'sz127097',
    'sz127102', 'sz128070', 'sz128142', 'sz128144'
]

# Initial Setup
initial = 100000  # Initial capital
share = 0  # Shares held
asset = initial  # Portfolio value
backtest = []  # Store backtest results

today = datetime.today().strftime('%Y-%m-%d')  # Set today's date
print("今天:", today)

# Set up logging file path
log_file = f"{today} 成交量策略 回测过程.txt"

i = 0

def get_time():
    # 获取本地时间
    local_timezone = pytz.timezone('Asia/Shanghai')  # 设置为你所在的时区（比如中国时间）
    local_time = datetime.now(local_timezone)  # 获取本地时区的当前时间

    # 获取本地时间的时分秒部分
    current_time = local_time.strftime('%H:%M:%S')
    current_time_obj = datetime.strptime(current_time, '%H:%M:%S').time()
    return current_time_obj

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
            print("时间为:", current_time, "总资产为：", asset)

            # Pause for 30 seconds before the next transaction
            time.sleep(50)  # Pause for 50 seconds

        else:
            # If it's outside of trading hours, wait and check again after a short interval
            print("不在交易时间，等待下一个检查...")
            time.sleep(60)  # Pause for 60 seconds before checking again
