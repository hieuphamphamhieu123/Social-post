// =============================================================================
// HÀM ONTICK MỚI - LOGIC RÕ RÀNG, KHÔNG LẶP
// =============================================================================
void OnTick() {
    // =============================================================================
    // 1. KIỂM TRA ĐIỀU KIỆN CƠ BẢN
    // =============================================================================

    UpdateAIThreshold();
    UpdateDynamicSL();

    if(!IsSpreadOK()) return;
    if(!IsAIConnectionOK()) return;
    if(IsWeekendTrading()) return;
    if(EnableNewsProtection && IsWithinNewsTime()) return;

    static int tickCount = 0;
    tickCount++;
    if(tickCount >= 10) {
        CalculateVolumeProfile();
        g_AllowTrading = ShouldAllowTradingByVolume();
        tickCount = 0;
    }
    if(!g_AllowTrading) return;

    // =============================================================================
    // 2. CẬP NHẬT THÔNG TIN THỊ TRƯỜNG
    // =============================================================================

    double currentPrice = GetCleanPrice();

    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);
    static int lastDay = -1;
    if(time_struct.day != lastDay) {
        g_DailyTargetHit = false;
        g_DailyOpenPrice = 0;
        lastDay = time_struct.day;
    }

    UpdateAnchorPrice();
    CountOrdersAndCalculateAverages();
    CountActiveCycles();
    g_DailyProfit = CalculateDailyProfit();

    DetectH1Box();
    double marketRange = CalculateMarketRange();
    g_InsideBox = marketRange;

    // =============================================================================
    // 3. XỬ LÝ CHU KỲ ĐANG ACTIVE (NẾU CÓ LỆNH)
    // =============================================================================

    if(g_TotalOrders_Buy > 0 || g_TotalOrders_Sell > 0) {
        // ĐÃ CÓ LỆNH → CHỈ XỬ LÝ DCA VÀ TP, KHÔNG MỞ CHU KỲ MỚI

        // Xác định loại chu kỳ đang active
        ActiveTradeType activeType = GetActiveTradeType();
        g_ActiveTradeType = activeType;

        // Quản lý DCA thống nhất cho chu kỳ hiện tại
        ManageUnifiedDCA();

        // Quản lý TP
        ModifyOrdersTPEnhanced(currentPrice);

        if(g_TotalOrders_Buy > 0 && CheckAnyTPReached(currentPrice, POSITION_TYPE_BUY)) {
            ResetTrendModeTracking();
        }
        if(g_TotalOrders_Sell > 0 && CheckAnyTPReached(currentPrice, POSITION_TYPE_SELL)) {
            ResetTrendModeTracking();
        }

        HandleCycleCompletion();

        // Reset flags khi không còn lệnh
        if(g_TotalOrders_Buy == 0) canOpenNewTrade_Buy = true;
        if(g_TotalOrders_Sell == 0) canOpenNewTrade_Sell = true;

        HandleMonthEndClosing();
        HandleWeekendClosing();
        return; // QUAN TRỌNG: Return để không chạy logic mở lệnh mới
    }

    // =============================================================================
    // 4. FILTERS & SAFETY (CHỈ CHẠY KHI KHÔNG CÓ LỆNH)
    // =============================================================================

    ResetAfterFullClose();
    if(IsInCooldownPeriod()) return;

    g_AllowedDirection = GetMFIDirection();

    OrderFlowStrength flowStrength = AnalyzeOrderFlowAdvanced();

    DetectNarrowRange();
    if(g_InNarrowRange && !ShouldTradeInNarrowRange(currentPrice)) return;

    // =============================================================================
    // 5. KIỂM TRA LIMITS (CHỈ CHẠY KHI KHÔNG CÓ LỆNH)
    // =============================================================================

    static bool g_DailyProfitActionExecuted = false;
    static datetime g_DailyProfitResetTime = 0;

    if(EnableDailyProfitLimit && g_DailyProfit >= DailyProfitTarget) {
        if(!g_DailyProfitActionExecuted) {
            g_DailyProfitActionExecuted = true;
            g_DailyProfitResetTime = TimeCurrent() + 60;
        }
        if(TimeCurrent() < g_DailyProfitResetTime) return;
        if(TimeCurrent() >= g_DailyProfitResetTime) {
            g_DailyProfit = 0;
            g_DailyProfitActionExecuted = false;
            g_DailyProfitResetTime = 0;
        }
    }

    if(!EnforcePeriodOrderLimits()) return;
    if(!CanOpenMoreOrdersInPeriod()) return;
    if(!HasEnoughTimeForNewOrder()) return;

    // =============================================================================
    // 6. RECOVERY MODE (PRIORITY 1)
    // =============================================================================

    if(g_InRecoveryMode) {
        ManageRecoveryMode();
        if(CheckAndCloseOnRecoveryTarget()) {
            g_HasResumedTrading = false;
        }
        return;
    }

    // =============================================================================
    // 7. MỞ CHU KỲ MỚI - QUYẾT ĐỊNH LOẠI CHU KỲ THEO THỊ TRƯỜNG
    // =============================================================================
    // Phân tích thị trường và quyết định loại chu kỳ phù hợp nhất

    // Phân tích daily momentum
    g_DailyAllowedDirection = AnalyzeDailyMomentum();

    // PRIORITY 1: AI Imbalance Signal (Highest - Strong AI signal)
    // Điều kiện: AI có tín hiệu mạnh, imbalance vượt ngưỡng
    if((EnableBuyOrders || EnableSellOrders) && g_APIAvailable) {
        if(OpenOrderByAIImbalance()) {
            return; // Đã mở lệnh theo AI signal
        }
    }

    // PRIORITY 2: Single Direction (Trend/Breakout)
    // Điều kiện: Market range lớn (> AI threshold) + Daily momentum rõ ràng (không phải BOTH)
    if(marketRange > g_CurrentAIThreshold && g_DailyAllowedDirection != DAILY_BOTH) {
        HandleSingleDirectionEntry();
        return;
    }

    // PRIORITY 3: Zone Strategy (Sideway trong zones rõ ràng)
    // Điều kiện: Range vừa phải (zone activation range đến AI threshold * 1.5)
    if(EnablePriceZoneStrategy) {
        if(marketRange >= ZoneActivationRange && marketRange < g_CurrentAIThreshold * 1.5) {
            RunFlexibleZoneStrategy();
            return;
        }
    }

    // PRIORITY 4: Regular Sideway DCA (Inside box, narrow range)
    // Điều kiện: Market range nhỏ (< AI threshold)
    if(marketRange < g_CurrentAIThreshold) {
        // Market trong box hẹp
        if(EnableBuyOrders && EnableSellOrders) {
            // Cho phép cả Buy và Sell → Dùng Parallel DCA
            HandleParallelDCA(currentPrice);
        } else {
            // Chỉ 1 hướng hoặc không có orders → Regular DCA
            HandleRegularDCA();
        }
        return;
    }

    // PRIORITY 5: Fallback - No clear signal
    // Không có điều kiện nào phù hợp → Chờ tín hiệu rõ ràng hơn
    // (Không làm gì cả)

    HandleMonthEndClosing();
    HandleWeekendClosing();
}
