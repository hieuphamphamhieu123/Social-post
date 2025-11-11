# 📊 Box-EA Backtest Framework

Hệ thống backtest hoàn chỉnh cho **Box-EA** + **AI Market Analyzer**, cho phép bạn test chiến lược trading với AI predictions trên historical data.

## 🎯 Tính năng chính

✅ **Backtest hoàn chỉnh** - Mô phỏng chính xác logic Box-EA
✅ **AI Integration** - Tích hợp AI market range predictions
✅ **Multiple data sources** - CSV, MT5, Yahoo Finance, synthetic data
✅ **Performance metrics** - Profit, Drawdown, Sharpe Ratio, Win Rate, etc.
✅ **Visualization** - Charts, equity curve, drawdown plot
✅ **Parameter optimization** - Tự động tìm parameters tốt nhất
✅ **Strategy comparison** - So sánh multiple strategies

---

## 📁 Cấu trúc

```
backtest/
├── __init__.py              # Package init
├── config.py                # Configuration settings
├── data_loader.py           # Load historical data
├── ai_predictor.py          # AI predictions simulator
├── ea_simulator.py          # Box-EA logic simulator
├── backtest_engine.py       # Main backtest engine
├── performance_analyzer.py  # Performance metrics calculator
├── run_backtest.py          # Entry point script
└── README.md               # This file
```

---

## 🚀 Cài đặt

### 1. Requirements

```bash
pip install pandas numpy loguru matplotlib seaborn tqdm yfinance
```

### 2. Optional: AI Model

Nếu muốn dùng real AI model thay vì rule-based:

```bash
pip install tensorflow scikit-learn joblib
```

---

## 💻 Cách sử dụng

### **Quick Start - Chạy backtest đơn giản**

```bash
cd backtest
python run_backtest.py
```

### **1. Chạy với preset configs**

```bash
# Default strategy
python run_backtest.py --mode default

# Aggressive strategy
python run_backtest.py --mode aggressive

# Conservative strategy
python run_backtest.py --mode conservative
```

### **2. Chạy với custom data**

```bash
# Sử dụng CSV file
python run_backtest.py --mode custom --csv path/to/data.csv

# Sử dụng Yahoo Finance
python run_backtest.py --mode custom --start 2024-01-01 --end 2024-12-31
```

### **3. Parameter optimization**

```bash
python run_backtest.py --mode optimize
```

### **4. So sánh strategies**

```bash
python run_backtest.py --mode compare
```

---

## 📝 Sử dụng trong Python

### Example 1: Basic Backtest

```python
from backtest.config import BacktestConfig
from backtest.backtest_engine import BacktestEngine

# Tạo config
config = BacktestConfig(
    start_date="2024-01-01",
    end_date="2024-12-31",
    initial_balance=10000,
    timeframe="M5",
    use_ai_prediction=True
)

# Khởi tạo engine
engine = BacktestEngine(config)

# Load data
engine.load_data(
    data_source="synthetic",  # hoặc "csv", "mt5", "yahoo"
    base_price=2000.0,
    volatility=0.002
)

# Run backtest
results = engine.run(verbose=True, progress_bar=True)

# Print report
engine.print_report()

# Plot results
engine.plot_results()

# Export results
engine.export_results("my_backtest_results")
```

### Example 2: Load Real Data

```python
# Từ CSV
engine.load_data(
    data_source="csv",
    filepath="XAUUSD_M5_2024.csv"
)

# Từ MT5 CSV
engine.load_data(
    data_source="mt5",
    filepath="XAUUSD_MT5.csv"
)

# Từ Yahoo Finance
engine.load_data(
    data_source="yahoo",
    ticker="GC=F",  # Gold Futures
    start_date="2024-01-01",
    end_date="2024-12-31",
    interval="5m"
)
```

### Example 3: Custom Configuration

```python
config = BacktestConfig(
    # General
    symbol="XAUUSD",
    initial_balance=10000,

    # EA Settings
    default_lot_size=0.01,
    max_orders=15,

    # Period 1
    period1_first_entry_distance=3000,
    period1_extra_distance=300,
    period1_tp=600,

    # Period 2
    period2_first_entry_distance=9000,
    period2_extra_distance=900,
    period2_tp=300,

    # AI
    use_ai_prediction=True,
)
```

### Example 4: Optimization

```python
# Define parameter grid
param_grid = {
    'period1_first_entry_distance': [2000, 3000, 4000],
    'period2_first_entry_distance': [7000, 9000, 11000],
    'period1_tp': [400, 600, 800],
    'max_orders': [10, 15, 20]
}

# Run optimization
best_params, best_result = engine.optimize(
    param_grid=param_grid,
    metric="sharpe_ratio"  # hoặc "total_return_pct", "profit_factor"
)

print(f"Best parameters: {best_params}")
```

---

## 📊 Output & Results

### **Files được tạo ra**

Sau khi chạy backtest, results được lưu vào thư mục `backtest_results/`:

