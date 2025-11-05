# Hướng dẫn cài đặt chi tiết

## Mục lục
1. [Cài đặt Python Environment](#1-cài-đặt-python-environment)
2. [Cấu hình Binance API](#2-cấu-hình-binance-api)
3. [Chạy API Server](#3-chạy-api-server)
4. [Cài đặt MT5 Integration](#4-cài-đặt-mt5-integration)
5. [Testing](#5-testing)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Cài đặt Python Environment

### Bước 1.1: Cài đặt Python

Nếu chưa có Python, download và cài đặt từ: https://www.python.org/downloads/

**Yêu cầu**: Python 3.8 hoặc cao hơn

Kiểm tra version:
```bash
python --version
```

### Bước 1.2: Tạo Virtual Environment

```bash
cd Lab-9\ai_market_analyzer

# Tạo virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### Bước 1.3: Cài đặt Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Cài đặt requirements
pip install -r requirements.txt
```

**Lưu ý**: Quá trình này có thể mất 5-10 phút tùy vào tốc độ internet.

---

## 2. Cấu hình Binance API

### Bước 2.1: Tạo Binance API Key

1. Đăng nhập vào Binance: https://www.binance.com/
2. Vào **Account** → **API Management**
3. Tạo API key mới:
   - Label: "Market Analyzer" (hoặc tên bất kỳ)
   - **KHÔNG** cần enable trading permissions
   - Chỉ cần **Read** permissions

4. Save API Key và API Secret (chỉ hiện 1 lần!)

### Bước 2.2: Cấu hình API Key

1. Copy file `.env.example` thành `.env`:
```bash
copy .env.example .env
```

2. Mở file `.env` và điền API keys:
```env
BINANCE_API_KEY=your_actual_api_key_here
BINANCE_API_SECRET=your_actual_secret_here
```

**⚠️ BẢO MẬT**: KHÔNG share file `.env` hoặc commit vào git!

---

## 3. Chạy API Server

### Bước 3.1: Tạo thư mục logs

```bash
mkdir logs
```

### Bước 3.2: Start API Server

**Cách 1**: Sử dụng batch file (Windows)
```bash
start_api.bat
```

**Cách 2**: Command line
```bash
python main.py api
```

API sẽ start tại: `http://localhost:8000`

### Bước 3.3: Verify API đang chạy

Mở browser và truy cập:
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

Bạn sẽ thấy response như:
```json
{
  "status": "healthy",
  "is_collecting": true,
  "predictor_ready": false,
  "timestamp": "2025-11-05T10:30:00"
}
```

### Bước 3.4: Test API

Mở terminal mới và chạy:
```bash
cd Lab-9\ai_market_analyzer
python test_api.py
```

---

## 4. Cài đặt MT5 Integration

### Bước 4.1: Enable WebRequest trong MT5

**QUAN TRỌNG**: Bước này bắt buộc!

1. Mở MetaTrader 5
2. Menu: **Tools** → **Options**
3. Tab: **Expert Advisors**
4. Check: ☑ **Allow WebRequest for listed URL**
5. Thêm URL vào danh sách:
   ```
   http://localhost:8000
   ```
6. Click **OK**

### Bước 4.2: Copy files MQL5

**Option 1**: Sử dụng Include File (Khuyến nghị)

1. Copy file `AI_MarketRange.mqh` vào:
   ```
   C:\Users\[YourName]\AppData\Roaming\MetaQuotes\Terminal\[TerminalID]\MQL5\Include\
   ```

2. Mở file `Box-ea` trong MetaEditor

3. Thêm vào đầu file (sau các #property):
   ```mql5
   #include <AI_MarketRange.mqh>
   ```

4. Tìm hàm `OnInit()` và thêm vào cuối:
   ```mql5
   // Initialize AI Integration
   InitAIIntegration();
   ```

5. Tìm hàm `CalculateMarketRange()` (dòng ~2206) và đổi tên:
   ```mql5
   double CalculateTraditionalMarketRange()
   {
       // Code gốc giữ nguyên
       MqlRates ratesH1[], ratesH4[], ratesD1[];
       // ... rest of original code
   }
   ```

6. Thêm hàm wrapper mới ngay sau đó:
   ```mql5
   double CalculateMarketRange()
   {
       return CalculateMarketRangeWithAI();
   }
   ```

**Option 2**: Sử dụng file standalone

1. Copy file `MQL5_Integration.mq5` vào:
   ```
   C:\Users\[YourName]\AppData\Roaming\MetaQuotes\Terminal\[TerminalID]\MQL5\Experts\
   ```

2. Compile trong MetaEditor
3. Chạy EA này thay vì Box-EA gốc

### Bước 4.3: Compile và Test

1. Compile EA trong MetaEditor (F7)
2. Kiểm tra không có errors
3. Attach EA vào chart
4. Kiểm tra log trong **Experts** tab

Bạn sẽ thấy messages như:
```
AI Market Range Integration initialized
AI API connected successfully!
Current Market Range: 15234.5 | API Status: Online
```

---

## 5. Testing

### Test 1: Verify Data Collection

Trong Python terminal:
```bash
python test_api.py
```

Expected output:
- ✓ Health check passed
- ✓ Market range endpoint working
- ✓ Simple market range endpoint working
- ✓ Orderflow metrics endpoint working

### Test 2: Monitor Real-time

```bash
# Windows PowerShell
while($true) {
    curl http://localhost:8000/market-range/simple | ConvertFrom-Json | Format-List
    Start-Sleep -Seconds 5
}
```

### Test 3: Verify EA Integration

1. Attach EA vào PAXGUSDT chart
2. Check **Experts** tab trong MT5
3. Tìm messages:
   ```
   AI Market Range updated: 15234.5
   Using AI Market Range: 15234.5
   ```

### Test 4: Verify EA Trading

1. Đợi EA đặt orders
2. Check comments của orders
3. Verify market range được sử dụng đúng

---

## 6. Troubleshooting

### Problem 1: API không start được

**Error**: `ModuleNotFoundError`

**Solution**:
```bash
# Activate venv
venv\Scripts\activate

# Reinstall requirements
pip install -r requirements.txt
```

---

### Problem 2: Binance connection error

**Error**: `Connection refused` hoặc `Invalid API key`

**Solution**:
1. Verify API key và secret trong `.env`
2. Check API permissions trên Binance
3. Verify internet connection

---

### Problem 3: MT5 WebRequest error

**Error**: `WebRequest not enabled`

**Solution**:
1. Check Tools → Options → Expert Advisors
2. Verify URL được add: `http://localhost:8000`
3. Restart MT5

---

### Problem 4: EA không connect được API

**Error**: `Cannot connect to API`

**Solution**:
1. Verify API đang chạy:
   ```bash
   curl http://localhost:8000/health
   ```
2. Check firewall settings
3. Verify URL trong EA settings

---

### Problem 5: Market range không update

**Symptoms**: Market range giữ nguyên giá trị

**Solution**:
1. Check API logs:
   ```bash
   tail -f logs\market_analyzer.log
   ```
2. Verify Binance data collection:
   ```bash
   curl http://localhost:8000/orderflow/metrics
   ```
3. Restart API nếu cần

---

## 7. Verify Installation

Checklist cuối cùng:

- [ ] Python environment đã setup
- [ ] Dependencies đã cài đặt
- [ ] Binance API keys đã cấu hình
- [ ] API server chạy thành công
- [ ] Test API passed
- [ ] MT5 WebRequest enabled
- [ ] EA compile không lỗi
- [ ] EA connect được API
- [ ] Market range update real-time

Nếu tất cả đều ✓, installation thành công! 🎉

---

## 8. Next Steps

1. **Thu thập training data**:
   ```bash
   python main.py collect
   ```
   Để chạy 24h để thu thập dữ liệu

2. **Train AI model**:
   ```bash
   python main.py train
   ```

3. **Monitor performance**:
   - Check logs
   - Monitor API responses
   - Verify EA trading behavior

4. **Optimize**:
   - Adjust config parameters
   - Retrain model với more data
   - Fine-tune EA settings

---

## Support

Nếu gặp vấn đề không được liệt kê ở đây:

1. Check logs: `logs/market_analyzer.log`
2. Check EA logs trong MT5 Experts tab
3. Review README.md
4. Test từng component riêng lẻ

---

**Good luck with your trading! 🚀**
