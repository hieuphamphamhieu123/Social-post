# 🚀 HƯỚNG DẪN SỬ DỤNG BACKTEST FRAMEWORK

## ✅ HỆ THỐNG ĐÃ HOÀN TẤT!

Bạn giờ có một **hệ thống backtest hoàn chỉnh** để test chiến lược Box-EA + AI Market Analyzer!

---

## 📁 CẤU TRÚC PROJECT

```
Lab-9/
├── Box-ea                          # EA gốc (MQL5)
├── AI_MarketRange.mqh             # AI integration cho EA
├── ai_market_analyzer/            # Python AI server
│   ├── api/
│   ├── data/
│   ├── models/
│   └── main.py
└── backtest/                      # ⭐ BACKTEST FRAMEWORK (MỚI!)
    ├── config.py                  # Configuration
    ├── data_loader.py             # Load market data
    ├── ai_predictor.py            # AI simulation
    ├── ea_simulator.py            # EA logic simulator
    ├── backtest_engine.py         # Main engine
    ├── performance_analyzer.py    # Metrics & reports
    ├── run_backtest.py           # Entry point
    ├── example_backtest.py       # Examples
    ├── quick_test.py             # Quick test
    └── README.md                 # Documentation
```

---

## 🎯 CÁCH SỬ DỤNG

### **1. Cài đặt dependencies**

```bash
pip install -r requirements_backtest.txt
```

Hoặc:

```bash
pip install pandas numpy loguru matplotlib seaborn tqdm yfinance
```

---

### **2. Quick Start - Test ngay**

```bash
cd backtest
python quick_test.py
```

Sẽ chạy backtest 1 tuần để verify system hoạt động.

---

### **3. Chạy backtest đầy đủ**

#### **Option 1: Dùng command line**

```bash
# Default strategy
python run_backtest.py

# Aggressive strategy
python run_backtest.py --mode aggressive

# Conservative strategy
python run_backtest.py --mode conservative

# Custom với CSV data
python run_backtest.py --mode custom --csv path/to/data.csv

# Optimization
python run_backtest.py --mode optimize

# So sánh strategies
python run_backtest.py --mode compare
```

#### **Option 2: Dùng example script**

```bash
python example_backtest.py
```

Chọn từ menu:
1. Simple Backtest
2. Aggressive Strategy
3. Custom Parameters
4. Parameter Optimization
5. Strategy Comparison
6. AI-Enhanced Backtest
7. Run ALL examples

#### **Option 3: Viết code Python**

```python
from backtest.config import BacktestConfig
from backtest.backtest_engine import BacktestEngine

# Tạo config
config = BacktestConfig(
    start_date="2024-01-01",
    end_date="2024-12-31",
    initial_balance=10000,
    use_ai_prediction=True
)

# Khởi tạo engine
engine = BacktestEngine(config)

# Load data
engine.load_data(data_source="synthetic")

# Run backtest
results = engine.run()

# Xem kết quả
engine.print_report()
engine.plot_results()
engine.export_results("my_results")
```

---

## 📊 SỬ DỤNG DATA THẬT

### **Method 1: CSV File**

Chuẩn bị file CSV với format:

```csv
datetime,open,high,low,close,volume
2024-01-01 00:00:00,2050.5,2051.2,2049.8,2050.1,1500
2024-01-01 00:05:00,2050.1,2050.9,2049.5,2050.5,1200
...
```

Load vào backtest:

```python
engine.load_data(
    data_source="csv",
    filepath="XAUUSD_M5_2024.csv"
)
```

### **Method 2: MT5 CSV Export**

1. Mở MT5
2. Chọn XAUUSD
3. View → Data Window
4. File → Export
5. Chọn period và save as CSV

Load:

```python
engine.load_data(
    data_source="mt5",
    filepath="XAUUSD_MT5.csv"
)
```

### **Method 3: Yahoo Finance (Gold Futures)**

```python
engine.load_data(
    data_source="yahoo",
    ticker="GC=F",  # Gold Futures
    start_date="2024-01-01",
    end_date="2024-12-31",
    interval="5m"
)
```

---

## 🔧 CUSTOMIZATION

### **Thay đổi EA settings**

```python
config = BacktestConfig(
    # General
    default_lot_size=0.02,
    max_orders=20,

    # Period 1 (Asian session)
    period1_first_entry_distance=2500,
    period1_tp=500,
    period1_max_orders=15,

    # Period 2 (London session)
    period2_first_entry_distance=8000,
    period2_tp=400,
    period2_max_orders=12,

    # AI
    use_ai_prediction=True,
)
```