```
backtest_results/
├── equity_curve.csv       # Equity & balance theo thời gian
├── trades_log.csv         # Chi tiết từng trade
├── ai_predictions.csv     # AI predictions history
├── metrics.json          # Tất cả metrics
└── results_plot.png      # Visualization charts
```

### **Metrics được tính toán**

#### 1. Overall Performance
- Initial Balance
- Final Balance
- Final Equity
- Total Return ($)
- Total Return (%)

#### 2. Trade Statistics
- Total Trades
- Winning Trades
- Losing Trades
- Win Rate (%)
- Profit Factor

#### 3. Profit/Loss Analysis
- Gross Profit
- Gross Loss
- Average Win
- Average Loss
- Largest Win
- Largest Loss
- Expectancy

#### 4. Drawdown Analysis
- Max Drawdown ($)
- Max Drawdown (%)
- Max Drawdown Duration
- Current Drawdown

#### 5. Risk Metrics
- Sharpe Ratio
- Sortino Ratio
- Calmar Ratio
- Volatility (%)

#### 6. Time Analysis
- Total Days
- Profitable Days
- Losing Days
- Trades per Day
- Average Trade Duration
- Best Day Profit
- Worst Day Profit

---

## 📈 Visualization

Backtest tự động tạo 6 charts:

1. **Equity & Balance Curve** - Theo dõi equity và balance
2. **Drawdown %** - Visualize drawdown periods
3. **Profit Distribution** - Histogram of trade profits
4. **Cumulative Profit** - Running total của profits
5. **Daily Profit/Loss** - Bar chart daily P&L
6. **Win/Loss Ratio** - Pie chart

---

## 🔧 Configuration Options

Xem file [config.py](config.py) để biết tất cả options.

### **Main Settings**

```python
# Backtest period
start_date = "2024-01-01"
end_date = "2024-12-31"
initial_balance = 10000.0

# EA Settings
default_lot_size = 0.01
max_orders = 15
max_spread = 369

# Profit Targets
daily_profit_target = 1800.0
enable_daily_profit_limit = True

# AI Settings
use_ai_prediction = True
default_market_range = 15000
```

### **Preset Configs**

- `DEFAULT_CONFIG` - Balanced strategy
- `AGGRESSIVE_CONFIG` - Higher risk, more orders
- `CONSERVATIVE_CONFIG` - Lower risk, fewer orders
- `SCALPING_CONFIG` - Short-term, quick profits

---

## 🧪 Testing với data thật

### **Chuẩn bị CSV data**

Format CSV cần có columns:

```csv
datetime,open,high,low,close,volume
2024-01-01 00:00:00,2050.5,2051.2,2049.8,2050.1,1500
2024-01-01 00:05:00,2050.1,2050.9,2049.5,2050.5,1200
...
```

### **Export data từ MT5**

1. Mở MT5, chọn symbol XAUUSD
2. View → Data Window
3. File → Export → Chọn period
4. Save as CSV

### **Sử dụng trong backtest**

```python
engine.load_data(
    data_source="csv",
    filepath="XAUUSD_M5_2024.csv"
)
```

---

## 🤖 AI Predictor Modes

### **1. Rule-based (Default)**

Tính market range từ ATR và time of day:

```python
ai_predictor = AIPredictor(mode="rule_based")
```

### **2. AI Model**

Sử dụng trained LSTM model:

```python
ai_predictor = AIPredictor(
    mode="ai_model",
    model_path="path/to/model"
)
```

### **3. Replay**

Replay historical predictions:

```python
ai_predictor = AIPredictor(mode="replay")
```

---

## 📋 Best Practices

### 1. **Start với synthetic data**
Test logic trước khi dùng real data

### 2. **Validate data quality**
Check null values, OHLC validity

### 3. **Use realistic settings**
Commission, slippage, spread

### 4. **Run optimization carefully**
Grid search có thể lâu với nhiều parameters

### 5. **Check overfitting**
Test trên out-of-sample data

### 6. **Compare strategies**
Chạy multiple configs để tìm best approach

---

## 🐛 Troubleshooting

### **Problem: Import errors**

```bash
# Make sure trong backtest directory
cd backtest

# Hoặc thêm vào Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/Lab-9"
```

### **Problem: No data**

Check data source và dates:
```python
# Validate data
valid, message = loader.validate_data()
print(message)
```

### **Problem: Poor performance**

1. Check EA settings
2. Verify AI predictions are working
3. Review individual trades
4. Compare với benchmark

---

## 📞 Support

Nếu có vấn đề:

1. Check logs trong console
2. Validate input data
3. Review configuration
4. Check [Issues](https://github.com/anthropics/claude-code/issues)

---

## 📄 License

MIT License - Free to use and modify

---

## 🎉 Quick Commands

```bash
# Default backtest
python run_backtest.py

# Aggressive strategy
python run_backtest.py --mode aggressive

# Custom data
python run_backtest.py --mode custom --csv data.csv

# Optimize parameters
python run_backtest.py --mode optimize

# Compare strategies
python run_backtest.py --mode compare
```

---

**Happy Backtesting! 🚀**
