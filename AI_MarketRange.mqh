//+------------------------------------------------------------------+
//|                                           AI_MarketRange.mqh      |
//|                        Include file for AI Market Range          |
//|                        Dùng để thêm vào Box-EA gốc                |
//+------------------------------------------------------------------+
#property copyright "AI Market Analyzer"
#property version   "1.00"
#property strict

//--- API Configuration
string g_API_URL = "http://127.0.0.1:8000";  // Use IP instead of localhost for MT5 compatibility
int g_API_TIMEOUT = 5000;
bool g_USE_AI_PREDICTION = true;
int g_AI_UPDATE_INTERVAL = 1;  // Updated to 1 second for more responsive updates
// How often to recalc traditional market range when AI not used (seconds)
int g_TRADITIONAL_UPDATE_INTERVAL = 1;  // Updated to 1 second for consistency

//--- IMPORTANT: PAXG/USDT vs XAU/USD Correlation Notice
// PAXG (Paxos Gold) trên Binance và XAU/USD có correlation nhưng KHÔNG giống nhau 100%:
// - PAXG: Crypto token, 24/7 trading, crypto market dynamics
// - XAU/USD: Spot gold, 24/5 trading, forex market dynamics
// - Correlation thường cao (0.8-0.95) nhưng có thể diverge trong market stress
// KHUYẾN NGHỊ: Chỉ dùng làm reference, KHÔNG dùng trực tiếp cho production XAU/USD trading!

//--- Global variables for AI integration
datetime g_LastAPICall = 0;
double g_LastAIMarketRange = 0;
bool g_APIAvailable = true;
string g_LastAPIError = "";
// Record what value was actually used by CalculateMarketRangeWithAI()
bool g_LastMarketRangeWasAI = false;
double g_LastUsedMarketRange = 0;
// Imbalance tracking
double g_LastAIImbalance = 0;
datetime g_LastImbalanceUpdate = 0;
// Record what value was actually used by CalculateMarketRangeWithAI()
double CalculateMarketRangeWithAI()
{
    static datetime lastLogTime = 0;
    static bool firstCall = true;

    // Log lần đầu tiên hàm được gọi
    if(firstCall)
    {
        Print("🚀 CalculateMarketRangeWithAI() called for the first time!");
        Print("   g_USE_AI_PREDICTION: ", g_USE_AI_PREDICTION);
        Print("   g_APIAvailable: ", g_APIAvailable);
        Print("   IsRunningInTester: ", IsRunningInTester());
        firstCall = false;
    }

    // Removed static cache to allow more responsive updates

    double finalRange = 0;
    bool usedAI = false;

    // 1. Thử lấy từ AI nếu enabled (AI helper itself caches using g_AI_UPDATE_INTERVAL)
    if(g_USE_AI_PREDICTION && g_APIAvailable && !IsRunningInTester())
    {
        double aiRange = GetAIMarketRange();

        if(aiRange > 0)
        {
            finalRange = aiRange;
            usedAI = true;
        }
        else
        {
            // If AI returned 0 (no data), fallback to traditional calculation
            finalRange = CalculateTraditionalMarketRange();
            usedAI = false;
        }
    }
    else
    {
        // If AI disabled or API unavailable, use traditional calculation
        finalRange = CalculateTraditionalMarketRange();
        usedAI = false;
    }

    // Log immediately when source changes or every update interval
    if(lastLogTime == 0 || TimeCurrent() - lastLogTime > g_TRADITIONAL_UPDATE_INTERVAL || (usedAI && TimeCurrent() - lastLogTime > g_AI_UPDATE_INTERVAL))
    {
        if(usedAI)
        {
            Print("✅ AI Market Range: ", finalRange, " (Updated every ", g_AI_UPDATE_INTERVAL, "s)");
            Print("   API Status: Online");
        }
        else
        {
            Print("⚠️ Using Traditional Market Range: ", finalRange);
            Print("   API Status: ", (g_APIAvailable ? "Online" : "Offline"));
        }
        lastLogTime = TimeCurrent();
    }

    // Expose what was used so EA can know if AI was applied
    g_LastMarketRangeWasAI = usedAI;
    g_LastUsedMarketRange = finalRange;

    return finalRange;
}

