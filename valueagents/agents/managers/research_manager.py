# =================================== v0 versions =================================== #
import time
from valueagents.agents.utils.agent_utils import build_instrument_context

def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        instrument_context = build_instrument_context(state["company_of_interest"])
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        investment_debate_state = state["investment_debate_state"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""As the portfolio manager and debate facilitator, your role is to critically evaluate this round of debate and make a definitive decision: align with the bear analyst, the bull analyst, or choose Hold only if it is strongly justified based on the arguments presented.

Summarize the key points from both sides concisely, focusing on the most compelling evidence or reasoning. Your recommendation—Buy, Sell, or Hold—must be clear and actionable. Avoid defaulting to Hold simply because both sides have valid points; commit to a stance grounded in the debate's strongest arguments.

Additionally, develop a detailed investment plan for the trader. This should include:

Your Recommendation: A decisive stance supported by the most convincing arguments.
Rationale: An explanation of why these arguments lead to your conclusion.
Strategic Actions: Concrete steps for implementing the recommendation.
Take into account your past mistakes on similar situations. Use these insights to refine your decision-making and ensure you are learning and improving. Present your analysis conversationally, as if speaking naturally, without special formatting. 

Here are your past reflections on mistakes:
\"{past_memory_str}\"

{instrument_context}

Here is the debate:
Debate History:
{history}"""
        response = llm.invoke(prompt)

        new_investment_debate_state = {
            "judge_decision": response.content,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": response.content,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": response.content,
        }

    return research_manager_node


# =================================== v1 versions =================================== #
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from valueagents.agents.utils.agent_utils import (
    build_instrument_context,
    retrieve_research_manager_wisdom,   # 假设已在 agent_utils 中定义
)
from langchain_core.messages import ToolMessage

def create_research_manager_v1(llm, memory):
    def research_manager_node(state):
        # ========== 保留原有变量提取 ==========
        instrument_context = build_instrument_context(state["company_of_interest"])
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        investment_debate_state = state["investment_debate_state"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"
        # =====================================

        # ========== 定义工具 ==========
        tools = [retrieve_research_manager_wisdom]

        # ========== 构建系统提示（包含原有内容 + 工具使用说明）==========
        system_message = f"""You are a Research Manager, the final decision-maker in the investment research team.
Your task is to synthesize the analysis from all previous agents and the debate between Bull and Bear analysts,
and produce a final **investment plan** (e.g., BUY, HOLD, SELL) with clear rationale.

You have access to the `retrieve_research_manager_wisdom` tool. Use it whenever you need to query investment wisdom
from legendary investors (Buffett, Munger) to support your decision. You are encouraged to use it at least once before finalizing.

**Available Reports:**
- Market Report: {market_research_report}
- Sentiment Report: {sentiment_report}
- News Report: {news_report}
- Fundamentals Report: {fundamentals_report}

**Debate History:**
{history}

**Reflections from past similar situations:**
{past_memory_str}

**Instrument Context:**
{instrument_context}

**Your Decision Process:**
1. If you need a specific principle or quote to justify your decision, call the tool with an appropriate query.
2. After receiving the wisdom, incorporate it into your reasoning.
3. Conclude with a final investment plan (BUY/HOLD/SELL) and a concise justification.

**Rules for generating tool queries:**
- The query must be specific and directly related to the current investment decision.
- It should include the stock ticker (e.g., {state["company_of_interest"]}) if relevant.
- It should reference the key debate issue you are trying to resolve (e.g., "growth vs value", "valuation", "risk").
- Use a question format when appropriate (e.g., "What is Buffett's view on high-PE stocks in a rising rate environment?").
- Avoid vague queries like "investment wisdom" or "general principles".
- **Example of a good query:** "Buffett's principle on selling a stock when its P/E exceeds 30x, applied to {state['company_of_interest']}."
- **Example of a bad query:** "Tell me about investing."

**IMPORTANT**: You are allowed to call the `retrieve_research_manager_wisdom` tool **multiple times** during your decision process. 
After receiving the result of a tool call, you should evaluate whether you still have unanswered questions. 
If you need additional or different information, you may call the tool again with a new query. 
Continue this process until you have enough wisdom to make a final decision, then output your investment plan without calling the tool.

Remember: The tool returns passages from legendary investors. A precise query yields more useful results.
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_message}"),
            MessagesPlaceholder(variable_name="messages"),
        ])

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))

        chain = prompt | llm.bind_tools(tools)

        # 初始化消息（用户指令）
        messages = [("human", "Please produce the final investment plan.")]

        max_iterations = 5
        final_response = None
        for index in range(max_iterations):
            try:
                response = chain.invoke({"messages": messages})
            except Exception as e:
                print(f"chain.invoke failed : {e}")
                time.sleep(30)
            messages.append(response)
            if not response.tool_calls: # 检查 LLM 返回的响应中是否包含工具调用请求。如果为空（即模型选择不调用工具），则设置 final_response = response 并跳出循环；否则进入工具执行分支。
                final_response = response
                break
            # 执行工具调用
            for tool_call in response.tool_calls: # 当模型决定调用工具时，执行具体的 RAG 检索（retrieve_research_manager_wisdom.func(query)），并将结果以 ToolMessage 形式追加到 messages 中，然后继续循环，让模型处理检索结果。
                if tool_call["name"] == "retrieve_research_manager_wisdom":
                    """ 当模型决定调用 retrieve_research_manager_wisdom 工具时，tool_call["args"] 中的 query 字段就是模型自主构造的检索字符串，完全由模型决定其内容。 """
                    query = tool_call["args"]["query"]
                    # 构造上下文（可选）
                    context = {
                        "ticker": state.get("company_of_interest", "Unknown"),
                        "market_summary": (market_research_report if market_research_report else ""),
                        "sentiment_summary": (sentiment_report if sentiment_report else ""),
                        "news_summary": (news_report if news_report else ""),
                        "fundamentals_summary": (fundamentals_report if fundamentals_report else ""),
                        "debate_history_summary": (history if history else ""),
                    }
                    # 传递 context 参数（注意：retrieve_research_manager_wisdom 现在是普通函数，直接调用）
                    result = retrieve_research_manager_wisdom.func(query, context=context, role=['research manager'])
                    # messages.append(("tool", result))
                    tool_msg = ToolMessage(content=result, tool_call_id=tool_call["id"])
                    messages.append(tool_msg)

        if final_response is None:
            final_response = response  # fallback

        # ========== 保留原有返回结构 ==========
        new_investment_debate_state = {
            "judge_decision": final_response.content,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": final_response.content,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": final_response.content,
        }

    return research_manager_node