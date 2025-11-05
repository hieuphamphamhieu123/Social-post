//+------------------------------------------------------------------+
//|                                          MQL5_Integration.mq5     |
//|                        AI Market Range Integration for Box-EA     |
//|                        Kết nối với Python AI API                  |
//+------------------------------------------------------------------+
#property copyright "AI Market Analyzer"
#property version   "1.00"
#property strict

// Include thư viện HTTP để gọi REST API
#include <JAson.mqh>  // Hoặc dùng thư viện JSON khác

//--- API Configuration
input string API_URL = "http://127.0.0.1:8000";  // URL của Python API (use IP instead of localhost)
input int API_TIMEOUT = 5000;                     // Timeout cho API call (ms)
input bool USE_AI_PREDICTION = true;              // Sử dụng AI prediction
input int API_UPDATE_INTERVAL = 5;                 // Cập nhật từ AI mỗi 5 giây

//--- Global variables
datetime g_LastAPICall = 0;
double g_LastAIMarketRange = 0;
bool g_APIAvailable = true;
string g_LastAPIError = "";

//+------------------------------------------------------------------+
//| Hàm gọi API để lấy market range từ AI                            |
//+------------------------------------------------------------------+
double GetAIMarketRange()
{
    // Kiểm tra interval
    if(TimeCurrent() - g_LastAPICall < AI_UPDATE_INTERVAL && g_LastAIMarketRange > 0)
    {
        return g_LastAIMarketRange;
    }

    // Call API
    string url = API_URL + "/market-range/simple";
    string headers = "Content-Type: application/json\r\n";
    char post[], result[];
    string result_headers;

    // Reset timeout
    int timeout = API_TIMEOUT;

    // Gọi HTTP GET
    int res = WebRequest(
        "GET",
        url,
        headers,
        timeout,
        post,
        result,
        result_headers
    );

    // Kiểm tra response
    if(res == 200)  // HTTP OK
    {
        // Parse JSON response
        string json_string = CharArrayToString(result);

        // Parse JSON (cần thư viện JSON)
        // Giả sử response format: {"market_range": 15234.5, "timestamp": "..."}

        double market_range = ParseMarketRangeFromJSON(json_string);

        if(market_range > 0)
        {
            g_LastAIMarketRange = market_range;
            g_LastAPICall = TimeCurrent();
            g_APIAvailable = true;
            g_LastAPIError = "";

            Print("AI Market Range updated: ", market_range);
            return market_range;
        }
    }
    else
    {
        // API call failed
        g_APIAvailable = false;
        g_LastAPIError = "API call failed with code: " + IntegerToString(res);
        Print(g_LastAPIError);

        // Fallback to cached value
        if(g_LastAIMarketRange > 0)
        {
            Print("Using cached AI market range: ", g_LastAIMarketRange);
            return g_LastAIMarketRange;
        }
    }

    // Return 0 nếu không có dữ liệu
    return 0;
}

//+------------------------------------------------------------------+
//| Parse market range từ JSON string                                |
//+------------------------------------------------------------------+
double ParseMarketRangeFromJSON(string json_string)
{
    // Simple JSON parsing
    // Tìm "market_range": value

    int start = StringFind(json_string, "\"market_range\":");
    if(start < 0) return 0;

    start += 15;  // Length of "market_range":

    // Skip whitespace
    while(start < StringLen(json_string) &&
          (StringGetCharacter(json_string, start) == ' ' ||
           StringGetCharacter(json_string, start) == '\t'))
    {
        start++;
    }

    // Find end of number
    int end = start;
    while(end < StringLen(json_string))
    {
        ushort c = StringGetCharacter(json_string, end);
        if(c == ',' || c == '}' || c == ' ' || c == '\n' || c == '\r')
            break;
        end++;
    }

    string value_str = StringSubstr(json_string, start, end - start);
    double value = StringToDouble(value_str);

    return value;
}