// Parse market range từ JSON string (Simple parser)
double ParseMarketRangeFromJSON(string json_string)
{
    int start = StringFind(json_string, "\"market_range\":");
    if(start < 0) return 0;

    start += 15; // length of '"market_range":'

    while(start < StringLen(json_string) &&
          (StringGetCharacter(json_string, start) == ' ' ||
           StringGetCharacter(json_string, start) == '\t'))
    {
        start++;
    }

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

// Gọi API để lấy AI market range
double GetAIMarketRange()
{
    // CACHE REMOVED: Always fetch fresh data for real-time updates
    // Only rate-limit if called multiple times within same second
    static datetime lastSecond = 0;
    static double lastValueInSecond = 0;

    datetime currentSecond = TimeCurrent();

    // If called multiple times in same second, return same value to avoid spam
    if(currentSecond == lastSecond && lastValueInSecond > 0)
    {
        Print("⚡ Returning same-second cached value: ", lastValueInSecond);
        return lastValueInSecond;
    }

    string url = g_API_URL + "/market-range/simple";
    string headers = "Content-Type: application/json\r\n";
    char post[], result[];
    string result_headers;

    Print("🔄 [", TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS), "] Calling AI API: ", url);

    int res = WebRequest(
        "GET",
        url,
        headers,
        g_API_TIMEOUT,
        post,
        result,
        result_headers
    );

    Print("📡 API Response Code: ", res);

    if(res == 200)
    {
        string json_string = CharArrayToString(result);
        Print("📦 JSON Response: ", json_string);

        double market_range = ParseMarketRangeFromJSON(json_string);

        if(market_range > 0)
        {
            g_LastAIMarketRange = market_range;
            g_LastAPICall = TimeCurrent();
            g_APIAvailable = true;
            lastSecond = currentSecond;
            lastValueInSecond = market_range;
            Print("✅ [FRESH] AI Market Range Retrieved: ", market_range, " at ", TimeToString(TimeCurrent(), TIME_SECONDS));
            return market_range;
        }
    }
    else
    {
        g_APIAvailable = false;
        Print("❌ API Call Failed - Code: ", res);

        // Only use old cache as last resort
        if(g_LastAIMarketRange > 0)
        {
            Print("⚠️ API failed, using last known value: ", g_LastAIMarketRange);
            return g_LastAIMarketRange;
        }
    }

    return 0;
}

//+------------------------------------------------------------------+
//| Initialize AI integration                                         |
//+------------------------------------------------------------------+
bool InitAIIntegration()
{
    // Note: WebRequest must be manually enabled in MT5 settings:
    // Tools -> Options -> Expert Advisors -> Allow WebRequest for listed URL
    // Add these URLs:
    //   http://127.0.0.1:8000
    //   http://localhost:8000
    // (Use IP address instead of 'localhost' for better MT5 compatibility)

    Print("========================================");
    Print("🤖 Initializing AI Integration...");
    Print("API URL: ", g_API_URL);
    Print("Imbalance Endpoint: ", g_API_URL + "/orderflow/metrics");
    Print("Current Symbol: ", _Symbol);
    Print("========================================");

    // Warning về correlation
    if(StringFind(_Symbol, "XAU") >= 0 || StringFind(_Symbol, "GOLD") >= 0 || StringFind(_Symbol, "GC") >= 0)
    {
        Print("⚠️⚠️⚠️ CORRELATION WARNING ⚠️⚠️⚠️");
        Print("Trading ", _Symbol, " but using PAXG/USDT orderflow data!");
        Print("PAXG and ", _Symbol, " have correlation but NOT identical!");
        Print("Use for REFERENCE only, not production trading!");
        Print("========================================");
    }

    // Test connection
    string url = g_API_URL + "/health";
    string headers = "Content-Type: application/json\r\n";
    char post[], result[];
    string result_headers;

    int res = WebRequest(
        "GET",
        url,
        headers,
        g_API_TIMEOUT,
        post,
        result,
        result_headers
    );

    if(res == 200)
    {
        g_APIAvailable = true;
        Print("AI API connected successfully!");
        return true;
    }
    else if(res == -1)
    {
        Print("ERROR: WebRequest not enabled or URL not in allowed list!");
        Print("Please add '", g_API_URL, "' to allowed URLs in MT5 settings");
        g_APIAvailable = false;
        return false;
    }
    else
    {
        Print("WARNING: Cannot connect to AI API (error code: ", res, ")");
        Print("Make sure Python API is running at: ", g_API_URL);
        g_APIAvailable = false;
        return false;
    }
}

//+------------------------------------------------------------------+
//| REPLACEMENT for CalculateMarketRange() in Box-EA                 |
//| Thay thế hàm CalculateMarketRange() gốc bằng hàm này             |
//+------------------------------------------------------------------+
/*
   HƯỚNG DẪN SỬ DỤNG:

   1. Thêm include vào đầu file Box-EA:
      #include "AI_MarketRange.mqh"

   2. Trong OnInit(), thêm:
      InitAIIntegration();

   3. THAY THẾ hàm CalculateMarketRange() gốc (từ dòng 2206)
      bằng hàm CalculateMarketRangeWithAI() bên dưới

      HOẶC

      Đổi tên hàm gốc thành CalculateTraditionalMarketRange()
      và tạo wrapper mới như dưới đây
*/

