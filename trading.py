import akshare as ak
import pandas as pd

# 所有的symbol
symbols = ['sh111001', 'sh113030', 'sh113537', 'sh113582', 'sh113685', 'sh118003', 'sh118026', 
           'sz123035', 'sz123078', 'sz123103', 'sz123184', 'sz123190', 'sz123209', 'sz123227', 
           'sz123228', 'sz123248', 'sz127035', 'sz127072', 'sz127087', 'sz128044', 'sz128076', 
           'sz128083', 'sz128109', 'sz128118']


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
                print(df, flush=True)
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

temp=get_temp(symbols)
print(temp, flush=True)
