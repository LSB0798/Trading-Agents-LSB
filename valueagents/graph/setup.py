# valueagents/graph/setup.py

from typing import Any, Dict
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from valueagents.agents import *
from valueagents.agents.utils.agent_states import AgentState

from .conditional_logic import ConditionalLogic


def signal_aggregator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    汇聚所有分析师的信号，不做额外处理。
    注意：大师分析师的信号已在各自节点中写入 state["master_analyst_signals"]。
    """
    # 可以在这里添加日志或统计
    # return state
    return {}


class GraphSetup:
    """Handles the setup and configuration of the agent graph."""

    def __init__(
        self,
        quick_thinking_llm: Any,
        deep_thinking_llm: Any,
        tool_nodes: Dict[str, ToolNode],
        bull_memory,
        bear_memory,
        trader_memory,
        invest_judge_memory,
        portfolio_manager_memory,
        conditional_logic: ConditionalLogic,
    ):
        """Initialize with required components."""
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.tool_nodes = tool_nodes
        self.bull_memory = bull_memory
        self.bear_memory = bear_memory
        self.trader_memory = trader_memory
        self.invest_judge_memory = invest_judge_memory
        self.portfolio_manager_memory = portfolio_manager_memory
        self.conditional_logic = conditional_logic

    def setup_graph(
        self, selected_analysts=["market", "social", "news", "fundamentals"], use_master_analysts=False,
    ):
        if len(selected_analysts) == 0:
            raise ValueError("Trading Agents Graph Setup Error: no analysts selected!")

        # Create analyst nodes
        analyst_nodes = {}
        delete_nodes = {}
        tool_nodes = {}

        # ==================== 1. 先创建所有普通分析师（无论是否大师模式） ====================
        if "market" in selected_analysts:
            analyst_nodes["market"] = create_market_analyst(self.quick_thinking_llm)
            delete_nodes["market"] = create_msg_delete()
            tool_nodes["market"] = self.tool_nodes["market"]

        if "social" in selected_analysts:
            analyst_nodes["social"] = create_social_media_analyst(self.quick_thinking_llm)
            delete_nodes["social"] = create_msg_delete()
            tool_nodes["social"] = self.tool_nodes["social"]

        if "news" in selected_analysts:
            analyst_nodes["news"] = create_news_analyst(self.quick_thinking_llm)
            delete_nodes["news"] = create_msg_delete()
            tool_nodes["news"] = self.tool_nodes["news"]

        if "fundamentals" in selected_analysts:
            analyst_nodes["fundamentals"] = create_fundamentals_analyst(self.quick_thinking_llm)
            delete_nodes["fundamentals"] = create_msg_delete()
            tool_nodes["fundamentals"] = self.tool_nodes["fundamentals"]

        if "gnews" in selected_analysts:
            analyst_nodes["gnews"] = create_gnews_analyst(self.quick_thinking_llm)
            delete_nodes["gnews"] = create_msg_delete()
            tool_nodes["gnews"] = self.tool_nodes["gnews"]
        
        if "alpha_news" in selected_analysts:
            analyst_nodes["alpha_news"] = create_alpha_news_analyst(self.quick_thinking_llm)
            delete_nodes["alpha_news"] = create_msg_delete()
            tool_nodes["alpha_news"] = self.tool_nodes["alpha_news"]
        
        if "finnhub_news" in selected_analysts:
            analyst_nodes["finnhub_news"] = create_finnhub_news_analyst(self.quick_thinking_llm)
            delete_nodes["finnhub_news"] = create_msg_delete()
            tool_nodes["finnhub_news"] = self.tool_nodes["finnhub_news"]

        # ==================== 2. 如果启用大师模式，添加大师分析师 ====================
        if use_master_analysts:
            from valueagents.agents.hf_analysts_wrapper import get_master_analyst_node
            STANDARD_ANALYSTS = {"market", "social", "news", "fundamentals", "gnews", "alpha_news", "finnhub_news"}
            
            for analyst_name in selected_analysts:
                if analyst_name not in STANDARD_ANALYSTS:
                    print(f"    Getting node for {analyst_name}")
                    node_func = get_master_analyst_node(analyst_name, self.quick_thinking_llm)
                    analyst_nodes[analyst_name] = node_func
                    delete_nodes[analyst_name] = create_msg_delete()
                    tool_nodes[analyst_name] = None
        # =================================================================================

        # Create researcher and manager nodes
        bull_researcher_node = create_bull_researcher(
            self.quick_thinking_llm, self.bull_memory
        )
        bear_researcher_node = create_bear_researcher(
            self.quick_thinking_llm, self.bear_memory
        )
        research_manager_node = create_research_manager(
            self.deep_thinking_llm, self.invest_judge_memory
        )
        trader_node = create_trader(self.quick_thinking_llm, self.trader_memory)

        # Create risk analysis nodes
        aggressive_analyst = create_aggressive_debator(self.quick_thinking_llm)
        neutral_analyst = create_neutral_debator(self.quick_thinking_llm)
        conservative_analyst = create_conservative_debator(self.quick_thinking_llm)
        portfolio_manager_node = create_portfolio_manager(
            self.deep_thinking_llm, self.portfolio_manager_memory
        )

        # Create workflow
        workflow = StateGraph(AgentState)

        # Add analyst nodes to the graph
        for analyst_type, node in analyst_nodes.items():
            workflow.add_node(f"{analyst_type.capitalize()} Analyst", node)
            workflow.add_node(f"Msg Clear {analyst_type.capitalize()}", delete_nodes[analyst_type])
            if tool_nodes[analyst_type] is not None:
                workflow.add_node(f"tools_{analyst_type}", tool_nodes[analyst_type])

        # Add other nodes
        workflow.add_node("Bull Researcher", bull_researcher_node)
        workflow.add_node("Bear Researcher", bear_researcher_node)
        workflow.add_node("Research Manager", research_manager_node)
        workflow.add_node("Trader", trader_node)
        workflow.add_node("Aggressive Analyst", aggressive_analyst)
        workflow.add_node("Neutral Analyst", neutral_analyst)
        workflow.add_node("Conservative Analyst", conservative_analyst)
        workflow.add_node("Portfolio Manager", portfolio_manager_node)

        # ========== 根据模式定义边 ==========
        if use_master_analysts:
            # 串行执行所有分析师（顺序执行）
            workflow.add_node("SignalAggregator", signal_aggregator_node)

            # 定义标准分析师集合（具有工具）
            STANDARD_ANALYSTS = {"market", "social", "news", "fundamentals", "gnews", "alpha_news", "finnhub_news"}

            # 添加 START 到第一个分析师的边
            if selected_analysts:
                first_analyst = f"{selected_analysts[0].capitalize()} Analyst"
                workflow.add_edge(START, first_analyst)
            else:
                raise ValueError("No analysts selected for master mode")

            # 依次连接分析师（包括工具循环）
            for i, analyst_name in enumerate(selected_analysts):
                current_analyst = f"{analyst_name.capitalize()} Analyst"
                current_clear = f"Msg Clear {analyst_name.capitalize()}"
                current_tools = f"tools_{analyst_name}"

                if analyst_name in STANDARD_ANALYSTS:
                    # 标准分析师：添加工具循环
                    workflow.add_conditional_edges(
                        current_analyst,
                        getattr(self.conditional_logic, f"should_continue_{analyst_name}"),
                        [current_tools, current_clear],
                    )
                    workflow.add_edge(current_tools, current_analyst)
                else:
                    # 大师分析师：直接到清理节点（无工具）
                    workflow.add_edge(current_analyst, current_clear)

                # 连接清理节点到下一个分析师或汇聚节点
                if i < len(selected_analysts) - 1:
                    next_analyst = f"{selected_analysts[i+1].capitalize()} Analyst"
                    workflow.add_edge(current_clear, next_analyst)
                else:
                    workflow.add_edge(current_clear, "SignalAggregator")

            workflow.add_edge("SignalAggregator", "Bull Researcher")
        else:
            # 原有模式：顺序执行，带工具循环
            # Define edges
            # Start with the first analyst
            first_analyst = selected_analysts[0]
            workflow.add_edge(START, f"{first_analyst.capitalize()} Analyst")

            for i, analyst_type in enumerate(selected_analysts):
                current_analyst = f"{analyst_type.capitalize()} Analyst"
                current_tools = f"tools_{analyst_type}"
                current_clear = f"Msg Clear {analyst_type.capitalize()}"
                # Connect analysts in sequence
                # Add conditional edges for current analyst
                workflow.add_conditional_edges(
                    current_analyst,
                    getattr(self.conditional_logic, f"should_continue_{analyst_type}"),
                    [current_tools, current_clear],
                )
                workflow.add_edge(current_tools, current_analyst)
                # Connect to next analyst or to Bull Researcher if this is the last analyst
                if i < len(selected_analysts) - 1:
                    next_analyst = f"{selected_analysts[i+1].capitalize()} Analyst"
                    workflow.add_edge(current_clear, next_analyst)
                else:
                    workflow.add_edge(current_clear, "Bull Researcher")

        # Add remaining edges
        workflow.add_conditional_edges(
            "Bull Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bear Researcher": "Bear Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_conditional_edges(
            "Bear Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bull Researcher": "Bull Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_edge("Research Manager", "Trader")
        workflow.add_edge("Trader", "Aggressive Analyst")
        workflow.add_conditional_edges(
            "Aggressive Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Conservative Analyst": "Conservative Analyst",
                "Portfolio Manager": "Portfolio Manager",
            },
        )
        workflow.add_conditional_edges(
            "Conservative Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Neutral Analyst": "Neutral Analyst",
                "Portfolio Manager": "Portfolio Manager",
            },
        )
        workflow.add_conditional_edges(
            "Neutral Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Aggressive Analyst": "Aggressive Analyst",
                "Portfolio Manager": "Portfolio Manager",
            },
        )

        workflow.add_edge("Portfolio Manager", END)

        # Compile and return
        return workflow.compile()
