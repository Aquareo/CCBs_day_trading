import akshare as ak
import pandas as pd
import logging

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 所有的symbol
symbols = ['sh111001', 'sh113030', 'sh113537', 'sh113582', 'sh113685', 'sh118003', 'sh118026', 
           'sz123035', 'sz123078', 'sz123103', 'sz123184', 'sz123190', 'sz123209', 'sz123227', 
           'sz123228', 'sz123248', 'sz127035', 'sz127072', 'sz127087', 'sz128044', 'sz128076', 
           'sz128083', 'sz128109', 'sz128118']

data_list = []

for symbol in symbols:
    try:
        # 获取数据并取最后一行
        logging.info(f"Fetching data for symbol: {symbol}")
        df = ak.bond_zh_hs_cov_min(symbol, period='1', adjust='', 
                                    start_date="1979-09-01 09:32:00", 
                                    end_date="2222-01-01 09:32:00")
        if not df.empty:
            last_row = df.iloc[-1].copy()
            logging.info(f"Last row for {symbol}: {last_row}")
            last_row['symbol'] = symbol
            data_list.append(last_row)
        else:
            logging.warning(f"No data found for symbol: {symbol}")
    except Exception as e:
        logging.error(f"Error for {symbol}: {e}")

# 合并数据
temp = pd.DataFrame(data_list).reset_index(drop=True)
logging.info(f"Dataframe constructed with {len(temp)} rows")

# 转换为数值类型
temp['最新价'] = pd.to_numeric(temp.get('最新价', pd.Series()), errors='coerce')
temp['成交额'] = pd.to_numeric(temp.get('成交额', pd.Series()), errors='coerce')

logging.info("Data types conversion completed")

# 打印最终结果
logging.info("Final dataframe:")
logging.info(temp)

# Optionally, if you want to display it
import ace_tools as tools; tools.display_dataframe_to_user(name="Bond Data", dataframe=temp)
