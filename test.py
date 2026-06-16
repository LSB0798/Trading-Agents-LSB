
import os
os.environ["FINANCIAL_DATASETS_API_KEY"] = "*****"

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