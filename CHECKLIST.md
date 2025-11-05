# Installation & Usage Checklist

## ✅ Pre-Installation

- [ ] Python 3.8+ installed
- [ ] MetaTrader 5 installed
- [ ] Binance account created
- [ ] Git installed (optional)

## ✅ Python Setup

- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created from `.env.example`
- [ ] Binance API key added to `.env`
- [ ] Binance API secret added to `.env`
- [ ] `logs/` directory created

## ✅ API Verification

- [ ] API starts without errors
- [ ] http://localhost:8000/docs accessible
- [ ] http://localhost:8000/health returns "healthy"
- [ ] Data collection starts (wait 2 minutes)
- [ ] http://localhost:8000/market-range returns data
- [ ] `test_api.py` runs successfully

## ✅ MT5 Configuration

- [ ] WebRequest enabled in MT5 settings
- [ ] `http://localhost:8000` added to allowed URLs
- [ ] MT5 restarted after settings change
- [ ] `AI_MarketRange.mqh` copied to MQL5\Include\
- [ ] Box-EA file backed up

## ✅ EA Integration

- [ ] `#include <AI_MarketRange.mqh>` added to Box-EA
- [ ] `InitAIIntegration()` added to OnInit()
- [ ] `CalculateMarketRange()` renamed to `CalculateTraditionalMarketRange()`
- [ ] New wrapper `CalculateMarketRange()` added
- [ ] EA compiles without errors
- [ ] No warnings in compilation

## ✅ EA Testing

- [ ] EA attached to PAXGUSDT chart
- [ ] Experts log shows "AI API connected successfully!"
- [ ] Market range updates appear in log
- [ ] "API Status: Online" appears
- [ ] No error messages in Experts tab
- [ ] EA can fallback to traditional calculation

## ✅ System Verification

- [ ] Python API running
- [ ] MT5 EA running
- [ ] Data flowing from Binance
- [ ] Metrics calculating correctly
- [ ] Predictions updating every 5 seconds
- [ ] EA using AI predictions
- [ ] Fallback works when API stopped

## ✅ Monitoring Setup

- [ ] Log file location confirmed: `ai_market_analyzer/logs/`
- [ ] Can view logs in real-time
- [ ] MT5 Experts tab monitored
- [ ] API endpoints responding

## ✅ Training Preparation (Optional)

- [ ] Data collection running for 24h+
- [ ] Historical data accumulated
- [ ] Model training tested
- [ ] Trained model saved successfully
- [ ] Predictions using trained model

## 🔧 Troubleshooting Checklist

### API Won't Start
- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Port 8000 not in use
- [ ] Binance API keys valid
- [ ] Internet connection active

### EA Can't Connect
- [ ] API is running
- [ ] WebRequest enabled in MT5
- [ ] URL in allowed list
- [ ] Firewall not blocking
- [ ] MT5 restarted after changes

### No Predictions
- [ ] Wait 2-3 minutes after start
- [ ] Check Binance connection
- [ ] Verify data collection in logs
- [ ] API health endpoint returns true

### Predictions Not Updating
- [ ] Check API logs for errors
- [ ] Verify WebSocket connections
- [ ] Test API endpoint directly
- [ ] Restart API if needed

## 📊 Performance Checklist

- [ ] API response time < 100ms
- [ ] Memory usage < 1GB
- [ ] CPU usage reasonable
- [ ] No memory leaks observed
- [ ] Logs not growing excessively

## 🔐 Security Checklist

- [ ] `.env` file not committed to git
- [ ] API keys have read-only permissions
- [ ] API running on localhost only
- [ ] No sensitive data in logs
- [ ] WebRequest URL whitelist configured

## 📝 Documentation Checklist

- [ ] README.md reviewed
- [ ] INSTALLATION.md followed
- [ ] QUICKSTART.md completed
- [ ] ARCHITECTURE.md understood
- [ ] PROJECT_SUMMARY.md read

## 🎯 Final Verification

### API Health Check
```bash
curl http://localhost:8000/health
```
Expected:
```json
{
  "status": "healthy",
  "is_collecting": true,
  "predictor_ready": false,
  "timestamp": "2025-11-05T..."
}
```

### Market Range Check
```bash
curl http://localhost:8000/market-range/simple
```
Expected:
```json
{
  "market_range": 15234.5,
  "timestamp": "2025-11-05T..."
}
```

### EA Log Check
Look for in MT5 Experts tab:
```
AI Market Range Integration initialized
AI API connected successfully!
Current Market Range: 15234.5 | API Status: Online
```

## 🚀 Ready to Trade Checklist

- [ ] All previous checklists completed
- [ ] System running stable for 1+ hour
- [ ] No errors in logs
- [ ] Market range updating correctly
- [ ] EA making trading decisions
- [ ] Risk management configured
- [ ] Account funded appropriately

## 📈 Production Checklist

- [ ] Tested on demo account first
- [ ] 24h+ training data collected
- [ ] Model trained and validated
- [ ] Performance metrics acceptable
- [ ] Backup strategy in place
- [ ] Monitoring alerts configured
- [ ] Documentation accessible

## 🎓 Knowledge Checklist

- [ ] Understand how order flow works
- [ ] Know how AI model predicts
- [ ] Understand fallback mechanism
- [ ] Can read API logs
- [ ] Can interpret EA logs
- [ ] Know how to restart services
- [ ] Can troubleshoot common issues

## 🔄 Maintenance Checklist (Weekly)

- [ ] Check log file sizes
- [ ] Review API performance
- [ ] Verify data collection
- [ ] Check model accuracy
- [ ] Update dependencies if needed
- [ ] Backup configuration
- [ ] Review trading results

## ⚠️ Emergency Checklist

If something goes wrong:

1. **First Response**
   - [ ] Check if API is running
   - [ ] Check if MT5 is connected
   - [ ] Review recent logs

2. **Quick Fixes**
   - [ ] Restart API: `python main.py api`
   - [ ] Restart EA in MT5
   - [ ] Check internet connection

3. **Fallback Plan**
   - [ ] EA will use traditional calculation
   - [ ] No trades lost
   - [ ] System continues functioning

4. **Recovery**
   - [ ] Fix identified issue
   - [ ] Verify system health
   - [ ] Resume AI predictions

## 📊 Success Metrics

After 24 hours of running:

- [ ] Uptime > 95%
- [ ] API response time < 100ms avg
- [ ] Prediction accuracy tested
- [ ] No critical errors
- [ ] Memory usage stable
- [ ] Trading results positive

## 🎉 Completion

When all checklists are ✅:

**🎊 CONGRATULATIONS! 🎊**

Your AI Market Range Analyzer is fully operational!

---

**Date Completed**: __________

**Notes**:
_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

**Next Review Date**: __________

---

**Version**: 1.0.0
**Last Updated**: 2025-11-05
