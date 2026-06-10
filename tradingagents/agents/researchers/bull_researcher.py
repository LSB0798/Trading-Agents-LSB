

def create_bull_researcher(llm, memory):
    def bull_node(state) -> dict:
        """
        从全局共享的 AgentState 字典中取出 investment_debate_state 字段。该字段是一个 InvestDebateState 类型的字典，其中包含了投资辩论相关的所有状态，例如：
            - history：完整对话历史（多头、空头双方的所有发言）。
            - bull_history：多头研究员所有历史发言。
            - bear_history：空头研究员所有历史发言。
            - current_response：对方（空头）最新一次的论点。
            - count：当前已进行的辩论轮次。 """
        investment_debate_state = state["investment_debate_state"]
        """
        从 investment_debate_state 中获取 history 键的值，即完整辩论历史（包含双方所有发言）。
        如果该键不存在，则返回空字符串。
        这个完整历史会被后续的提示词使用，让多头研究员看到整个辩论的来龙去脉，以便衔接上下文。"""
        history = investment_debate_state.get("history", "")
        """
        获取 bull_history 键的值，即多头研究员自己之前的所有历史发言。如果不存在则为空字符串。
        这个历史记录也会被加入提示词（虽然在该节点中未直接用于提示词，但随后会用于更新状态，或有时用于记忆或反思）。
        在此节点返回的新状态中，会把更新后的 bull_history 拼接到原来的历史后面。 """
        bull_history = investment_debate_state.get("bull_history", "")
        """
        获取的是 上一次辩论中对方（即 Bear Researcher，空头研究员）的发言内容。
        这是因为在交替辩论的流程中：
            当执行 bull_node 时，上一轮发言的是 bear_node（空头研究员）。
            bear_node 在执行完成后，会将它的论点写入 investment_debate_state["current_response"]。
            因此，bull_node 读取 current_response 就能得到空头刚刚提出的论据，从而可以针对性地进行反驳或回应。
        类似地，在 bear_node 中，current_response 保存的是多头研究员上一次的发言。"""
        current_response = investment_debate_state.get("current_response", "")

        """
        读取当前状态：
            从 state 中获取四位分析师提供的报告（市场、情绪、新闻、基本面）。
            获取辩论历史（history）、多头历史（bull_history）以及对方（熊方）的最新论点（current_response）。"""
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        """
        检索历史记忆：
            将当前所有报告拼接成 curr_situation，然后调用 memory.get_memories() 查找与该情景相似的过往案例及其教训/建议（最多 2 条）。"""
        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        """
        构建提示词：
            提示词要求 LLM 扮演看涨分析师，依据已有的研究报告、辩论历史、对方论点、过往教训，构建一个有说服力的看涨论点，并主动反驳熊方的观点。"""
        prompt = f"""You are a Bull Analyst advocating for investing in the stock. Your task is to build a strong, evidence-based case emphasizing growth potential, competitive advantages, and positive market indicators. Leverage the provided research and data to address concerns and counter bearish arguments effectively.

Key points to focus on:
- Growth Potential: Highlight the company's market opportunities, revenue projections, and scalability.
- Competitive Advantages: Emphasize factors like unique products, strong branding, or dominant market positioning.
- Positive Indicators: Use financial health, industry trends, and recent positive news as evidence.
- Bear Counterpoints: Critically analyze the bear argument with specific data and sound reasoning, addressing concerns thoroughly and showing why the bull perspective holds stronger merit.
- Engagement: Present your argument in a conversational style, engaging directly with the bear analyst's points and debating effectively rather than just listing data.

Resources available:
Market research report: {market_research_report}
Social media sentiment report: {sentiment_report}
Latest world affairs news: {news_report}
Company fundamentals report: {fundamentals_report}
Conversation history of the debate: {history}
Last bear argument: {current_response}
Reflections from similar situations and lessons learned: {past_memory_str}
Use this information to deliver a compelling bull argument, refute the bear's concerns, and engage in a dynamic debate that demonstrates the strengths of the bull position. You must also address reflections and learn from lessons and mistakes you made in the past.
"""

        """调用 LLM 生成论点：调用 llm.invoke(prompt)，得到回应（response.content）。"""
        response = llm.invoke(prompt)

        """更新辩论状态：将新生成的论点追加到 history、bull_history，更新 current_response 为本次论点的内容，并将辩论轮次计数器 count 加 1。"""
        argument = f"Bull Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bull_history": bull_history + "\n" + argument,
            "bear_history": investment_debate_state.get("bear_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bull_node