// Forward declaration - sẽ được định nghĩa trong Box-EA
double CalculateTraditionalMarketRange();

// Hàm này sẽ THAY THẾ hàm CalculateMarketRange() gốc

//+------------------------------------------------------------------+
//| Parse imbalance từ JSON string                                    |
//+------------------------------------------------------------------+
double ParseImbalanceFromJSON(string json_string)
{
    Print("🔍 [DEBUG] Parsing Imbalance from JSON: ", json_string);

    // Danh sách các key có thể có (ưu tiên volume_imbalance trước)
    string keys[] = {"volume_imbalance", "order_book_imbalance", "imbalance", "order_imbalance", "order_flow_imbalance", "net_imbalance", "buy_sell_imbalance"};
    int start = -1;
    int keyLength = 0;

    // Thử từng key
    for(int i = 0; i < ArraySize(keys); i++)
    {
        string searchKey = "\"" + keys[i] + "\":";
        start = StringFind(json_string, searchKey);

        if(start >= 0)
        {
            keyLength = StringLen(searchKey);
            Print("🔍 [DEBUG] Found key: ", keys[i]);
            break;
        }
    }

    // Nếu không tìm thấy key nào
    if(start < 0)
    {
        Print("❌ [DEBUG] No imbalance key found in JSON");
        return 0;
    }

    start += keyLength;

    // Skip whitespace
    while(start < StringLen(json_string) &&
          (StringGetCharacter(json_string, start) == ' ' ||
           StringGetCharacter(json_string, start) == '\t'))
    {
        start++;
    }

    int end = start;
    while(end < StringLen(json_string))
    {
        ushort c = StringGetCharacter(json_string, end);
        // Allow minus sign and decimal point
        if(c == ',' || c == '}' || c == ' ' || c == '\n' || c == '\r' || c == '\t')
            break;
        end++;
    }

    string value_str = StringSubstr(json_string, start, end - start);

    // Remove any quotes if value is string
    StringReplace(value_str, "\"", "");
    StringTrimLeft(value_str);
    StringTrimRight(value_str);

    double result = StringToDouble(value_str);

    Print("🔍 [DEBUG] Parsed value_str: '", value_str, "' → double: ", result);

    return result;
}

//+------------------------------------------------------------------+
//| Lấy AI Imbalance từ API                                           |
//+------------------------------------------------------------------+
double GetAIImbalance()
{
    // Cache trong 1 giây để tránh gọi API quá nhiều
    static datetime lastSecond = 0;
    static double lastValueInSecond = 0;

    datetime currentSecond = TimeCurrent();

    // Nếu gọi nhiều lần trong cùng 1 giây, trả về giá trị đã cache
    if(currentSecond == lastSecond && lastValueInSecond != 0)
    {
        return lastValueInSecond;
    }

    // FIX: Dùng endpoint đúng cho orderflow metrics
    string url = g_API_URL + "/orderflow/metrics";
    string headers = "Content-Type: application/json\r\n";
    char post[], result[];
    string result_headers;

    Print("🔄 [", TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS), "] Getting AI Imbalance from: ", url);

    int res = WebRequest(
        "GET",
        url,
        headers,
        g_API_TIMEOUT,
        post,
        result,
        result_headers
    );

    if(res == 200)
    {
        string json_string = CharArrayToString(result);
        Print("📦 JSON Response for Imbalance: ", json_string);

        double imbalance = ParseImbalanceFromJSON(json_string);

        g_LastAIImbalance = imbalance;
        g_LastImbalanceUpdate = TimeCurrent();
        g_APIAvailable = true;
        lastSecond = currentSecond;
        lastValueInSecond = imbalance;

        Print("✅ AI Imbalance Retrieved: ", imbalance, " at ", TimeToString(TimeCurrent(), TIME_SECONDS));
        return imbalance;
    }
    else
    {
        g_APIAvailable = false;
        Print("❌ API Call Failed for Imbalance - Code: ", res);

        // Sử dụng giá trị cũ nếu có
        if(g_LastImbalanceUpdate > 0 && TimeCurrent() - g_LastImbalanceUpdate < 300) // 5 phút
        {
            Print("⚠️ API failed, using last known imbalance: ", g_LastAIImbalance);
            return g_LastAIImbalance;
        }
    }

    return 0; // Không có dữ liệu
}


//+------------------------------------------------------------------+
