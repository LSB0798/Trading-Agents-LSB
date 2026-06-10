# TradingAgents/graph/setup.py

from typing import Any, Dict
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from tradingagents.agents import *
from tradingagents.agents.utils.agent_states import AgentState

from .conditional_logic import ConditionalLogic


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
        self, selected_analysts=["market", "social", "news", "fundamentals"]
    ):
        """Set up and compile the agent workflow graph.

        Args:
            selected_analysts (list): List of analyst types to include. Options are:
                - "market": Market analyst
                - "social": Social media analyst
                - "news": News analyst
                - "fundamentals": Fundamentals analyst
        """
        if len(selected_analysts) == 0:
            raise ValueError("Trading Agents Graph Setup Error: no analysts selected!")

        # Create analyst nodes
        analyst_nodes = {}
        delete_nodes = {}
        tool_nodes = {}

        """ self.quick_thinking_llm :   callbacks=[<cli.stats_handler.StatsCallbackHandler object at 0x74aea3eb1400>] 
                                        client=<openai.resources.chat.completions.completions.Completions object at 0x74aea38a8a50> 
                                        async_client=<openai.resources.chat.completions.completions.AsyncCompletions object at 0x74aea38a8e10> 
                                        root_client=<openai.OpenAI object at 0x74aea38a87d0> 
                                        root_async_client=<openai.AsyncOpenAI object at 0x74aea38a8b90> 
                                        model_name='qwen3-moe' 
                                        model_kwargs={} 
                                        openai_api_key=SecretStr('**********') 
                                        openai_api_base='http://10.20.223.89:61253/v1' 
                                        reasoning_effort='high' 
                                        use_responses_api=False """

        """
        - 市场分析师（Market Analyst）节点 的实现，其核心作用是：对指定股票进行技术面分析，生成详细的市场趋势报告。
        - 具体来说，它负责：
            -- 根据当前状态（包含股票代码 company_of_interest 和交易日 trade_date）构建分析上下文。
            -- 让 LLM 自主选择最相关的技术指标（最多 8 个，如 SMA、MACD、RSI、布林带、ATR 等），并通过工具调用获取真实数据：
                --- 首先调用 get_stock_data 获取原始行情（OHLCV）。
                --- 然后调用 get_indicators 分别计算所选指标的值。
            -- 基于获取的数据，LLM 撰写一份详细、可操作的分析报告（包括趋势解读、支撑/阻力、动量判断等），最后附上一个 Markdown 表格总结关键点。
            -- 将生成的报告存入状态（state["market_report"]），供后续的研究团队、交易员等节点使用。 """
        if "market" in selected_analysts: # market_report
            analyst_nodes["market"] = create_market_analyst(
                self.quick_thinking_llm
            )
            """print('analyst_nodes["market"] : {}'.format(analyst_nodes["market"]))
            analyst_nodes["market"] : <function create_market_analyst.<locals>.market_analyst_node at 0x74aea3cc9080>
            analyst_nodes["market"] 是一个 LangGraph 节点可调用对象（函数），它封装了市场分析师的完整行为逻辑。
            analyst_nodes["market"] 不是实例化，而是直接引用了 market_analyst_node 这个函数对象本身"""

            delete_nodes["market"] = create_msg_delete()
            tool_nodes["market"] = self.tool_nodes["market"]

        """
        - 社交媒体分析师（Social Media Analyst）节点，其作用是：分析特定公司在社交媒体上的讨论、公众情绪以及公司近期新闻，从而生成一份情绪与舆情分析报告。
        - 具体分析内容包括：
            -- 社交媒体情绪：通过 get_news 工具搜索公司名称，获取过去一周社交媒体上的帖子、评论、讨论等。
            -- 公司特定新闻：同样使用 get_news 检索公司最近发布的新闻（如产品发布、财报、管理层变动等）。
            -- 公众情感趋势：综合以上信息，判断市场对该公司的整体情绪（积极/消极/中性）及其变化。
            -- 对交易者的影响：给出基于情绪和新闻的具体见解，例如：是否存在利空/利多信号、市场关注焦点、潜在的风险或机会。
        - 最终输出一份详细的报告（存储在 state["sentiment_report"]），并附加一个 Markdown 表格总结关键点。该报告将传递给后续的研究团队，辅助投资决策。
        - 因此，该节点是整个交易分析流程中“情感与舆情分析”环节，与市场分析师（技术分析）、新闻分析师（宏观新闻）、基本面分析师形成互补。 """
        if "social" in selected_analysts: # sentiment_report
            analyst_nodes["social"] = create_social_media_analyst(
                self.quick_thinking_llm
            )
            delete_nodes["social"] = create_msg_delete()
            tool_nodes["social"] = self.tool_nodes["social"]

        """
        - 新闻分析师（News Analyst）节点，其核心任务是：分析过去一周内的全球宏观经济新闻以及与公司相关的特定新闻，生成一份综合性的新闻和趋势报告。
        - 具体分析内容包括：
            -- 公司特定新闻：通过 get_news 工具检索与目标公司直接相关的新闻（如财报、产品发布、管理层变动、法律诉讼等）。
            -- 全球宏观经济新闻：通过 get_global_news 工具获取更广泛的宏观新闻（如利率决策、GDP数据、地缘政治事件、大宗商品价格、贸易政策等）。
            -- 对交易的影响：综合以上信息，评估新闻事件可能对市场情绪、行业趋势以及目标公司股价产生的潜在影响，并提供可操作的见解（例如：当前是风险偏好还是避险情绪？哪些行业可能受益或受损？）。
        - 最终产出一份详细的新闻分析报告（存入 state["news_report"]），并附上一个 Markdown 表格总结关键点。该报告会作为后续研究团队的输入之一，帮助判断市场大环境。
        - 因此，这个节点是整个流程中负责“宏观与公司新闻分析”的环节，与市场分析师（技术）、社交媒体分析师（情绪）、基本面分析师（财务）互为补充。 """
        if "news" in selected_analysts: # news_report
            analyst_nodes["news"] = create_news_analyst(
                self.quick_thinking_llm
            )
            delete_nodes["news"] = create_msg_delete()
            tool_nodes["news"] = self.tool_nodes["news"]

        """
        - 基本面分析师（Fundamentals Analyst）节点，其作用是：分析目标公司的基本面信息，包括财务报表（资产负债表、现金流量表、利润表）以及公司概况、财务历史等，生成一份详细的基本面分析报告。
        - 具体分析内容包括：
            -- 公司的财务健康状况（收入、利润、现金流、负债等）。
            -- 公司的业务概况、行业地位。
            -- 历史财务趋势和关键财务比率。
            -- 基于基本面的投资见解（例如估值水平、盈利能力、成长性等）。
        - 最终报告存入 state["fundamentals_report"]，供后续团队参考。该节点是交易分析流程中“公司内在价值评估”的环节，与技术面、情绪面、新闻面分析互补。"""
        if "fundamentals" in selected_analysts: # fundamentals_report
            analyst_nodes["fundamentals"] = create_fundamentals_analyst(
                self.quick_thinking_llm
            )
            delete_nodes["fundamentals"] = create_msg_delete()
            tool_nodes["fundamentals"] = self.tool_nodes["fundamentals"]

        # Create researcher and manager nodes
        """ bull_researcher_node：多头研究员节点，通过 create_bull_researcher 创建，使用 quick_thinking_llm（快速思考模型）和 bull_memory（多头历史记忆）。该节点负责在投资辩论中生成看涨论点。 """
        bull_researcher_node = create_bull_researcher(
            self.quick_thinking_llm, self.bull_memory
        )
        """bear_researcher_node：空头研究员节点，使用 quick_thinking_llm 和 bear_memory，负责生成看跌论点。"""
        bear_researcher_node = create_bear_researcher(
            self.quick_thinking_llm, self.bear_memory
        )
        """research_manager_node：研究经理（审判员）节点，使用 deep_thinking_llm（深度思考模型）和 invest_judge_memory，负责听取两方辩论后做出最终判断。"""
        research_manager_node = create_research_manager(
            self.deep_thinking_llm, self.invest_judge_memory
        )
        """trader_node：交易员节点，使用 quick_thinking_llm 和 trader_memory，负责基于研究团队的结论生成具体的交易计划。"""
        trader_node = create_trader(self.quick_thinking_llm, self.trader_memory)

        # Create risk analysis nodes
        """aggressive_analyst：激进风险分析师节点，使用 quick_thinking_llm（快速思考模型）。在风险讨论中，该角色倾向于积极承担风险，强调潜在收益。"""
        aggressive_analyst = create_aggressive_debator(self.quick_thinking_llm)
        """neutral_analyst：中性风险分析师节点，同样使用 quick_thinking_llm，持平衡观点，客观评估风险与回报。"""
        neutral_analyst = create_neutral_debator(self.quick_thinking_llm)
        """conservative_analyst：保守风险分析师节点，使用 quick_thinking_llm，倾向于规避风险，强调潜在损失和下行保护。"""
        conservative_analyst = create_conservative_debator(self.quick_thinking_llm)
        """portfolio_manager_node：投资组合经理节点，使用 deep_thinking_llm（深度思考模型）和 portfolio_manager_memory（记忆组件）。这是整个交易流程的最终决策者，它会听取三位风险分析师的辩论，结合之前的分析报告，做出最终的交易决策（买入/持有/卖出）。"""
        portfolio_manager_node = create_portfolio_manager(
            self.deep_thinking_llm, self.portfolio_manager_memory
        )

        # Create workflow
        """
        - 初始化一个 LangGraph 状态图对象，并指定整个图使用 AgentState 作为共享状态的数据结构。
            -- StateGraph 是 LangGraph 中用于构建多节点、有状态工作流的类。
            -- AgentState 是一个 TypedDict（继承自 MessagesState），定义了所有 Agent 节点之间共享的状态字段，例如：
                --- 各类分析报告（market_report, sentiment_report 等）
                --- 辩论状态（investment_debate_state, risk_debate_state）
                --- 消息历史（messages）
                --- 最终交易决策（final_trade_decision）
        - 初始化 workflow 后，后续代码会通过：
            -- workflow.add_node(...) 添加节点（如各个 Analyst、Researcher、Trader 等）
            -- workflow.add_edge(...) / workflow.add_conditional_edges(...) 定义节点间的跳转逻辑
            -- workflow.set_entry_point(...) 设置起始节点
            -- workflow.compile() 将图编译成可执行的 Runnable 对象 
        =========================================================================================================
        workflow = StateGraph(AgentState) 只是创建了一个空的工作流图对象，并指定了所有节点共享的状态结构为 AgentState。
        严格来说，这仅仅是构建工作流的起点，而不是完整的“构建工作流”。
        完整的构建工作流包括后续的多个步骤：
            - 添加节点：workflow.add_node(...) 加入各个智能体（分析师、研究员、交易员、风险分析师、投资组合经理）。
            - 添加边：workflow.add_edge(...) 定义顺序执行路径，以及 add_conditional_edges 定义条件分支（如辩论轮换）。
            - 设置入口点：workflow.set_entry_point(...) 指定起始节点（这里是第一个选中的分析师）。
            - 编译：workflow.compile() 将图转换为可执行的 Runnable 对象。
        因此，workflow = StateGraph(AgentState) 只是初始化了一个图构建器，真正的“构建工作流”是后面所有配置步骤的总和。"""
        workflow = StateGraph(AgentState)

        # Add analyst nodes to the graph
        # 加入 analyst nodes 包括 analyst_nodes, delete_nodes, tool_nodes
        for analyst_type, node in analyst_nodes.items():
            workflow.add_node(f"{analyst_type.capitalize()} Analyst", node)
            workflow.add_node(
                f"Msg Clear {analyst_type.capitalize()}", delete_nodes[analyst_type]
            )
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

        # Define edges
        # Start with the first analyst
        first_analyst = selected_analysts[0]
        workflow.add_edge(START, f"{first_analyst.capitalize()} Analyst")

        # Connect analysts in sequence
        for i, analyst_type in enumerate(selected_analysts):
            current_analyst = f"{analyst_type.capitalize()} Analyst" # {analyst} Analyst：LLM 生成分析报告或请求工具的节点。
            current_tools = f"tools_{analyst_type}" # tools_{analyst}：实际执行工具调用（如获取行情、计算指标）的节点。
            current_clear = f"Msg Clear {analyst_type.capitalize()}" # Msg Clear {analyst}：清理临时状态、保存最终报告，并负责路由到下一个分析师或研究团队。

            # Add conditional edges for current analyst
            """
            1.  每个分析师形成一个小循环（分析师 ↔ 工具节点）
                    - 条件边从 current_analyst 出发，根据 conditional_logic.should_continue_{analyst_type} 的返回值：
                        -- 若 LLM 需要调用工具 → 返回工具节点名（current_tools）
                        -- 若不需要工具 → 返回清理节点名（current_clear）
                    - 直连边从 current_tools → current_analyst：工具执行完后必须回到原分析师，以便 LLM 看到工具结果后继续生成最终报告或再次请求新工具。
                因此，每个分析师内部可以循环多次：analyst → tools → analyst → tools → ... → analyst → (无工具时) → current_clear。

                should_continue_market / should_continue_social 等方法：
                    检查 state["messages"][-1].tool_calls 是否存在。
                    若有 → 返回 "tools_{analyst}"；若无 → 返回 "Msg Clear {analyst}"。
                这样设计保证了：
                    每个分析师可以多次使用工具（如先获取数据，再计算多个指标），直到满意为止。
                    分析师之间是严格顺序执行，上一个完成清理后才会启动下一个。
                    最后一个分析师完成后自动转入研究团队辩论阶段。"""
            workflow.add_conditional_edges(
                current_analyst,
                getattr(self.conditional_logic, f"should_continue_{analyst_type}"),
                [current_tools, current_clear],
            )
            workflow.add_edge(current_tools, current_analyst)

            # Connect to next analyst or to Bull Researcher if this is the last analyst
            """
            2. 清理节点串联各分析师
                若当前分析师不是最后一个（i < len-1），则从 current_clear → 下一个分析师节点（next_analyst）。
                若当前分析师是最后一个，则从 current_clear → Bull Researcher（进入研究团队的辩论阶段）。"""
            if i < len(selected_analysts) - 1:
                next_analyst = f"{selected_analysts[i+1].capitalize()} Analyst"
                workflow.add_edge(current_clear, next_analyst)
            else:
                workflow.add_edge(current_clear, "Bull Researcher")

        # Add remaining edges
        """
        - 参数解释
            -- "Bull Researcher"：源节点，即这条边从这个节点出发。
            -- self.conditional_logic.should_continue_debate：一个可调用函数（在 conditional_logic.py 中定义），接收当前状态 state 作为输入，返回一个字符串（下文路径键）。
            -- 映射字典：键是 should_continue_debate 可能的返回值，值是对应的目标节点名称。
                --- "Bear Researcher" → 跳转到 "Bear Researcher" 节点（继续辩论，由空头发言）。
                --- "Research Manager" → 跳转到 "Research Manager" 节点（辩论结束，由经理做最终判断）。
        
        - 这是一个循环，但并非自循环，而是在“Bull Researcher”和“Bear Researcher”两个节点之间的交替往返。
            -- 具体流程：
                1. Bull Researcher 发言后，根据 should_continue_debate 的条件：
                    如果辩论轮次未达上限 → 进入 Bear Researcher（空头）。
                2. Bear Researcher 发言后，它的条件边（未贴出但代码中同样存在）会判断：
                    如果轮次未达上限 → 返回 Bull Researcher。
                3. 如此往复，直到累计轮次达到 2 * max_debate_rounds，则从任意一方的条件边跳转到 Research Manager 终止循环。
        因此，这个循环实现了多头与空头的多轮辩论，直至满足结束条件才退出。"""
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

