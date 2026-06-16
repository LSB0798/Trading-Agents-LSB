# tradingagents/agents/src/analysts/__init__.py

from .aswath_damodaran import aswath_damodaran_agent
from .ben_graham import ben_graham_agent
from .bill_ackman import bill_ackman_agent
from .cathie_wood import cathie_wood_agent
from .charlie_munger import charlie_munger_agent
from .fundamentals import fundamentals_analyst_agent
from .growth_agent import growth_analyst_agent
from .michael_burry import michael_burry_agent
from .mohnish_pabrai import mohnish_pabrai_agent
from .nassim_taleb import nassim_taleb_agent
from .news_sentiment import news_sentiment_agent
from .peter_lynch import peter_lynch_agent
from .phil_fisher import phil_fisher_agent
from .portfolio_manager import portfolio_management_agent   # 注意：portfolio_manager 中函数名是 portfolio_management_agent
from .rakesh_jhunjhunwala import rakesh_jhunjhunwala_agent
from .risk_manager import risk_management_agent
from .sentiment import sentiment_analyst_agent
from .stanley_druckenmiller import stanley_druckenmiller_agent
from .technicals import technical_analyst_agent
from .valuation import valuation_analyst_agent
from .warren_buffett import warren_buffett_agent

__all__ = [
    "aswath_damodaran_agent",
    "ben_graham_agent",
    "bill_ackman_agent",
    "cathie_wood_agent",
    "charlie_munger_agent",
    "fundamentals_analyst_agent",
    "growth_analyst_agent",
    "michael_burry_agent",
    "mohnish_pabrai_agent",
    "nassim_taleb_agent",
    "news_sentiment_agent",
    "peter_lynch_agent",
    "phil_fisher_agent",
    "portfolio_management_agent",
    "rakesh_jhunjhunwala_agent",
    "risk_management_agent",
    "sentiment_analyst_agent",
    "stanley_druckenmiller_agent",
    "technical_analyst_agent",
    "valuation_analyst_agent",
    "warren_buffett_agent",
]

