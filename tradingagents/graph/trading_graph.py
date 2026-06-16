# TradingAgents/graph/trading_graph.py

import os
from pathlib import Path
import json
from datetime import date
from typing import Dict, Any, Tuple, List, Optional

from langgraph.prebuilt import ToolNode

from tradingagents.llm_clients import create_llm_client

from tradingagents.agents import *
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.memory import FinancialSituationMemory
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from tradingagents.dataflows.config import set_config

# Import the new abstract tool methods from agent_utils
from tradingagents.agents.utils.agent_utils import (
    get_stock_data,
    get_indicators,
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement,
    get_news,
    get_insider_transactions,
    get_global_news,
    # retrieve_investment_wisdom,
    retrieve_market_wisdom,
    retrieve_sentiment_wisdom,
    retrieve_news_wisdom,
    retrieve_fundamentals_wisdom,
)

from .conditional_logic import ConditionalLogic
from .setup import GraphSetup
from .propagation import Propagator
from .reflection import Reflector
from .signal_processing import SignalProcessor


class TradingAgentsGraph:
    """Main class that orchestrates the trading agents framework."""

    def __init__(
        self,
        selected_analysts=["market", "social", "news", "fundamentals"],
        use_master_analysts=False,         # 新增
        master_analysts_list=None,         # 新增，可选
        debug=False,
        config: Dict[str, Any] = None,
        callbacks: Optional[List] = None,
    ):
        """Initialize the trading agents graph and components.

        Args:
            selected_analysts: List of analyst types to include
            debug: Whether to run in debug mode
            config: Configuration dictionary. If None, uses default config
            callbacks: Optional list of callback handlers (e.g., for tracking LLM/tool stats)
        """
        self.debug = debug
        self.config = config or DEFAULT_CONFIG
        self.callbacks = callbacks or []

        # Update the interface's config
        set_config(self.config)

        # Create necessary directories
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # Initialize LLMs with provider-specific thinking configuration
        llm_kwargs = self._get_provider_kwargs()

        # Add callbacks to kwargs if provided (passed to LLM constructor)
        if self.callbacks:
            llm_kwargs["callbacks"] = self.callbacks

        deep_client = create_llm_client(
            provider=self.config["llm_provider"],
            model=self.config["deep_think_llm"],
            base_url=self.config.get("backend_url"),
            **llm_kwargs,
        )
        quick_client = create_llm_client(
            provider=self.config["llm_provider"],
            model=self.config["quick_think_llm"],
            base_url=self.config.get("backend_url"),
            **llm_kwargs,
        )

        self.deep_thinking_llm = deep_client.get_llm()
        self.quick_thinking_llm = quick_client.get_llm()
        
        # Initialize memories
        """
        FinancialSituationMemory 是存储/检索组件，不是 Agent
                                 基于 BM25 算法的文本记忆检索系统，
                                 算法：BM25（Best Matching 25），经典的信息检索排名函数。
        核心作用
            存储历史情景与建议对：通过 add_situations(situations_and_advice) 方法，接收一个包含
                                 (情景描述, 对应建议) 的元组列表，将其存入内部文档库 self.documents 和建议库 self.recommendations。
            根据当前情景检索相似记忆：调用 get_memories(current_situation, n_matches) 时，
                                    使用 BM25 算法将当前情景文本与已存储的 documents 进行词汇匹配，
                                    返回最相似的 n_matches 条历史记录，并附带相似度分数（0-1），供 Agent 参考。"""
        self.bull_memory = FinancialSituationMemory("bull_memory", self.config) # （多头研究员记忆）
        self.bear_memory = FinancialSituationMemory("bear_memory", self.config) # （空头研究员记忆）
        self.trader_memory = FinancialSituationMemory("trader_memory", self.config) # （交易员记忆）
        self.invest_judge_memory = FinancialSituationMemory("invest_judge_memory", self.config) # （研究经理记忆）
        self.portfolio_manager_memory = FinancialSituationMemory("portfolio_manager_memory", self.config) # （投资组合经理记忆）

        # Create tool nodes
        self.tool_nodes = self._create_tool_nodes()

        # Initialize components
        """ 创建条件逻辑控制器（ConditionalLogic），用于管理多 Agent 工作流中的路由决策。
        具体作用：
            根据用户在 CLI 中选择的 research_depth（研究深度）参数（1、3 或 5），设置：
                max_debate_rounds：研究团队（Bull ↔ Bear）的最大辩论轮数。
                max_risk_discuss_rounds：风险团队（Aggressive ↔ Conservative ↔ Neutral）的最大讨论轮数。
            该控制器实例随后被传递给 GraphSetup，在构建 LangGraph 工作流时，条件边（conditional edges）会调用其内部方法（如 should_continue_debate、should_continue_risk_analysis），用于决定：
                辩论是否继续进行（下一回合由哪位研究员发言）。
                辩论何时终止（移交至研究经理或投资组合经理）。
        概括：管理“谁下一个发言”以及“何时进入下一阶段”的决策逻辑单元，依赖辩论轮次上限作为停止条件。 """
        self.conditional_logic = ConditionalLogic(
            max_debate_rounds=self.config["max_debate_rounds"],
            max_risk_discuss_rounds=self.config["max_risk_discuss_rounds"],
        )

        """构建 LangGraph 工作流
        通过 GraphSetup 类调用 setup_graph(selected_analysts) 方法，
        根据选中的分析师列表动态生成包含 12 个潜在 Agent 节点 的有向图（StateGraph）。
        该方法会添加所有研究、交易、风险、组合经理节点，并按硬编码逻辑连接它们
        （分析师顺序执行 → 研究团队辩论 → 交易员 → 风险团队循环辩论 → 组合经理）。
        最终调用 compile() 得到一个可执行的 LangGraph 实例，赋值给 self.graph。"""
        """
        self.quick_thinking_llm : callbacks=[<cli.stats_handler.StatsCallbackHandler object at 0x76d859a6d550>] client=<openai.resources.chat.completions.completions.Completions object at 0x76d859278910> async_client=<openai.resources.chat.completions.completions.AsyncCompletions object at 0x76d859278cd0> root_client=<openai.OpenAI object at 0x76d859278690> root_async_client=<openai.AsyncOpenAI object at 0x76d859278a50> model_name='qwen3-moe' model_kwargs={} openai_api_key=SecretStr('**********') openai_api_base='http://10.20.223.89:61253/v1' reasoning_effort='high' use_responses_api=False
        self.deep_thinking_llm  : callbacks=[<cli.stats_handler.StatsCallbackHandler object at 0x76d859a6d550>] client=<openai.resources.chat.completions.completions.Completions object at 0x76d859a0ea50> async_client=<openai.resources.chat.completions.completions.AsyncCompletions object at 0x76d859918050> root_client=<openai.OpenAI object at 0x76d859a6ea50> root_async_client=<openai.AsyncOpenAI object at 0x76d8599182f0> model_name='qwen3-moe' model_kwargs={} openai_api_key=SecretStr('**********') openai_api_base='http://10.20.223.89:61253/v1' reasoning_effort='high' use_responses_api=False
        self.tool_nodes : {'market': tools(tags=None, recurse=True, explode_args=False, func_accepts={'config': ('N/A', <class 'inspect._empty'>), 'runtime': ('N/A', <class 'inspect._empty'>)}, _tools_by_name={'get_stock_data': StructuredTool(name='get_stock_data', description='Retrieve stock price data (OHLCV) for a given ticker symbol.\nUses the configured core_stock_apis vendor.\nArgs:\n    symbol (str): Ticker symbol of the company, e.g. AAPL, TSM\n    start_date (str): Start date in yyyy-mm-dd format\n    end_date (str): End date in yyyy-mm-dd format\nReturns:\n    str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.', args_schema=<class 'langchain_core.utils.pydantic.get_stock_data'>, func=<function get_stock_data at 0x76d8b99df6a0>), 'get_indicators': StructuredTool(name='get_indicators', description="Retrieve a single technical indicator for a given ticker symbol.\nUses the configured technical_indicators vendor.\nArgs:\n    symbol (str): Ticker symbol of the company, e.g. AAPL, TSM\n    indicator (str): A single technical indicator name, e.g. 'rsi', 'macd'. Call this tool once per indicator.\n    curr_date (str): The current trading date you are trading on, YYYY-mm-dd\n    look_back_days (int): How many days to look back, default is 30\nReturns:\n    str: A formatted dataframe containing the technical indicators for the specified ticker symbol and indicator.", args_schema=<class 'langchain_core.utils.pydantic.get_indicators'>, func=<function get_indicators at 0x76d8bcf99580>)}, _injected_args={'get_stock_data': _InjectedArgs(state={}, store=None, runtime=None, all_injected_keys=set()), 'get_indicators': _InjectedArgs(state={}, store=None, runtime=None, all_injected_keys=set())}, _handle_tool_errors=<function _default_handle_tool_errors at 0x76d8bcf73b00>, _messages_key='messages', _wrap_tool_call=None, _awrap_tool_call=None), 'social': tools(tags=None, recurse=True, explode_args=False, func_accepts={'config': ('N/A', <class 'inspect._empty'>), 'runtime': ('N/A', <class 'inspect._empty'>)}, _tools_by_name={'get_news': StructuredTool(name='get_news', description='Retrieve news data for a given ticker symbol.\nUses the configured news_data vendor.\nArgs:\n    ticker (str): Ticker symbol\n    start_date (str): Start date in yyyy-mm-dd format\n    end_date (str): End date in yyyy-mm-dd format\nReturns:\n    str: A formatted string containing news data', args_schema=<class 'langchain_core.utils.pydantic.get_news'>, func=<function get_news at 0x76d859f3b6a0>)}, _injected_args={'get_news': _InjectedArgs(state={}, store=None, runtime=None, all_injected_keys=set())}, _handle_tool_errors=<function _default_handle_tool_errors at 0x76d8bcf73b00>, _messages_key='messages', _wrap_tool_call=None, _awrap_tool_call=None), 'news': tools(tags=None, recurse=True, explode_args=False, func_accepts={'config': ('N/A', <class 'inspect._empty'>), 'runtime': ('N/A', <class 'inspect._empty'>)}, _tools_by_name={'get_news': StructuredTool(name='get_news', description='Retrieve news data for a given ticker symbol.\nUses the configured news_data vendor.\nArgs:\n    ticker (str): Ticker symbol\n    start_date (str): Start date in yyyy-mm-dd format\n    end_date (str): End date in yyyy-mm-dd format\nReturns:\n    str: A formatted string containing news data', args_schema=<class 'langchain_core.utils.pydantic.get_news'>, func=<function get_news at 0x76d859f3b6a0>), 'get_global_news': StructuredTool(name='get_global_news', description='Retrieve global news data.\nUses the configured news_data vendor.\nArgs:\n    curr_date (str): Current date in yyyy-mm-dd format\n    look_back_days (int): Number of days to look back (default 7)\n    limit (int): Maximum number of articles to return (default 5)\nReturns:\n    str: A formatted string containing global news data', args_schema=<class 'langchain_core.utils.pydantic.get_global_news'>, func=<function get_global_news at 0x76d859f649a0>), 'get_insider_transactions': StructuredTool(name='get_insider_transactions', description='Retrieve insider transaction information about a company.\nUses the configured news_data vendor.\nArgs:\n    ticker (str): Ticker symbol of the company\nReturns:\n    str: A report of insider transaction data', args_schema=<class 'langchain_core.utils.pydantic.get_insider_transactions'>, func=<function get_insider_transactions at 0x76d859f3b920>)}, _injected_args={'get_news': _InjectedArgs(state={}, store=None, runtime=None, all_injected_keys=set()), 'get_global_news': _InjectedArgs(state={}, store=None, runtime=None, all_injected_keys=set()), 'get_insider_transactions': _InjectedArgs(state={}, store=None, runtime=None, all_injected_keys=set())}, _handle_tool_errors=<function _default_handle_tool_errors at 0x76d8bcf73b00>, _messages_key='messages', _wrap_tool_call=None, _awrap_tool_call=None), 'fundamentals': tools(tags=None, recurse=True, explode_args=False, func_accepts={'config': ('N/A', <class 'inspect._empty'>), 'runtime': ('N/A', <class 'inspect._empty'>)}, _tools_by_name={'get_fundamentals': StructuredTool(name='get_fundamentals', description='Retrieve comprehensive fundamental data for a given ticker symbol.\nUses the configured fundamental_data vendor.\nArgs:\n    ticker (str): Ticker symbol of the company\n    curr_date (str): Current date you are trading at, yyyy-mm-dd\nReturns:\n    str: A formatted report containing comprehensive fundamental data', args_schema=<class 'langchain_core.utils.pydantic.get_fundamentals'>, func=<function get_fundamentals at 0x76d859f3b880>), 'get_balance_sheet': StructuredTool(name='get_balance_sheet', description='Retrieve balance sheet data for a given ticker symbol.\nUses the configured fundamental_data vendor.\nArgs:\n    ticker (str): Ticker symbol of the company\n    freq (str): Reporting frequency: annual/quarterly (default quarterly)\n    curr_date (str): Current date you are trading at, yyyy-mm-dd\nReturns:\n    str: A formatted report containing balance sheet data', args_schema=<class 'langchain_core.utils.pydantic.get_balance_sheet'>, func=<function get_balance_sheet at 0x76d859f3b7e0>), 'get_cashflow': StructuredTool(name='get_cashflow', description='Retrieve cash flow statement data for a given ticker symbol.\nUses the configured fundamental_data vendor.\nArgs:\n    ticker (str): Ticker symbol of the company\n    freq (str): Reporting frequency: annual/quarterly (default quarterly)\n    curr_date (str): Current date you are trading at, yyyy-mm-dd\nReturns:\n    str: A formatted report containing cash flow statement data', args_schema=<class 'langchain_core.utils.pydantic.get_cashflow'>, func=<function get_cashflow at 0x76d859f3b4c0>), 'get_income_statement': StructuredTool(name='get_income_statement', description='Retrieve income statement data for a given ticker symbol.\nUses the configured fundamental_data vendor.\nArgs:\n    ticker (str): Ticker symbol of the company\n    freq (str): Reporting frequency: annual/quarterly (default quarterly)\n    curr_date (str): Current date you are trading at, yyyy-mm-dd\nReturns:\n    str: A formatted report containing income statement data', args_schema=<class 'langchain_core.utils.pydantic.get_income_statement'>, func=<function get_income_statement at 0x76d859f3be20>)}, _injected_args={'get_fundamentals': _InjectedArgs(state={}, store=None, runtime=None, all_injected_keys=set()), 'get_balance_sheet': _InjectedArgs(state={}, store=None, runtime=None, all_injected_keys=set()), 'get_cashflow': _InjectedArgs(state={}, store=None, runtime=None, all_injected_keys=set()), 'get_income_statement': _InjectedArgs(state={}, store=None, runtime=None, all_injected_keys=set())}, _handle_tool_errors=<function _default_handle_tool_errors at 0x76d8bcf73b00>, _messages_key='messages', _wrap_tool_call=None, _awrap_tool_call=None)}
        self.bull_memory : <tradingagents.agents.utils.memory.FinancialSituationMemory object at 0x76d859918440>
        self.bear_memory : <tradingagents.agents.utils.memory.FinancialSituationMemory object at 0x76d859278e10>
        self.trader_memory : <tradingagents.agents.utils.memory.FinancialSituationMemory object at 0x76d859278f50>
        self.invest_judge_memory : <tradingagents.agents.utils.memory.FinancialSituationMemory object at 0x76d859401f30>
        self.portfolio_manager_memory : <tradingagents.agents.utils.memory.FinancialSituationMemory object at 0x76d8594023f0>
        self.conditional_logic : <tradingagents.graph.conditional_logic.ConditionalLogic object at 0x76d859918ad0> """
        self.graph_setup = GraphSetup(
            self.quick_thinking_llm,
            self.deep_thinking_llm,
            self.tool_nodes,
            self.bull_memory,
            self.bear_memory,
            self.trader_memory,
            self.invest_judge_memory,
            self.portfolio_manager_memory,
            self.conditional_logic,
        )

        # 根据开关确定最终的分析师列表
        if use_master_analysts:
            if master_analysts_list is None:
                master_analysts_list = [
                    "ben_graham", "warren_buffett", "peter_lynch", "phil_fisher",
                    "charlie_munger", "michael_burry", "aswath_damodaran", "cathie_wood",
                    "bill_ackman", "rakesh_jhunjhunwala", "mohnish_pabrai", "nassim_taleb",
                    "stanley_druckenmiller", "technical_analyst", "fundamentals_analyst",
                    "growth_analyst", "news_sentiment_analyst", "sentiment_analyst", "valuation_analyst"
                ]
            final_analysts = ["news"] + master_analysts_list
        else:
            final_analysts = selected_analysts

        self.propagator = Propagator()
        self.reflector = Reflector(self.quick_thinking_llm)
        self.signal_processor = SignalProcessor(self.quick_thinking_llm)

        # State tracking
        self.curr_state = None
        self.ticker = None
        self.log_states_dict = {}  # date to full state dict

        # Set up the graph
        # self.graph = self.graph_setup.setup_graph(selected_analysts)
        # 设置工作流，传递 use_master_analysts 标志
        self.graph = self.graph_setup.setup_graph(final_analysts, use_master_analysts=use_master_analysts)

    def _get_provider_kwargs(self) -> Dict[str, Any]:
        """Get provider-specific kwargs for LLM client creation."""
        kwargs = {}
        provider = self.config.get("llm_provider", "").lower()

        if provider == "google":
            thinking_level = self.config.get("google_thinking_level")
            if thinking_level:
                kwargs["thinking_level"] = thinking_level

        elif provider == "openai":
            reasoning_effort = self.config.get("openai_reasoning_effort")
            if reasoning_effort:
                kwargs["reasoning_effort"] = reasoning_effort

        elif provider == "anthropic":
            effort = self.config.get("anthropic_effort")
            if effort:
                kwargs["effort"] = effort

        return kwargs

    def _create_tool_nodes(self) -> Dict[str, ToolNode]:
        """Create tool nodes for different data sources using abstract methods."""
        return {
            "market": ToolNode(
                [
                    # Core stock data tools
                    get_stock_data,
                    # Technical indicators
                    get_indicators,
                    # investment rag
                    # retrieve_investment_wisdom,
                    retrieve_market_wisdom,
                ]
            ),
            "social": ToolNode(
                [
                    # News tools for social media analysis
                    get_news,
                    retrieve_sentiment_wisdom,
                ]
            ),
            "news": ToolNode(
                [
                    # News and insider information
                    get_news,
                    get_global_news,
                    get_insider_transactions,
                    retrieve_news_wisdom,
                ]
            ),
            "fundamentals": ToolNode(
                [
                    # Fundamental analysis tools
                    get_fundamentals,
                    get_balance_sheet,
                    get_cashflow,
                    get_income_statement,
                    retrieve_fundamentals_wisdom,
                ]
            ),
        }

    def propagate(self, company_name, trade_date):
        """Run the trading agents graph for a company on a specific date."""

        self.ticker = company_name

        # Initialize state
        init_agent_state = self.propagator.create_initial_state(
            company_name, trade_date
        )
        args = self.propagator.get_graph_args()

        if self.debug:
            # Debug mode with tracing
            trace = []
            for chunk in self.graph.stream(init_agent_state, **args):
                if len(chunk["messages"]) == 0:
                    pass
                else:
                    chunk["messages"][-1].pretty_print()
                    trace.append(chunk)

            final_state = trace[-1]
        else:
            # Standard mode without tracing
            final_state = self.graph.invoke(init_agent_state, **args)

        # Store current state for reflection
        self.curr_state = final_state

        # Log state
        self._log_state(trade_date, final_state)

        # Return decision and processed signal
        return final_state, self.process_signal(final_state["final_trade_decision"])

    def _log_state(self, trade_date, final_state):
        """Log the final state to a JSON file."""
        self.log_states_dict[str(trade_date)] = {
            "company_of_interest": final_state["company_of_interest"],
            "trade_date": final_state["trade_date"],
            "market_report": final_state["market_report"],
            "sentiment_report": final_state["sentiment_report"],
            "news_report": final_state["news_report"],
            "fundamentals_report": final_state["fundamentals_report"],
            "investment_debate_state": {
                "bull_history": final_state["investment_debate_state"]["bull_history"],
                "bear_history": final_state["investment_debate_state"]["bear_history"],
                "history": final_state["investment_debate_state"]["history"],
                "current_response": final_state["investment_debate_state"][
                    "current_response"
                ],
                "judge_decision": final_state["investment_debate_state"][
                    "judge_decision"
                ],
            },
            "trader_investment_decision": final_state["trader_investment_plan"],
            "risk_debate_state": {
                "aggressive_history": final_state["risk_debate_state"]["aggressive_history"],
                "conservative_history": final_state["risk_debate_state"]["conservative_history"],
                "neutral_history": final_state["risk_debate_state"]["neutral_history"],
                "history": final_state["risk_debate_state"]["history"],
                "judge_decision": final_state["risk_debate_state"]["judge_decision"],
            },
            "investment_plan": final_state["investment_plan"],
            "final_trade_decision": final_state["final_trade_decision"],
        }

        # Save to file
        directory = Path(self.config["results_dir"]) / self.ticker / "TradingAgentsStrategy_logs"
        directory.mkdir(parents=True, exist_ok=True)

        log_path = directory / f"full_states_log_{trade_date}.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(self.log_states_dict[str(trade_date)], f, indent=4)

    def reflect_and_remember(self, returns_losses):
        """Reflect on decisions and update memory based on returns."""
        self.reflector.reflect_bull_researcher(
            self.curr_state, returns_losses, self.bull_memory
        )
        self.reflector.reflect_bear_researcher(
            self.curr_state, returns_losses, self.bear_memory
        )
        self.reflector.reflect_trader(
            self.curr_state, returns_losses, self.trader_memory
        )
        self.reflector.reflect_invest_judge(
            self.curr_state, returns_losses, self.invest_judge_memory
        )
        self.reflector.reflect_portfolio_manager(
            self.curr_state, returns_losses, self.portfolio_manager_memory
        )

    def process_signal(self, full_signal):
        """Process a signal to extract the core decision."""
        return self.signal_processor.process_signal(full_signal)
