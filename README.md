# CCBs Day Trading and Backtesting

This project implements day trading strategies and backtesting models for financial markets using Python. It includes the following strategies:

## Files

- **day_trading.py**: 
  - **Strategy 1: Moving Average Crossover**  
    A basic strategy where a short-term moving average crosses over a long-term moving average, indicating buy or sell signals.

- **main.py**:
  - **Strategy 1: Moving Average Crossover**  
    This strategy combines short and long-term moving averages to determine buy and sell signals.
  - **Strategy 2: Relative Strength Index (RSI)**  
    The RSI strategy uses overbought and oversold conditions (typically RSI values above 70 and below 30) to determine potential entry or exit points.
  - **Strategy 3: Combination of Strategy 1 and Strategy 2**  
    A hybrid strategy that combines both moving average crossovers and RSI conditions to refine trade signals.

- **trading.py**:  
  - **Volume-Based Strategy**  
    A volume strategy that takes advantage of unusual volume spikes to enter or exit positions. This strategy is a unique and critical part of the backtesting framework.

## Setup

To get started, you'll need to install the required dependencies. Make sure you have the following Python packages installed:

```bash
pip install akshare pandas pytz
