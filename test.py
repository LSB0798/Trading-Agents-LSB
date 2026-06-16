"""
import time
from tradingagents.dataflows.y_finance import get_YFin_data_online, get_stock_stats_indicators_window, get_balance_sheet as get_yfinance_balance_sheet, get_cashflow as get_yfinance_cashflow, get_income_statement as get_yfinance_income_statement, get_insider_transactions as get_yfinance_insider_transactions

print("Testing optimized implementation with 30-day lookback:")
start_time = time.time()
result = get_stock_stats_indicators_window("AAPL", "macd", "2024-11-01", 30)
end_time = time.time()

print(f"Execution time: {end_time - start_time:.2f} seconds")
print(f"Result length: {len(result)} characters")
print(result)
"""


'''
import os
os.environ["FINANCIAL_DATASETS_API_KEY"] = "7822668c-eb7d-43b6-bee4-fb31a46e182a"

from cli.utils import select_llm_provider, select_shallow_thinking_agent, select_deep_thinking_agent
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

# 获取用户输入（或直接写死用于测试）
provider, base_url = select_llm_provider()          # 这里会提示输入 URL 和模型名
quick_model = select_shallow_thinking_agent(provider)
deep_model = select_deep_thinking_agent(provider)

config = DEFAULT_CONFIG.copy()
config.update({
    "llm_provider": provider,
    "backend_url": base_url,
    "quick_think_llm": quick_model,
    "deep_think_llm": deep_model,
    "openai_api_key": "dummy",
})

# 只使用 news 分析师
"""
agent_graph：是你之前创建的 TradingAgentsGraph 实例，它内部已经构建好了完整的 LangGraph 工作流
（包含分析师、研究员、交易员、风险分析师、投资组合经理等节点）。
"""
agent_graph = TradingAgentsGraph(selected_analysts=["news"], config=config)

"""
.propagate("AAPL", "2025-01-15")：调用该实例的 propagate 方法，传入两个参数：
"AAPL"：目标股票的代码（苹果公司）。
"2025-01-15"：分析的基准日期（系统会基于该日期获取历史数据，确保没有未来信息泄露）。
"""
final_state, decision = agent_graph.propagate("AAPL", "2025-01-15")

"""
返回值：
    final_state：整个工作流结束后得到的最终状态字典，包含了所有中间报告
        （例如 market_report, sentiment_report, news_report, fundamentals_report），
        辩论历史，风险讨论，以及最终的投资计划 investment_plan 和最终交易决策 final_trade_decision 等。

    decision：是从 final_state["final_trade_decision"] 中提取出的简化交易信号
        （通过内部的 signal_processor 处理，通常返回类似 "BUY", "SELL", "HOLD" 等单词）。
"""
print(decision)

'''





###################################################################################

import os
os.environ["FINANCIAL_DATASETS_API_KEY"] = "7822668c-eb7d-43b6-bee4-fb31a46e182a"

from tradingagents.graph.trading_graph import TradingAgentsGraph
from cli.utils import select_llm_provider, select_shallow_thinking_agent, select_deep_thinking_agent
from tradingagents.default_config import DEFAULT_CONFIG

provider, base_url = select_llm_provider()
quick_model = select_shallow_thinking_agent(provider)
deep_model = select_deep_thinking_agent(provider)

config = DEFAULT_CONFIG.copy()
config.update({
    "llm_provider": provider,
    "backend_url": base_url,
    "quick_think_llm": quick_model,
    "deep_think_llm": deep_model,
    "openai_api_key": "dummy",
})

# 启用大师分析师模式，使用全部（或指定子集）
agent_graph = TradingAgentsGraph(
    use_master_analysts=True,
    master_analysts_list=None,   # 使用全部
    config=config,
)

final_state, decision = agent_graph.propagate("AAPL", "2026-06-11")
print(decision)