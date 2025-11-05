//+------------------------------------------------------------------+
//|                                              TEST_AI_EA.mq5      |
//|                        Simple test EA for AI Market Range        |
//+------------------------------------------------------------------+
#property copyright "AI Market Analyzer"
#property version   "1.00"

#include <AI_MarketRange.mqh>

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== TEST AI EA Starting ===");

    // Initialize AI Integration
    if(InitAIIntegration())
    {
        Print("✅ AI Integration initialized successfully");
    }
    else
    {
        Print("❌ AI Integration failed to initialize");
    }

    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    static datetime lastCheck = 0;

    // Test every 10 seconds
    if(TimeCurrent() - lastCheck >= 10)
    {
        Print("--- Testing AI Market Range ---");

        // Get AI market range directly
        double aiRange = GetAIMarketRange();

        if(aiRange > 0)
        {
            Print("✅ AI Market Range: ", aiRange);
            Print("   API Status: ", (g_APIAvailable ? "Online" : "Offline"));
        }
        else
        {
            Print("❌ No AI market range available");
            Print("   API Status: ", (g_APIAvailable ? "Online" : "Offline"));
        }

        lastCheck = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("=== TEST AI EA Stopped ===");
}
//+------------------------------------------------------------------+