### **Optimization**

```python
param_grid = {
    'period1_first_entry_distance': [2000, 3000, 4000],
    'period2_first_entry_distance': [7000, 9000, 11000],
    'period1_tp': [400, 600, 800],
    'max_orders': [10, 15, 20]
}

best_params, best_result = engine.optimize(
    param_grid=param_grid,
    metric="sharpe_ratio"  # hoặc "total_return_pct"
)
```

---

## 📈 KẾT QUẢ & METRICS

Sau khi chạy, bạn sẽ có:

### **Console Output**
- Overall Performance (Return, Balance, Equity)
- Trade Statistics (Win rate, Profit Factor)
- Profit/Loss Analysis
- Drawdown Analysis
- Risk Metrics (Sharpe, Sortino, Calmar)
- Time Analysis

### **Files được tạo** (trong `backtest_results/`)
```
backtest_results/
├── equity_curve.csv       # Equity & balance theo time
├── trades_log.csv         # Chi tiết từng trade
├── ai_predictions.csv     # AI predictions history
├── metrics.json          # All metrics
└── results_plot.png      # 6 charts visualization
```

### **Metrics chính**
- **Total Return %** - Lợi nhuận tổng
- **Max Drawdown %** - Sụt giảm tối đa
- **Win Rate %** - Tỷ lệ thắng
- **Profit Factor** - Tỷ lệ profit/loss
- **Sharpe Ratio** - Risk-adjusted return
- **Expectancy** - Expected profit per trade

---

## 💡 TIPS & BEST PRACTICES

### ✅ DO:
- Bắt đầu với synthetic data để test
- Validate data trước khi backtest
- Dùng realistic settings (commission, slippage)
- Test trên out-of-sample data
- So sánh multiple strategies
- Check equity curve & drawdown

### ❌ DON'T:
- Over-optimize (overfitting)
- Ignore transaction costs
- Test trên data quá ngắn
- Dùng parameters không realistic
- Bỏ qua risk metrics

---

## 🔍 TROUBLESHOOTING

### **"No trades executed"**
Có thể do:
- Price không đi xa anchor price đủ để trigger
- First entry distance quá lớn
- Daily profit target hit quá sớm

**Fix:** Giảm `period1_first_entry_distance` hoặc tăng volatility

### **"Data validation failed"**
Check:
- CSV format đúng không
- Có null values không
- OHLC data hợp lệ không (High >= Low, etc.)

### **"Import errors"**
```bash
# Make sure trong backtest directory
cd backtest

# Install dependencies
pip install -r ../requirements_backtest.txt
```

---

## 📚 THAM KHẢO

- **README.md** trong `backtest/` - Full documentation
- **example_backtest.py** - 6 examples chi tiết
- **quick_test.py** - Quick verification

---

## 🎯 WORKFLOW ĐỀ XUẤT

1. **Test basic** - Chạy `quick_test.py`
2. **Run examples** - Chạy `example_backtest.py`
3. **Load real data** - Từ CSV hoặc MT5
4. **Customize config** - Điều chỉnh EA settings
5. **Run backtest** - Full period test
6. **Analyze results** - Review metrics & charts
7. **Optimize** - Tìm best parameters
8. **Compare strategies** - Test multiple configs
9. **Forward test** - Test out-of-sample
10. **Live trade** (nếu results tốt)

---

## 📞 KẾT LUẬN

Bạn giờ có:

✅ **Backtest framework hoàn chỉnh**
✅ **Mô phỏng Box-EA logic chính xác**
✅ **AI integration** (rule-based + model support)
✅ **Multiple data sources** (CSV, MT5, Yahoo, synthetic)
✅ **Comprehensive metrics** (20+ metrics)
✅ **Visualization** (6 charts)
✅ **Optimization engine**
✅ **Strategy comparison**

**Bạn có thể backtest toàn bộ hệ thống EA + AI ngay bây giờ!**

---

## 🚀 NEXT STEPS

1. Chạy backtest với data thật (2024 data)
2. So sánh AI vs non-AI strategies
3. Optimize parameters cho từng period
4. Test trên multiple symbols (không chỉ XAUUSD)
5. Forward test kết quả

**Happy Backtesting! 📊💰**

---

_Created with ❤️ for automated trading excellence_
