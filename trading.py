import akshare as ak
import pandas as pd

# 所有的symbol
symbols = ['sh111001', 'sh113030', 'sh113537', 'sh113582', 'sh113685', 'sh118003', 'sh118026', 
           'sz123035', 'sz123078', 'sz123103', 'sz123184', 'sz123190', 'sz123209', 'sz123227', 
           'sz123228', 'sz123248', 'sz127035', 'sz127072', 'sz127087', 'sz128044', 'sz128076', 
           'sz128083', 'sz128109', 'sz128118']


def get_temp(symbols):
    data_list = []
    
    for symbol in symbols:
        try:
            # 获取数据并取最后一行
            df = ak.bond_zh_hs_cov_min(symbol, period='1', adjust='', 
                                       start_date="1979-09-01 09:32:00", 
                                       end_date="2222-01-01 09:32:00")
            if not df.empty:
                last_row = df.iloc[-1].copy()
                last_row['symbol'] = symbol
                data_list.append(last_row)
        except Exception as e:
            print(f"Error for {symbol}: {e}")
    
    # 合并数据
    temp = pd.DataFrame(data_list).reset_index(drop=True)
    
    # 转换为数值类型
    temp['最新价'] = pd.to_numeric(temp.get('最新价', pd.Series()), errors='coerce')
    temp['成交额'] = pd.to_numeric(temp.get('成交额', pd.Series()), errors='coerce')
    return temp

    
print(get_temp(symbols))
