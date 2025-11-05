# 🔧 Hướng dẫn Restart API để áp dụng code mới

## Vấn đề
API đang chạy với Python bytecode cache cũ, nên code mới chưa được load.

## Giải pháp (chỉ mất 1 phút)

### Bước 1: Stop API hiện tại
1. Tìm cửa sổ console có title **"AI Market API"** hoặc đang chạy `python main.py`
2. Nhấn **Ctrl+C** để dừng
3. Đóng cửa sổ đó lại

### Bước 2: Xóa Python cache
Mở Command Prompt mới và chạy:
```bash
cd c:\Users\Admin\OneDrive\Documents\GitHub\Lab-9
python clear_cache_and_restart.py
```

**HOẶC** xóa thủ công:
1. Mở Explorer → Navigate to `ai_market_analyzer` folder
2. Tìm kiếm tất cả folders tên `__pycache__`
3. Delete tất cả các `__pycache__` folders

### Bước 3: Start API với code mới
Mở Command Prompt mới và chạy:
```bash
cd c:\Users\Admin\OneDrive\Documents\GitHub\Lab-9\ai_market_analyzer
python main.py
```

### Bước 4: Verify (sau 10 giây)
Mở Command Prompt thứ 3 và chạy:
```bash
cd c:\Users\Admin\OneDrive\Documents\GitHub\Lab-9
python test_market_range_updates.py
```

## Kết quả mong đợi
```
[1/10] 20:50:15 | Range: 50000 |
[2/10] 20:50:16 | Range: 48532 | [CHANGED] -1468 (-2.94%)
[3/10] 20:50:17 | Range: 49821 | [CHANGED] +1289 (+2.66%)
...
[SUCCESS] Market range is updating continuously!
```

## Nếu vẫn thấy 3000
Có thể API chưa kết nối được Binance. Check console xem có lỗi không.

Metrics cần có giá trị > 0:
- buy_volume > 0
- sell_volume > 0
- trade_intensity > 0

## Kiểm tra nhanh
```bash
curl http://127.0.0.1:8000/orderflow/metrics
```

Phải thấy:
```json
{
  "buy_volume": 10-50,
  "sell_volume": 10-50,
  "trade_intensity": 5-20,
  ...
}
```

Nếu tất cả = 0 → SimpleCollector chưa lấy được data từ Binance.