//+------------------------------------------------------------------+
//| Hàm CalculateMarketRange mới - tích hợp AI                       |
//+------------------------------------------------------------------+
double CalculateMarketRange()
{
    static datetime lastCalculation = 0;
    static double lastRange = 0;

    // Cache trong 5 phút (giống code gốc)
    if(TimeCurrent() - lastCalculation < 300 && lastRange > 0)
    {
        return lastRange;
    }

    double finalRange = 0;

    // 1. Lấy AI prediction nếu enabled
    if(USE_AI_PREDICTION)
    {
        double aiRange = GetAIMarketRange();

        if(aiRange > 0 && g_APIAvailable)
        {
            // Sử dụng AI prediction
            finalRange = aiRange;

            Print("Using AI Market Range: ", finalRange);
        }
    }

    // 2. Fallback: Tính traditional market range (code gốc)
    if(finalRange == 0)
    {
        finalRange = CalculateTraditionalMarketRange();
        Print("Using Traditional Market Range: ", finalRange);
    }

    // Update cache
    lastCalculation = TimeCurrent();
    lastRange = finalRange;

    return finalRange;
}

//+------------------------------------------------------------------+
//| Hàm tính market range traditional (code gốc từ Box-EA)           |
//+------------------------------------------------------------------+
double CalculateTraditionalMarketRange()
{
    MqlRates ratesH1[], ratesH4[], ratesD1[];
    ArraySetAsSeries(ratesH1, true);
    ArraySetAsSeries(ratesH4, true);
    ArraySetAsSeries(ratesD1, true);

    // Lấy dữ liệu từ nhiều timeframe
    if(CopyRates(_Symbol, PERIOD_H1, 0, 10, ratesH1) < 10 ||
       CopyRates(_Symbol, PERIOD_H4, 0, 5, ratesH4) < 5 ||
       CopyRates(_Symbol, PERIOD_D1, 0, 3, ratesD1) < 3)
    {
        return 15000; // Default value
    }

    // Tính range cho từng timeframe
    double h1Range = 0, h4Range = 0, d1Range = 0;

    // H1 Range
    double h1High = ratesH1[0].high;
    double h1Low = ratesH1[0].low;
    for(int i = 0; i < 10; i++)
    {
        if(ratesH1[i].high > h1High) h1High = ratesH1[i].high;
        if(ratesH1[i].low < h1Low) h1Low = ratesH1[i].low;
    }
    h1Range = MathAbs(h1High - h1Low) / _Point;

    // H4 Range
    double h4High = ratesH4[0].high;
    double h4Low = ratesH4[0].low;
    for(int i = 0; i < 5; i++)
    {
        if(ratesH4[i].high > h4High) h4High = ratesH4[i].high;
        if(ratesH4[i].low < h4Low) h4Low = ratesH4[i].low;
    }
    h4Range = MathAbs(h4High - h4Low) / _Point;

    // D1 Range
    double d1High = ratesD1[0].high;
    double d1Low = ratesD1[0].low;
    for(int i = 0; i < 3; i++)
    {
        if(ratesD1[i].high > d1High) d1High = ratesD1[i].high;
        if(ratesD1[i].low < d1Low) d1Low = ratesD1[i].low;
    }
    d1Range = MathAbs(d1High - d1Low) / _Point;

    // Tính trọng số
    double weightedRange;

    // Tính ATR của D1
    double d1ATR = 0;
    for(int i = 1; i < 3; i++)
    {
        d1ATR += MathAbs(ratesD1[i].high - ratesD1[i].low) / _Point;
    }
    d1ATR /= 2;

    // Điều chỉnh trọng số dựa trên ATR
    int MarketRangeThreshold = 15000; // Từ config gốc

    if(d1ATR > MarketRangeThreshold * 1.5)
    {
        // Thị trường biến động mạnh
        weightedRange = (h1Range * 0.5 + h4Range * 0.3 + d1Range * 0.2);
    }
    else if(d1ATR > MarketRangeThreshold)
    {
        // Thị trường biến động vừa
        weightedRange = (h1Range * 0.4 + h4Range * 0.4 + d1Range * 0.2);
    }
    else
    {
        // Thị trường ít biến động
        weightedRange = (h1Range * 0.2 + h4Range * 0.3 + d1Range * 0.5);
    }

    return weightedRange;
}

