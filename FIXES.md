# Common Fixes

## Fix: TERMINAL_WEBREQUEST undeclared identifier

### Lỗi
```
undeclared identifier	AI_MarketRange.mqh	108	29
cannot convert enum	AI_MarketRange.mqh	108	29
```

### Nguyên nhân
`TERMINAL_WEBREQUEST` không tồn tại trong MQL5. WebRequest settings không thể check programmatically.

### Giải pháp
✅ **Đã fix trong version mới**

Files đã được cập nhật:
- [AI_MarketRange.mqh](AI_MarketRange.mqh)
- [MQL5_Integration.mq5](MQL5_Integration.mq5)

### Cách sử dụng
1. Copy lại files đã fix
2. Compile lại trong MetaEditor
3. Enable WebRequest thủ công trong MT5:
   - Tools → Options → Expert Advisors
   - Check "Allow WebRequest for listed URL"
   - Add: `http://localhost:8000`
   - Click OK
4. Restart MT5

---

## Fix: WebRequest Error -1

### Lỗi trong Experts tab
```
ERROR: WebRequest failed - check if enabled and URL is allowed
```

### Nguyên nhân
WebRequest chưa được enable hoặc URL chưa được thêm vào whitelist.

### Giải pháp

#### Bước 1: Enable WebRequest
1. Mở MT5
2. Menu: **Tools** → **Options**
3. Tab: **Expert Advisors**
4. Check: ☑ **Allow WebRequest for listed URL**

#### Bước 2: Add URL
1. Trong box bên dưới, thêm:
   ```
   http://127.0.0.1:8000
   ```
   **QUAN TRỌNG**:
   - Sử dụng `127.0.0.1` thay vì `localhost` (MT5 không nhận localhost)
   - KHÔNG có dấu `/` ở cuối URL

2. Click **OK** (không nhấn Enter)

#### Bước 3: Restart
1. Đóng MT5 hoàn toàn
2. Mở lại MT5
3. Attach EA vào chart

#### Bước 4: Verify
Check Experts tab, phải thấy:
```
AI Market Range Integration initialized
AI API connected successfully!
```

---

## Fix: Cannot connect to API

### Lỗi
```
WARNING: Cannot connect to API. Will use traditional calculation.
```

### Nguyên nhân
Python API chưa chạy hoặc không accessible.

### Giải pháp

#### Check 1: API có đang chạy không?
```bash
# Test bằng browser
http://localhost:8000/health

# Hoặc curl
curl http://localhost:8000/health
```

Nếu không response → API chưa chạy.

#### Check 2: Start API
```bash
cd Lab-9\ai_market_analyzer
python main.py api
```

Hoặc dùng batch file:
```bash
start_api.bat
```

#### Check 3: Verify API health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "is_collecting": true,
  "predictor_ready": false,
  "timestamp": "2025-11-05T..."
}
```

#### Check 4: Test from EA
1. Restart EA trong MT5
2. Check Experts tab
3. Phải thấy: "API connection successful!"

---

## Fix: Port 8000 already in use

### Lỗi khi start API
```
Error: [Errno 10048] Only one usage of each socket address...
```

### Nguyên nhân
Port 8000 đã được process khác sử dụng.

### Giải pháp

#### Option 1: Stop process đang dùng port 8000
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID [PID_NUMBER] /F
```

#### Option 2: Đổi port
1. Edit `config/config.py`:
   ```python
   API_PORT = 8001  # Đổi sang port khác
   ```

2. Update trong EA files:
   ```mql5
   string g_API_URL = "http://localhost:8001";  // AI_MarketRange.mqh
   input string API_URL = "http://localhost:8001";  // MQL5_Integration.mq5
   ```

3. Add port mới vào MT5 allowed URLs:
   ```
   http://localhost:8001
   ```

---

## Fix: Missing dependencies

### Lỗi khi start API
```
ModuleNotFoundError: No module named 'xxx'
```

### Giải pháp

```bash
# Activate virtual environment
cd ai_market_analyzer
venv\Scripts\activate

# Reinstall all dependencies
pip install -r requirements.txt --upgrade

# Verify installation
python -c "import fastapi; import tensorflow; print('OK')"
```

---

## Fix: Binance connection error

### Lỗi trong logs
```
Connection refused
Invalid API key
```

### Giải pháp

#### Check 1: API keys đúng chưa?
```bash
# Check .env file
type .env
```

Phải có:
```env
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
```

#### Check 2: API key có permissions?
1. Login Binance
2. Account → API Management
3. Check permissions:
   - ✅ Enable Reading (required)
   - ❌ Enable Spot & Margin Trading (not needed)

