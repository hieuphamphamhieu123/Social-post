# Quick Start Guide

## 5-Minute Setup

### Prerequisites
- Python 3.8+
- MetaTrader 5
- Binance Account (for API key)

### Step 1: Setup Python (2 minutes)

```bash
cd Lab-9\ai_market_analyzer

# Create virtual environment
python -m venv venv

# Activate
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Key (1 minute)

1. Get Binance API key: https://www.binance.com/en/my/settings/api-management
2. Copy `.env.example` to `.env`
3. Add your keys to `.env`:
   ```env
   BINANCE_API_KEY=your_key
   BINANCE_API_SECRET=your_secret
   ```

### Step 3: Start API (30 seconds)

```bash
# Create logs directory
mkdir logs

# Start API
python main.py api
```

Visit: http://localhost:8000/docs

### Step 4: Setup MT5 (1.5 minutes)

1. **Enable WebRequest**:
   - Tools → Options → Expert Advisors
   - Check "Allow WebRequest for listed URL"
   - Add: `http://127.0.0.1:8000` (use IP, not localhost)

2. **Copy integration file**:
   ```
   Copy: AI_MarketRange.mqh
   To: MQL5\Include\
   ```

3. **Modify Box-EA**:

   Add at top:
   ```mql5
   #include <AI_MarketRange.mqh>
   ```

   In `OnInit()`:
   ```mql5
   InitAIIntegration();
   ```

   Rename function (line ~2206):
   ```mql5
   double CalculateMarketRange()
   →
   double CalculateTraditionalMarketRange()
   ```

   Add new wrapper:
   ```mql5
   double CalculateMarketRange() {
       return CalculateMarketRangeWithAI();
   }
   ```

4. **Compile and run**

## Test Installation

```bash
# In new terminal
cd Lab-9\ai_market_analyzer
python test_api.py
```

Expected: All tests pass ✓

## Verify in MT5

Check Experts tab for:
```
AI Market Range Integration initialized
AI API connected successfully!
Current Market Range: 15234.5 | API Status: Online
```

## Done! 🎉

Your EA now uses AI-powered market range analysis!

## Next Steps

1. **Let it run for 24h** to collect training data
2. **Train the model**:
   ```bash
   python main.py train
   ```
3. **Monitor performance** and adjust settings

## Troubleshooting

| Problem | Solution |
|---------|----------|
| API won't start | Check `logs/market_analyzer.log` |
| EA can't connect | Verify WebRequest URL whitelist |
| No predictions | Wait 1-2 minutes for data collection |
| Wrong predictions | Need more training data (24h+) |

## Key URLs

- API Docs: http://localhost:8000/docs (or http://127.0.0.1:8000/docs)
- Health: http://localhost:8000/health
- Market Range: http://localhost:8000/market-range/simple

**Note**: MT5 WebRequest requires IP address: `http://127.0.0.1:8000`

## Support Files

- Full guide: [INSTALLATION.md](INSTALLATION.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Main docs: [README.md](README.md)

---

**Time to profit: ~5 minutes** ⏱️