//+------------------------------------------------------------------+
//| Hàm kiểm tra API health                                          |
//+------------------------------------------------------------------+
bool CheckAPIHealth()
{
    string url = API_URL + "/health";
    string headers = "Content-Type: application/json\r\n";
    char post[], result[];
    string result_headers;

    int res = WebRequest(
        "GET",
        url,
        headers,
        API_TIMEOUT,
        post,
        result,
        result_headers
    );

    if(res == 200)
    {
        g_APIAvailable = true;
        return true;
    }
    else if(res == -1)
    {
        Print("ERROR: WebRequest failed - check if enabled and URL is allowed");
        g_APIAvailable = false;
        return false;
    }
    else
    {
        Print("WARNING: API health check failed with code: ", res);
        g_APIAvailable = false;
        return false;
    }
}

//+------------------------------------------------------------------+
//| Hàm lấy order flow metrics từ API                                |
//+------------------------------------------------------------------+
bool GetOrderFlowMetrics(
    double &buy_volume,
    double &sell_volume,
    double &volume_imbalance,
    double &trend_strength
)
{
    string url = API_URL + "/orderflow/metrics";
    string headers = "Content-Type: application/json\r\n";
    char post[], result[];
    string result_headers;

    int res = WebRequest(
        "GET",
        url,
        headers,
        API_TIMEOUT,
        post,
        result,
        result_headers
    );

    if(res == 200)
    {
        string json_string = CharArrayToString(result);

        // Parse metrics (simplified)
        buy_volume = ParseJSONDouble(json_string, "buy_volume");
        sell_volume = ParseJSONDouble(json_string, "sell_volume");
        volume_imbalance = ParseJSONDouble(json_string, "volume_imbalance");
        trend_strength = ParseJSONDouble(json_string, "volume_imbalance"); // Use as trend

        return true;
    }

    return false;
}

//+------------------------------------------------------------------+
//| Helper: Parse double value từ JSON                               |
//+------------------------------------------------------------------+
double ParseJSONDouble(string json_string, string key)
{
    string search_key = "\"" + key + "\":";
    int start = StringFind(json_string, search_key);

    if(start < 0) return 0;

    start += StringLen(search_key);

    // Skip whitespace
    while(start < StringLen(json_string) &&
          (StringGetCharacter(json_string, start) == ' ' ||
           StringGetCharacter(json_string, start) == '\t'))
    {
        start++;
    }

    // Find end
    int end = start;
    while(end < StringLen(json_string))
    {
        ushort c = StringGetCharacter(json_string, end);
        if(c == ',' || c == '}' || c == ' ' || c == '\n' || c == '\r')
            break;
        end++;
    }

    string value_str = StringSubstr(json_string, start, end - start);
    return StringToDouble(value_str);
}

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("AI Market Range Integration initialized");

    // Note: WebRequest must be manually enabled in MT5 settings
    // Tools -> Options -> Expert Advisors -> Allow WebRequest for listed URL
    Print("Please ensure WebRequest is enabled for: ", API_URL);

    // Test API connection
    if(CheckAPIHealth())
    {
        Print("API connection successful!");
    }
    else
    {
        Print("WARNING: Cannot connect to API. Will use traditional calculation.");
        Print("If this is the first run, please:");
        Print("1. Enable WebRequest in Tools->Options->Expert Advisors");
        Print("2. Add '", API_URL, "' to allowed URLs");
        Print("3. Restart MT5 and try again");
    }

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("AI Market Range Integration deinitialized");
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    // Test: Print market range mỗi 10 giây
    static datetime lastPrint = 0;

    if(TimeCurrent() - lastPrint >= 10)
    {
        double marketRange = CalculateMarketRange();
        Print("Current Market Range: ", marketRange, " | API Status: ", (g_APIAvailable ? "Online" : "Offline"));

        lastPrint = TimeCurrent();
    }
}
//+------------------------------------------------------------------+