"""
一、工作流整体结构（按执行顺序）
    分析师团队（Analysts）：依次执行选中的分析师节点（每个分析师包含三个子节点：分析师主节点、工具节点、消息清理节点），顺序由 selected_analysts 列表决定。

    研究团队（Research Team）：Bull Researcher ↔ Bear Researcher 交替辩论，由条件逻辑控制轮数，最后进入 Research Manager。

    交易员（Trader）：单个节点，接在研究经理之后。

    风险管理团队（Risk Management）：Aggressive → Conservative → Neutral 循环辩论，由条件逻辑控制轮数，最后进入 Portfolio Manager。

    投资组合经理（Portfolio Manager）：最终节点，结束图执行。

二、详细阶段分解
    阶段 1：分析师顺序执行（含工具调用循环）
        起始点：START → 第一个选中的分析师（例如 Market Analyst）。

        对于每个分析师（如 Market Analyst）：
            1. 进入 Market Analyst 节点：生成分析报告，可能会调用工具（例如获取股票数据、技术指标）。
            2. 条件边：调用 conditional_logic.should_continue_market：
                如果该分析师的响应中包含工具调用（tool_calls），则转到 tools_market 节点执行工具。
                否则转到 Msg Clear Market 节点（清理消息，输出最终报告）。
            3. 如果进入 tools_market，执行完后边直接回到 Market Analyst 节点（再次让分析师处理工具结果）。
            4. 当最终进入 Msg Clear Market 后，如果还有下一个分析师，则边连接到下一个分析师（如 Social Analyst）；如果是最后一个分析师，则连接到 Bull Researcher。
        所有分析师按顺序处理完毕，进入研究团队。

    阶段 2：研究团队辩论
        起始节点：Bull Researcher（由最后一个分析师的 Msg Clear 直接边进入）。

        两个节点 Bull Researcher 和 Bear Researcher 通过条件边互相切换：
            Bull Researcher 完成输出后，条件边调用 should_continue_debate：
                根据辩论轮数计数器（investment_debate_state["count"]）判断：
                    若未达到最大轮数（count < 2 * max_debate_rounds），则根据当前响应的发送者决定下一位：
                        如果当前响应以 "Bull" 开头 → 下一个节点 Bear Researcher（让空头发言）。
                        否则（以 "Bear" 开头）→ 下一个节点 Bull Researcher（让多头发言）。
                    若达到最大轮数，则转到 Research Manager。
            Bear Researcher 类似，条件边逻辑相同。

        最终进入 Research Manager（研究经理），他听取辩论后给出最终投资计划（investment_plan）。

    阶段 3：交易员
        固定边：Research Manager → Trader。
        交易员节点生成具体交易方案（trader_investment_plan）。

    阶段 4：风险管理团队循环辩论
        固定边：Trader → Aggressive Analyst。

        三个风险分析师节点：Aggressive Analyst, Conservative Analyst, Neutral Analyst 通过条件边循环：
            Aggressive Analyst 后，条件边 should_continue_risk_analysis：
                根据风险讨论轮数计数器（risk_debate_state["count"]）判断：
                    若未达到最大轮数（count < 3 * max_risk_discuss_rounds），根据 latest_speaker 决定下一个：
                        如果当前发言者是 Aggressive → 下一个 Conservative Analyst
                        如果 Conservative → 下一个 Neutral Analyst
                        如果 Neutral → 下一个 Aggressive Analyst
                    若达到最大轮数，则转到 Portfolio Manager。

            Conservative Analyst 和 Neutral Analyst 同样有对应的条件边。

        最终进入 Portfolio Manager。

    阶段 5：最终决策与结束
        Portfolio Manager 节点根据风险分析师的辩论结果做出最终交易决策（final_trade_decision）。
        固定边：Portfolio Manager → END，图执行结束。

三、关键节点类型说明
    1. 分析师节点：由 create_xxx_analyst 创建，是 LLM 节点，会调用工具。
    2. 工具节点：ToolNode，执行具体的函数调用（如获取股票数据），执行后返回结果。
    3. 消息清理节点：create_msg_delete()，用于清空消息历史并提供最终输出。
    4. 辩论节点：研究员和风险分析师都是 LLM 节点，用于生成辩论内容。
    5. 管理节点：Research Manager 和 Portfolio Manager 也是 LLM 节点，负责汇总辩论并做出决策。

四、总结流程图（文本示意）

                           START
                             ↓
    -------------------- 分析师团队 --------------------
    [第一个分析师, 例如 Market Analyst]
    ├─ (如有工具调用) → tools_market → 回到 Market Analyst
    └─ (无工具调用) → Msg Clear Market
                             ↓
    [第二个分析师, 例如 Social Analyst]（依此类推）
    ...
                             ↓ (最后一个分析师完成后)
    ---------------------------------------------------
    --------------------- 研究团队 ---------------------
                     Bull Researcher
    ↺ (循环) ↔ Bear Researcher  (根据 debate 轮数)
    ↓ (当达到 max_debate_rounds)
    Research Manager 研究经理
    ---------------------------------------------------
    -------------------- 交易员团队 --------------------
                            ↓
                          Trader
                            ↓
    ---------------------------------------------------
    ------------------- 风险管理团队 -------------------
    Aggressive Analyst
    ↺ (循环) → Conservative Analyst → Neutral Analyst → Aggressive Analyst ... (根据 risk 轮数)
    ↓ (当达到 max_risk_discuss_rounds)
    ---------------------------------------------------
    ------------------- 最终决策团队 -------------------
                     Portfolio Manager
                            ↓
                           END
    ---------------------------------------------------
"""

"""
add_edge：固定边（直接边）
    无条件地从源节点跳转到目标节点。例如 workflow.add_edge("tools_market", "Market Analyst") 表示工具节点执行完毕后一定回到市场分析师节点。它是单向、确定的链接。

add_conditional_edges：条件边（分支边）
    根据当前状态（state）通过一个回调函数（如 should_continue_debate）的返回值，动态选择下一个要跳转的目标节点。它可以形成循环（例如从 Bull 到 Bear，再从 Bear 回到 Bull，构成交替辩论循环），也可以是向前推进（例如从 Bull 到 Research Manager 结束辩论）。它本身不是“循环边”，而是一个“条件分支边”，循环是由条件函数的逻辑和多个条件边共同构造出来的。

所以：
    add_edge = 固定路径（直连）。
    add_conditional_edges = 动态选择路径（可分支、可循环、可终止）。"""