"""
这些 analyst 文件（包括 aswath_damodaran.py、ben_graham.py、bill_ackman.py、cathie_wood.py、charlie_munger.py、
                       fundamentals.py、growth_agent.py、michael_burry.py、mohnish_pabrai.py、nassim_taleb.py、
                       news_sentiment.py、peter_lynch.py、phil_fisher.py、rakesh_jhunjhunwala.py、sentiment.py、
                       stanley_druckenmiller.py、technicals.py、valuation.py、warren_buffett.py）
整体上具有高度相似的结构，可以归纳为一种统一的“分析师代理（Analyst Agent）”设计模式。

共同结构
    每个 analyst 文件都遵循以下大致框架：

    1. 导入与依赖
        从 src.graph.state 导入 AgentState、show_agent_reasoning

        从 src.tools.api 导入数据获取函数（如 get_financial_metrics、search_line_items、get_market_cap、get_prices、get_insider_trades、get_company_news 等）

        从 langchain_core.prompts 导入 ChatPromptTemplate

        从 langchain_core.messages 导入 HumanMessage

        从 pydantic 导入 BaseModel，定义一个输出信号模型（如 BenGrahamSignal、WarrenBuffettSignal 等）

        从 src.utils.progress 导入 progress

        从 src.utils.llm 导入 call_llm

        从 src.utils.api_key 导入 get_api_key_from_state

    2. 主函数 *_agent(state: AgentState, agent_id: str = ...)
        签名：接受 state 和 agent_id（默认与文件名对应），返回字典 {"messages": [HumanMessage], "data": state["data"]}。

        主体逻辑：

        提取 state["data"] 中的 tickers、end_date、start_date（如果需要）

        获取 API key（通过 get_api_key_from_state）

        初始化 analysis_data = {} 和 signal_dict = {}（名称各异，如 graham_analysis、buffett_analysis）

        对每个 ticker 循环：

        调用 progress.update_status(agent_id, ticker, "Fetching ...") 更新进度

        获取财务数据：metrics = get_financial_metrics(...)

        获取行项目：line_items = search_line_items(...)

        获取市场市值：market_cap = get_market_cap(...)

        可选：获取价格、内幕交易、新闻等（取决于分析师风格）

        调用多个子分析函数（如 analyze_growth、analyze_valuation、analyze_moat 等），每个返回 score 和 details

        计算总分、最大分，并根据阈值（或特定规则）确定初步 signal（"bullish"/"bearish"/"neutral"）

        将子分析结果存入 analysis_data[ticker]

        调用 LLM 生成最终输出（通过 generate_xxx_output 函数，内部使用 call_llm 和提示模板）

        将 LLM 返回的 signal、confidence、reasoning 存入 signal_dict[ticker]

        更新进度为 "Done"

        创建 HumanMessage，内容为 json.dumps(signal_dict)

        若 state["metadata"]["show_reasoning"] 为真，则调用 show_agent_reasoning

        将结果存入 state["data"]["analyst_signals"][agent_id] = signal_dict

        更新最终进度 progress.update_status(agent_id, None, "Done")

        返回 {"messages": [message], "data": state["data"]}

    3. 子分析函数（多个，命名模式如 analyze_*）
        每个函数接受 metrics、line_items、prices_df、market_cap 等参数

        内部计算分数（通常为 0‑10 或 0‑X 后缩放）

        返回包含 score、details（字符串）的字典，有时也返回 max_score 和其他字段

    4. LLM 生成函数（generate_*_output）
        接受 ticker、analysis_data、state、agent_id

        构建 ChatPromptTemplate，系统提示模仿该投资大师的风格和原则

        调用 call_llm，传入 pydantic_model（信号类）和 default_factory

        返回信号对象（如 BenGrahamSignal）

        
相似点总结
    维度                共同特征
    入口函数            def xxx_agent(state, agent_id)，返回 {"messages": [...], "data": ...}
    状态更新            使用全局 progress 对象报告进度
    数据获取            使用 src.tools.api 中的函数（财务指标、行项目、市值、价格、内幕、新闻）
    子分析函数          多个，返回 score 和 details，用于量化基本面/估值/质量等
    评分聚合            加权或简单加总各子分析分数，计算 total_score 和 max_score
    初步信号            基于总分比例或特定规则（如 margin_of_safety）确定一个初步信号（但最终信号由 LLM 决定）
    LLM 调用            通过 call_llm 和自定义提示模板，生成最终 signal、confidence、reasoning
    输出格式            向 state["data"]["analyst_signals"] 写入 {ticker: {signal, confidence, reasoning}}，并返回 HumanMessage
    错误处理            大多使用 default_factory 提供默认信号，避免 LLM 解析失败导致工作流中断

数据侧差异：
    仅依赖财务基本面数据的分析师

    分析师                  主要数据源                                                           特点
    Ben Graham              get_financial_metrics, search_line_items                            关注 EPS、账面价值、流动比率、负债、股息等，计算格雷厄姆数、净流动资产价值（NCAV）。
    Aswath Damodaran        get_financial_metrics, search_line_items, get_market_cap            获取 FCFF、EBIT、利息、折旧、营收、债务等，用于 DCF 和资本成本计算。
    Warren Buffett          search_line_items 大量字段（净利、折旧、CAPEX、营运资本、股东权益等）   计算所有者盈余（Owner Earnings），进行三阶段 DCF 和账面价值分析。
    Fundamentals            get_financial_metrics                                               仅使用财务比率（ROE、利润率、增长率、负债率等），不深入行项目。
    Growth Agent            get_financial_metrics, search_line_items                            获取营收、EPS、FCF、毛利率、运营利润率等，计算增长趋势。
    Valuation               get_financial_metrics, search_line_items                            获取 FCFF、EBIT、EBITDA、净利、负债、现金等，用于多种估值模型。
    Mohnish Pabrai          search_line_items                                                   重点获取 FCF、负债、现金、资本支出、营收等，评估下行保护和 FCF 收益率。
    Rakesh Jhunjhunwala     search_line_items                                                   获取净利、EPS、EBIT、营收、资产、负债、FCF、股息、股份回购等。
    这些分析师从不调用价格、内幕交易或新闻数据。

需要价格/技术数据的分析师
    分析师                  额外数据                     用途
    Technical Analyst       get_prices (OHLCV)          计算移动平均、ADX、布林带、RSI、ATR、Hurst 指数等，完全基于价格和成交量。
    Stanley Druckenmiller   get_prices                  计算价格动量（上涨百分比），结合财务增长进行评分。
    Nassim Taleb            get_prices                  分析尾部风险、波动率、偏度、峰度、最大回撤、上涨/下跌不对称性。
    这些分析师不使用内幕交易或新闻。

需要内幕交易数据的分析师
    分析师              数据                     用途
    Charlie Munger      get_insider_trades      评估管理层“skin in the game”，计算买卖比例。
    Michael Burry       get_insider_trades      观察内幕净买入情况，作为催化剂信号。
    Phil Fisher         get_insider_trades      判断管理层信心的辅助信号。
    Sentiment Analyst   get_insider_trades      结合新闻情绪，计算多头/空头加权分数。
    Peter Lynch         get_insider_trades      简单判断买入/卖出比例，影响最终评分。

综合多个数据源的分析师（覆盖最全）
    分析师                  数据组合
    Charlie Munger          财务 + 内幕 + 新闻
    Michael Burry           财务 + 内幕 + 新闻 + 市值
    Stanley Druckenmiller   财务 + 价格 + 内幕 + 新闻
    Nassim Taleb            财务 + 价格 + 内幕 + 新闻（最全面）

Confidence 的来源与含义
    Confidence 由各分析师根据自己的评估逻辑独立计算，常见方法包括：

    1. 基于量化分数的映射（无 LLM）
        例如 Ben Graham、Aswath Damodaran、Charlie Munger 等会先通过财务指标、估值模型、风险指标等计算一个总分数
        （例如 0 – 10 或 0 – 某个最大值），然后将分数映射为 0 – 100 的置信度。
        分数越高 → 置信度越高。

    2. 基于 Margin of Safety（安全边际）
        如 Aswath Damodaran 使用 margin_of_safety（内在价值与市值的偏差）直接转换：
        confidence = min(abs(margin_of_safety) * 150, 95)，安全边际越大，置信度越高。

    3. 基于规则 + 启发式
        例如 Michael Burry 的置信度由几个子分析（价值、资产负债表、内幕交易、反向情绪）的分数加权求和后，
        通过简单规则（如 total_score >= 0.7 * max_score → bullish）给出信号，而置信度可能直接取 total_score / max_score * 100。

    4. 由 LLM 直接生成
        多数分析师在最终步骤中调用 call_llm()，让 LLM 根据提供的量化分析结果
        （如“ROE 18%”、“PEG 0.8”、“自由现金流强劲”等）直接输出一个 confidence 数值。
        LLM 会按照系统提示中的规则（例如“若业务优秀且估值便宜 → 置信度 90%+”，“信号矛盾 → 置信度 50% 左右”）给出置信度。

    📌 Confidence 在整体工作流中的作用
        风险管理者会读取所有分析师的信号和置信度，但当前代码中风险管理者并未直接使用置信度来调整仓位，而是基于市场波动率和相关性计算仓位限制。
        投资组合管理者会汇总所有分析师的信号（忽略置信度），然后生成最终的交易决策（买入/卖出/做空/平仓等）。置信度目前更多用于输出展示和可解释性。
"""