#### Check 3: API key restrictions
1. Check IP whitelist (nếu có)
2. Remove restrictions hoặc add your IP

#### Check 4: Test connection
```python
from binance.client import Client
client = Client(api_key, api_secret)
print(client.ping())
```

---

## Fix: Compilation errors in MQL5

### Error: Cannot open include file
```
cannot open include file 'AI_MarketRange.mqh'
```

### Giải pháp
1. Copy `AI_MarketRange.mqh` vào đúng thư mục:
   ```
   C:\Users\[YourName]\AppData\Roaming\MetaQuotes\Terminal\[TerminalID]\MQL5\Include\
   ```

2. Hoặc dùng relative path trong Box-EA:
   ```mql5
   #include <AI_MarketRange.mqh>  // Nếu file trong Include/
   // hoặc
   #include "AI_MarketRange.mqh"  // Nếu file cùng thư mục với EA
   ```

---

## Fix: EA không sử dụng AI prediction

### Symptoms
EA chạy nhưng luôn dùng traditional calculation.

### Debug steps

#### Check 1: API available?
Trong Experts tab, tìm:
```
API Status: Online
```

Nếu thấy "Offline" → fix API connection first.

#### Check 2: Predictions updating?
```
Current Market Range: 15234.5 | API Status: Online
```

Nếu số không đổi → check API logs.

#### Check 3: API logs
```bash
tail -f logs/market_analyzer.log
```

Phải thấy:
```
Market Range updated: 15234.5
```

#### Check 4: Test API directly
```bash
curl http://localhost:8000/market-range/simple
```

Phải return:
```json
{
  "market_range": 15234.5,
  "timestamp": "..."
}
```

---

## Fix: High memory usage

### Problem
Python process dùng > 2GB RAM.

### Giải pháp

#### Option 1: Giảm buffer sizes
Edit `config/config.py`:
```python
TRADE_STREAM_BUFFER = 500  # Giảm từ 1000
FEATURE_WINDOW = 50        # Giảm từ 100
```

#### Option 2: Clear old data
Restart API định kỳ (mỗi 24h).

#### Option 3: Monitor memory
```python
import psutil
process = psutil.Process()
print(process.memory_info().rss / 1024 / 1024, "MB")
```

---

## Quick Troubleshooting Checklist

### Python API
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] `.env` file configured
- [ ] Port 8000 available
- [ ] API starts without errors
- [ ] http://localhost:8000/health returns 200

### MT5 EA
- [ ] WebRequest enabled
- [ ] URL in allowed list
- [ ] EA compiles without errors
- [ ] EA attached to chart
- [ ] Experts tab shows "API connected"

### Connection
- [ ] Python API running
- [ ] MT5 EA running
- [ ] Same machine (localhost)
- [ ] No firewall blocking
- [ ] No proxy issues

### Data Flow
- [ ] Binance connection OK
- [ ] Data collecting
- [ ] Metrics calculating
- [ ] Predictions updating
- [ ] EA receiving predictions

---

## Still Having Issues?

### Step 1: Check ALL logs
```bash
# Python logs
tail -f ai_market_analyzer/logs/market_analyzer.log

# MT5 logs
# Check Experts tab in Terminal window
```

### Step 2: Test components individually

**Test API:**
```bash
python test_api.py
```

**Test Binance:**
```bash
python -c "from data.binance_collector import *; c = BinanceOrderFlowCollector(); print('OK')"
```

**Test WebRequest:**
```mql5
// In MetaEditor, create test script
string url = "http://localhost:8000/health";
char post[], result[];
string headers = "Content-Type: application/json\r\n";
string result_headers;
int res = WebRequest("GET", url, headers, 5000, post, result, result_headers);
Print("Result: ", res);
```

### Step 3: Fresh start
```bash
# 1. Stop everything
# 2. Close MT5
# 3. Stop Python API (Ctrl+C)
# 4. Restart Python API
python main.py api
# 5. Wait for "Data collection started"
# 6. Open MT5
# 7. Attach EA
# 8. Check logs
```

### Step 4: Verify installation
Use [CHECKLIST.md](CHECKLIST.md) to verify every step.

---

**Need more help?**
- Review [INSTALLATION.md](INSTALLATION.md)
- Check [README.md](README.md)
- See [ARCHITECTURE.md](ARCHITECTURE.md) for system design

---

**Version**: 1.0.1 (Fixed TERMINAL_WEBREQUEST issue)
**Last Updated**: 2025-11-05
