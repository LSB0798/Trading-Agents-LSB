from langchain_core.tools import tool
from typing import Annotated
from valueagents.dataflows.interface import route_to_vendor

@tool
def get_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"] = 30,
) -> str:
    """
    Retrieve a single technical indicator for a given ticker symbol.
    Uses the configured technical_indicators vendor.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        indicator (str): A single technical indicator name, e.g. 'rsi', 'macd'. Call this tool once per indicator.
        curr_date (str): The current trading date you are trading on, YYYY-mm-dd
        look_back_days (int): How many days to look back, default is 30
    Returns:
        str: A formatted dataframe containing the technical indicators for the specified ticker symbol and indicator.
    """
    # LLMs sometimes pass multiple indicators as a comma-separated string;
    # split and process each individually.
    indicators = [i.strip().lower() for i in indicator.split(",") if i.strip()]
    results = []
    for ind in indicators:
        try:
            results.append(route_to_vendor("get_indicators", symbol, ind, curr_date, look_back_days))
        except ValueError as e:
            results.append(str(e))
    # return "\n\n".join(results)
    result = "\n\n".join(results)

    # # ========== 添加打印 ==========
    # print("="*30 + "TECHNICAL INDICATORS (Alpha Vantage)" + "="*30)
    # print(f"📊 [Indicators] Raw data for {symbol} (indicators: {', '.join(indicators)})")
    # print(f"   Date: {curr_date}, look_back: {look_back_days}d")
    # print(f"   Total characters: {len(result)}")
    # preview = result[:200].replace('\n', ' ')
    # print(f"   Preview: {preview}...")
    # print("="*30 + "TECHNICAL INDICATORS END" + "="*30)
    # # ==============================

    return result

"""
分析结果总体评估
    合理且质量良好。这份报告基于 get_stock_data（股价数据）和 8 个技术指标（get_indicators），生成了结构清晰、逻辑严密的技术分析报告。

细节检查
    1. 数据来源匹配
        报告引用的关键数据均来自工具返回的原始数据：

            报告引用	数据来源	验证
            50 SMA: 369.47	close_50_sma	✅ 预览中显示 2026-06-29: 369.47
            200 SMA: 314.07	close_200_sma	✅ 预览中显示 2026-06-29: 314.07
            10 EMA: 352.29	close_10_ema	✅ 预览中显示 2026-06-29: 352.29
            MACD: -6.78	macd	✅ 预览中显示 2026-06-29: -6.78
            MACD 信号线: -4.60	macds	✅ 预览中显示 2026-06-29: -4.60
            RSI: 45.60	rsi	✅ 预览中显示 2026-06-29: 45.60
            ATR: 12.24	atr	✅ 预览中显示 2026-06-29: 12.24
            布林带中轨: 359.43	boll	✅ 预览中显示 2026-06-29: 359.43
        所有数据与工具返回的原始数据一致，没有捏造数据。

    2. 逻辑连贯性
        报告从以下维度展开分析，逻辑链条清晰：
            趋势方向（50/200 SMA 黄金交叉 → 长期看涨）
            短期动量（10 EMA 滞后 → 短期弱势）
            动量指标（MACD 看跌但趋平 → 可能反转）
            波动率（ATR 偏高 → 建议动态止损）
            超买超卖（RSI 从超卖反弹 → 短期反弹可能）
            综合结论（HOLD，等待方向明确）
        最终结论 HOLD 与前面的分析一致（趋势向上但短期信号混杂），没有矛盾。

    3. 工具调用行为
        第一轮：LLM 调用 get_stock_data 获取基础价格数据。

        第二轮：LLM 并行调用了 8 个 get_indicators，分别获取：
            趋势类：close_50_sma, close_200_sma, close_10_ema
            动量类：macd, macds, rsi
            波动类：boll, atr

        这 8 个指标覆盖了趋势、动量、波动三个维度，符合系统提示中“选择最多 8 个指标提供互补洞察”的要求，选择合理，没有冗余。

    4. 报告结构与要求
        ✅ 包含 Markdown 表格（关键指标表）
        ✅ 包含 FINAL TRANSACTION PROPOSAL: HOLD
        ✅ 包含具体数值支撑（369.47, 314.07, -6.78 等）
        ✅ 包含可操作的交易建议（入场/出场策略、止损位）

    5. 值得注意的观察
        打印顺序混乱：TECHNICAL INDICATORS 的打印块重复出现多次，且内容交错。
                    这是因为 LLM 并行调用了 8 个 get_indicators，且每个调用都独立打印，导致输出交错。
                    这是并发执行的正常现象，不影响分析质量。

        STOCK DATA 未出现在日志中：您的日志片段中未包含 STOCK DATA 的打印，说明 get_stock_data 的打印可能被截断了，
                                或者工具调用没有触发打印。建议检查 core_stock_tools.py 中 get_stock_data 的打印是否正常。

        报告中的价格引用：报告引用了 337.39（6月26日收盘价）和 385（6月16日高点），
                        这些数据应来自 get_stock_data，但由于 STOCK DATA 打印缺失，无法直接验证。
"""