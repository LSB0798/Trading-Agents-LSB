# ValueAgents/valueagents/agents/utils/agent_utils.py
from langchain_core.messages import HumanMessage, RemoveMessage

# Import tools from separate utility files
from valueagents.agents.utils.core_stock_tools import (
    get_stock_data
)
from valueagents.agents.utils.technical_indicators_tools import (
    get_indicators
)
from valueagents.agents.utils.fundamental_data_tools import (
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement
)
from valueagents.agents.utils.news_data_tools import (
    get_news,
    get_insider_transactions,
    get_global_news
)

from valueagents.agents.utils.gnews_data_tools import (
    get_news_gnews,
    get_global_news_gnews,
)

from valueagents.agents.utils.alpha_news_data_tools import (
    get_alpha_news,
    get_alpha_global_news,
)

from valueagents.agents.utils.finnhub_data_tools import (
    get_finnhub_news,
    get_finnhub_global_news,
)

from valueagents.agents.utils.investment_rag import (
    # retrieve_investment_wisdom,
    retrieve_market_wisdom,                 # 市场分析师
    retrieve_sentiment_wisdom,              # 社交媒体分析师
    retrieve_news_wisdom,                   # 新闻分析师
    retrieve_fundamentals_wisdom,           # 基本面分析师
    retrieve_bull_wisdom,                   # Bull Researcher
    retrieve_bear_wisdom,                   # Bear Researcher
    retrieve_research_manager_wisdom,       # Research Manager
    retrieve_trader_wisdom,                 # Trader
    retrieve_risk_wisdom,                   # 风险分析师
    retrieve_portfolio_manager_wisdom,       # Portfolio Manager
)



def get_language_instruction() -> str:
    """Return a prompt instruction for the configured output language.

    Returns empty string when English (default), so no extra tokens are used.
    Only applied to user-facing agents (analysts, portfolio manager).
    Internal debate agents stay in English for reasoning quality.
    """
    from valueagents.dataflows.config import get_config
    lang = get_config().get("output_language", "English")
    if lang.strip().lower() == "english":
        return ""
    return f" Write your entire response in {lang}."


def build_instrument_context(ticker: str) -> str:
    """Describe the exact instrument so agents preserve exchange-qualified tickers."""
    return (
        f"The instrument to analyze is `{ticker}`. "
        "Use this exact ticker in every tool call, report, and recommendation, "
        "preserving any exchange suffix (e.g. `.TO`, `.L`, `.HK`, `.T`)."
    )

def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]

        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages]

        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")

        return {"messages": removal_operations + [placeholder]}

    return delete_messages


        
