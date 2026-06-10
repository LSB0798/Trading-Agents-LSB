from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_indicators,
    get_language_instruction,
    get_stock_data,
    retrieve_market_wisdom,
)
from tradingagents.dataflows.config import get_config


def create_market_analyst(llm):
    """create_market_analyst 是一个高阶函数，它接收一个 LLM 对象作为参数，然后返回内部定义的 market_analyst_node 函数。
    因此 analyst_nodes["market"]=create_market_analyst(self.quick_thinking_llm) 得到的 market_analyst_node 是一个节点函数，不是普通变量或类实例。"""
    def market_analyst_node(state):
        current_date = state["trade_date"] # current_date : 2025-01-01
        """ state["company_of_interest"] : 0700.HK
        instrument_context : The instrument to analyze is `0700.HK`. Use this exact ticker in every tool call, report, and recommendation, preserving any exchange suffix (e.g. `.TO`, `.L`, `.HK`, `.T`). """
        instrument_context = build_instrument_context(state["company_of_interest"])
        """ build_instrument_context 根据股票代码生成一段描述性文本（例如公司简介、行业信息），将被注入到系统提示中，帮助 LLM 理解分析对象。 """

        tools = [
            get_stock_data,
            get_indicators,
            retrieve_market_wisdom,
        ]

        system_message = (
            """You are a trading assistant tasked with analyzing financial markets. Your role is to select the **most relevant indicators** for a given market condition or trading strategy from the following list. The goal is to choose up to **8 indicators** that provide complementary insights without redundancy. Categories and each category's indicators are:

Moving Averages:
- close_50_sma: 50 SMA: A medium-term trend indicator. Usage: Identify trend direction and serve as dynamic support/resistance. Tips: It lags price; combine with faster indicators for timely signals.
- close_200_sma: 200 SMA: A long-term trend benchmark. Usage: Confirm overall market trend and identify golden/death cross setups. Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries.
- close_10_ema: 10 EMA: A responsive short-term average. Usage: Capture quick shifts in momentum and potential entry points. Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals.

MACD Related:
- macd: MACD: Computes momentum via differences of EMAs. Usage: Look for crossovers and divergence as signals of trend changes. Tips: Confirm with other indicators in low-volatility or sideways markets.
- macds: MACD Signal: An EMA smoothing of the MACD line. Usage: Use crossovers with the MACD line to trigger trades. Tips: Should be part of a broader strategy to avoid false positives.
- macdh: MACD Histogram: Shows the gap between the MACD line and its signal. Usage: Visualize momentum strength and spot divergence early. Tips: Can be volatile; complement with additional filters in fast-moving markets.

Momentum Indicators:
- rsi: RSI: Measures momentum to flag overbought/oversold conditions. Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis.

Volatility Indicators:
- boll: Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. Usage: Acts as a dynamic benchmark for price movement. Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals.
- boll_ub: Bollinger Upper Band: Typically 2 standard deviations above the middle line. Usage: Signals potential overbought conditions and breakout zones. Tips: Confirm signals with other tools; prices may ride the band in strong trends.
- boll_lb: Bollinger Lower Band: Typically 2 standard deviations below the middle line. Usage: Indicates potential oversold conditions. Tips: Use additional analysis to avoid false reversal signals.
- atr: ATR: Averages true range to measure volatility. Usage: Set stop-loss levels and adjust position sizes based on current market volatility. Tips: It's a reactive measure, so use it as part of a broader risk management strategy.

Volume-Based Indicators:
- vwma: VWMA: A moving average weighted by volume. Usage: Confirm trends by integrating price action with volume data. Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses.

- Select indicators that provide diverse and complementary information. Avoid redundancy (e.g., do not select both rsi and stochrsi). Also briefly explain why they are suitable for the given market context. When you tool call, please use the exact name of the indicators provided above as they are defined parameters, otherwise your call will fail. Please make sure to call get_stock_data first to retrieve the CSV that is needed to generate indicators. Then use get_indicators with the specific indicator names. Write a very detailed and nuanced report of the trends you observe. Provide specific, actionable insights with supporting evidence to help traders make informed decisions."""
            + """ Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."""
            # + """\n\nAdditionally, you have access to the `retrieve_market_wisdom` tool, which can search a knowledge base of investment principles from Warren Buffett, Charlie Munger, and other legendary investors. Use this tool when you need to support your technical analysis with classic quotes or proven investment philosophies. For example, you might ask about market psychology, trend following, risk management, or value investing principles."""
            + """\n\nIMPORTANT: Before writing your final report, you MUST use the `retrieve_market_wisdom` tool at least once to gather relevant investment wisdom. For example, you can query: "Warren Buffett's view on technical analysis" or "Charlie Munger's principles of market psychology". Then incorporate the retrieved wisdom into your analysis report."""
            + get_language_instruction() # get_language_instruction() :  Write your entire response in Japanese.
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. {instrument_context}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        # tools : [StructuredTool(name='get_stock_data', description='Retrieve stock price data (OHLCV) for a given ticker symbol.\nUses the configured core_stock_apis vendor.\nArgs:\n    symbol (str): Ticker symbol of the company, e.g. AAPL, TSM\n    start_date (str): Start date in yyyy-mm-dd format\n    end_date (str): End date in yyyy-mm-dd format\nReturns:\n str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.', args_schema=<class 'langchain_core.utils.pydantic.get_stock_data'>, func=<function get_stock_data at 0x7d70686f7600>), StructuredTool(name='get_indicators', description="Retrieve a single technical indicator for a given ticker symbol.\nUses the configured technical_indicators vendor.\nArgs:\n    symbol (str): Ticker symbol of the company, e.g. AAPL, TSM\n indicator (str): A single technical indicator name, e.g. 'rsi', 'macd'. Call this tool once per indicator.\n    curr_date (str): The current trading date you are trading on, YYYY-mm-dd\n    look_back_days (int): How many days to look back, default is 30\nReturns:\n    str: A formatted dataframe containing the technical indicators for the specified ticker symbol and indicator.", args_schema=<class 'langchain_core.utils.pydantic.get_indicators'>, func=<function get_indicators at 0x7d706bc214e0>)]

        """ 为什么需要 partial？
            - 提前绑定不变的值：system_message、current_date、instrument_context 在这个节点内是固定的，不会因调用而改变。将它们 partial 化后，后续 invoke 只需要传入动态部分（如 messages）。
            - 代码简洁：避免在每次 invoke 时重复传递相同的参数。
            - 性能：partial 返回的是新模板，内部已做优化，不会重复解析。"""
        prompt = prompt.partial(system_message=system_message) # 将系统指令长文本 system_message 固定到模板的 {system_message} 位置。此后不需要再传入 system_message。
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools])) # 将工具名称列表拼接成字符串，如 "get_stock_data, get_indicators"，固定到某个 {tool_names} 变量（尽管模板中未使用，可能用于别处或代码遗留）。
        prompt = prompt.partial(current_date=current_date) # current_date : 2025-01-01 将 current_date 固定到 {current_date}。
        prompt = prompt.partial(instrument_context=instrument_context) # 将 instrument_context 固定到 {instrument_context}。instrument_context : The instrument to analyze is `0700.HK`. Use this exact ticker in every tool call, report, and recommendation, preserving any exchange suffix (e.g. `.TO`, `.L`, `.HK`, `.T`).

        """
        - prompt：
            是一个 ChatPromptTemplate 对象。调用 chain.invoke(input) 时，它会根据输入字典和内部模板，生成一个标准的聊天消息列表（List[BaseMessage]）
            prompt: input_variables=['messages'] 
                    input_types={'messages': list[typing.Annotated[typing.Union[typing.Annotated[langchain_core.messages.ai.AIMessage, Tag(tag='ai')],
                                                                                typing.Annotated[langchain_core.messages.human.HumanMessage, Tag(tag='human')],
                                                                                typing.Annotated[langchain_core.messages.chat.ChatMessage, Tag(tag='chat')],
                                                                                typing.Annotated[langchain_core.messages.system.SystemMessage, Tag(tag='system')],
                                                                                typing.Annotated[langchain_core.messages.function.FunctionMessage, Tag(tag='function')],
                                                                                typing.Annotated[langchain_core.messages.tool.ToolMessage, Tag(tag='tool')],
                                                                                typing.Annotated[langchain_core.messages.ai.AIMessageChunk, Tag(tag='AIMessageChunk')],
                                                                                typing.Annotated[langchain_core.messages.human.HumanMessageChunk, Tag(tag='HumanMessageChunk')],
                                                                                typing.Annotated[langchain_core.messages.chat.ChatMessageChunk, Tag(tag='ChatMessageChunk')],
                                                                                typing.Annotated[langchain_core.messages.system.SystemMessageChunk, Tag(tag='SystemMessageChunk')],
                                                                                typing.Annotated[langchain_core.messages.function.FunctionMessageChunk, Tag(tag='FunctionMessageChunk')],
                                                                                typing.Annotated[langchain_core.messages.tool.ToolMessageChunk, Tag(tag='ToolMessageChunk')]
                                                                                ],
                                                                FieldInfo(annotation=NoneType, required=True, discriminator=Discriminator(discriminator=<function _get_type at 0x7e03aea2ede0>, custom_error_type=None, custom_error_message=None, custom_error_context=None))
                                                                ]
                                                ]
                                } 
                    partial_variables ={'system_message': "You are a trading assistant tasked with analyzing financial markets. Your role is to select the **most relevant indicators** for a given market condition or trading strategy from the following list. The goal is to choose up to **8 indicators** that provide complementary insights without redundancy. Categories and each category's indicators are:\n\nMoving Averages:\n- close_50_sma: 50 SMA: A medium-term trend indicator. Usage: Identify trend direction and serve as dynamic support/resistance. Tips: It lags price; combine with faster indicators for timely signals.\n- close_200_sma: 200 SMA: A long-term trend benchmark. Usage: Confirm overall market trend and identify golden/death cross setups. Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries.\n- close_10_ema: 10 EMA: A responsive short-term average. Usage: Capture quick shifts in momentum and potential entry points. Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals.\n\nMACD Related:\n- macd: MACD: Computes momentum via differences of EMAs. Usage: Look for crossovers and divergence as signals of trend changes. Tips: Confirm with other indicators in low-volatility or sideways markets.\n- macds: MACD Signal: An EMA smoothing of the MACD line. Usage: Use crossovers with the MACD line to trigger trades. Tips: Should be part of a broader strategy to avoid false positives.\n- macdh: MACD Histogram: Shows the gap between the MACD line and its signal. Usage: Visualize momentum strength and spot divergence early. Tips: Can be volatile; complement with additional filters in fast-moving markets.\n\nMomentum Indicators:\n- rsi: RSI: Measures momentum to flag overbought/oversold conditions. Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis.\n\nVolatility Indicators:\n- boll: Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. Usage: Acts as a dynamic benchmark for price movement. Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals.\n- boll_ub: Bollinger Upper Band: Typically 2 standard deviations above the middle line. Usage: Signals potential overbought conditions and breakout zones. Tips: Confirm signals with other tools; prices may ride the band in strong trends.\n- boll_lb: Bollinger Lower Band: Typically 2 standard deviations below the middle line. Usage: Indicates potential oversold conditions. Tips: Use additional analysis to avoid false reversal signals.\n- atr: ATR: Averages true range to measure volatility. Usage: Set stop-loss levels and adjust position sizes based on current market volatility. Tips: It's a reactive measure, so use it as part of a broader risk management strategy.\n\nVolume-Based Indicators:\n- vwma: VWMA: A moving average weighted by volume. Usage: Confirm trends by integrating price action with volume data. Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses.\n\n- Select indicators that provide diverse and complementary information. Avoid redundancy (e.g., do not select both rsi and stochrsi). Also briefly explain why they are suitable for the given market context. When you tool call, please use the exact name of the indicators provided above as they are defined parameters, otherwise your call will fail. Please make sure to call get_stock_data first to retrieve the CSV that is needed to generate indicators. Then use get_indicators with the specific indicator names. Write a very detailed and nuanced report of the trends you observe. Provide specific, actionable insights with supporting evidence to help traders make informed decisions. Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read.",
                                        'tool_names': 'get_stock_data, get_indicators', 
                                        'current_date': '2025-01-01', 
                                        'instrument_context': 'The instrument to analyze is `0700.HK`. Use this exact ticker in every tool call, report, and recommendation, preserving any exchange suffix (e.g. `.TO`, `.L`, `.HK`, `.T`).'}
                    messages=[SystemMessagePromptTemplate(prompt=PromptTemplate(input_variables=['current_date', 'instrument_context', 'system_message', 'tool_names'], 
                                                                                input_types={}, partial_variables={}, template="You are a helpful AI assistant, collaborating with other assistants. Use the provided tools to progress towards answering the question. If you are unable to fully answer, that's OK; another assistant with different tools will help where you left off. Execute what you can to make progress. If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable, prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop. You have access to the following tools: {tool_names}.\n{system_message}For your reference, the current date is {current_date}. {instrument_context}"), 
                                                        additional_kwargs={}), 
                            MessagesPlaceholder(variable_name='messages')] 
                    type of prompt : <class 'langchain_core.prompts.chat.ChatPromptTemplate'> 
        
        - llm.bind_tools(tools)：
            bind_tools 是 LangChain 聊天模型的一个方法，它返回原 LLM 的一个副本，但该副本在调用时会将传入的工具定义附加到 API 请求中（通过 OpenAI 的 tools 参数、Anthropic 的 tools 参数等，具体取决于后端）。
            这样，LLM 在生成回复时，可以决定是否调用这些工具，并在输出中包含 tool_calls 字段。
            注意：bind_tools 只是声明了可用的工具，并不会自动执行工具。执行工具需要另外的 ToolNode 或手动处理。
        
        - | 管道操作符
            在 LCEL 中，| 用于将两个组件组合成一个 RunnableSequence。其效果是：前一个组件的输出作为后一个组件的输入。
            当调用 chain.invoke(input) 时，先执行 prompt.invoke(input)，生成消息列表。
            然后将该消息列表作为输入，调用 llm.bind_tools(tools).invoke(messages)，得到 LLM 的回复（一个 AIMessage，可能包含 tool_calls）。
        
            没有 | 时，你需要手动写：
                messages = prompt.invoke(input)
                response = llm.bind_tools(tools).invoke(messages)
            
            使用 | 后，你可以直接 chain.invoke(input)，代码更简洁，而且可以继续串联其他组件（如 | output_parser）。
        
        - 在 market_analyst_node 中：
            prompt 包含了系统指令、占位符（MessagesPlaceholder 用于注入历史消息）和动态变量（日期、公司上下文）。
            llm.bind_tools(tools) 让 LLM 知道它可以调用 get_stock_data 和 get_indicators 这两个工具。
            最终 chain 是一个可运行对象，接收 state["messages"]（一个消息列表），输出 LLM 的回复（AIMessage）。
            这样就实现了：将对话历史 + 工具能力 + 系统提示组合成一个完整的调用，无需手动拼接消息或处理工具声明。"""
        chain = prompt | llm.bind_tools(tools)
        # ========================================================= #
        test_messages = [
            {"role": "system", "content": "You must call the retrieve_investment_wisdom tool with query='market psychology'."},
            {"role": "user", "content": "Get a quote."}
        ]
        try:
            test_result = llm.bind_tools(tools).invoke(test_messages)
        except Exception as e:
            print(f"[DEBUG] Direct test failed: {e}")
        # ========================================================= #

        """ type of state["messages"] : <class 'list'>
        state["messages"] : [HumanMessage(content='0700.HK', additional_kwargs={}, response_metadata={}, id='f44b5f7b-49af-4288-8e45-91e6d3f69149')]
        
        messages 是通过 MessagesPlaceholder 注入的，且其他变量已被 partial 固定，所以只需要传入 messages 列表。
        LangChain 内部会将传入的消息列表自动映射到名为 "messages" 的占位符。 
        如果不使用 partial，则需要： result = chain.invoke({"messages": state["messages"], "system_message": system_message, "current_date": current_date, "instrument_context": instrument_context, "tool_names": "..."}) """
        
        # === 调试开始 ===
        result = chain.invoke(state["messages"])
        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "market_report": report,
        }

    return market_analyst_node
