

def create_bull_researcher(llm, memory):
    def bull_node(state) -> dict:
        # 获取大师信号并打印
        master_signals = state.get("master_analyst_signals", {})
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
        
        # ========================================== master_analyst_signals 注入到 prompts ========================================== #
        # 格式化大师信号
        master_signals = state.get("master_analyst_signals", {}) # CONTENT-01
        master_signals_text = ""
        if master_signals:
            master_signals_text = "\n\nAdditional insights from investment masters:\n"
            for analyst_name, signals in master_signals.items():
                for ticker, sig in signals.items():
                    master_signals_text += f"- {analyst_name.replace('_', ' ').title()} on {ticker}: {sig.get('signal', 'neutral').upper()} (confidence {sig.get('confidence', 0)}%)\n"
                    if 'reasoning' in sig:
                        master_signals_text += f"  Reasoning: {sig['reasoning']}\n"
        else:
            master_signals_text = "\n\nNo additional master analyst signals available.\n"
        # master_signals_text length : 11338
        # ========================================== master_analyst_signals 注入到 prompts ========================================== #

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
Master analyst signals: {master_signals_text}
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

"""
CONTENT-01
master_signals : {
    'ben_graham_agent': {'AAPL': {'signal': 'bearish', 'confidence': 40.0, 'reasoning': "The valuation analysis reveals ......"}},
    'warren_buffett_agent': {'AAPL': {'signal': 'bearish', 'confidence': 35, 'reasoning': 'High valuation (negative margin of safety), ......'}},
    'peter_lynch_agent': {'AAPL': {'signal': 'bearish', 'confidence': 65.0, 'reasoning': "Apple's PEG ratio of ......"}},
    'phil_fisher_agent': {'AAPL': {'signal': 'neutral', 'confidence': 65.0, 'reasoning': "Apple exhibits a mixed....."}},
    'charlie_munger_agent': {'AAPL': {'signal': 'bearish', 'confidence': 37, 'reasoning': 'Expensive valuation......'}}, 
    'michael_burry_agent': {'AAPL': {'signal': 'bearish', 'confidence': 40.0, 'reasoning': 'FCF yield 3.5% .....'}}, 
    'aswath_damodaran_agent':{'AAPL': {'signal': 'neutral', 'confidence': 25.0, 'reasoning': "Apple's strong ROIC (58.1%) ......"}},
    'cathie_wood_agent': {'AAPL': {'signal': 'neutral', 'confidence': 58.33, 'reasoning': "Apple (AAPL)....."}}, 
    'bill_ackman_agent': {'AAPL': {'signal': 'bearish', 'confidence': 45.0, 'reasoning': "Apple's valuation is severely ......"}}, 
    'rakesh_jhunjhunwala_agent': {'AAPL': {'signal': 'bearish', 'confidence': 92.5, 'reasoning': "The stock is trading ......"}}, 
    'mohnish_pabrai_agent': {'AAPL': {'signal': 'bearish', 'confidence': 72.0, 'reasoning': 'Downside protection fails ......'}}, 
    'nassim_taleb_agent': {'AAPL': {'signal': 'bearish', 'confidence': 45, 'reasoning': 'Fragile balance sheet ......'}}, 
    'stanley_druckenmiller_agent': {'AAPL': {'signal': 'bearish', 'confidence': 65.0, 'reasoning': 'AAPL exhibits ......'}}, 
    'technical_analyst_agent': {}, 
    'fundamentals_analyst_agent': {'AAPL': {'signal': 'neutral', 'confidence': 25.0, 'reasoning': {'profitability_signal': {'signal': 'bullish', 'details': 'ROE: 146.70%, Net Margin: 27.20%, Op Margin: 32.71%'}, 
                                                                                                   'growth_signal': {'signal': 'neutral', 'details': 'Revenue Growth: 3.63%, Earnings Growth: 4.07%'}, 
                                                                                                   'financial_health_signal': {'signal': 'neutral', 'details': 'Current Ratio: 1.07, D/E: 2.48'}, 
                                                                                                   'price_ratios_signal': {'signal': 'bearish', 'details': 'P/E: 29.80, P/B: 34.30, P/S: 8.09'}}}}, 
    'growth_analyst_agent': {'AAPL': {'signal': 'bearish', 'confidence': 74, 'reasoning': {'historical_growth': {'score': 0.05, 'revenue_growth': 0.03632778335097115, 'revenue_trend': -0.00754062757019453, 'eps_growth': 0.04748760249737321, 'eps_trend': 0.0015886660468650837, 'fcf_growth': 0.04743602218546268, 'fcf_trend': -0.04342106077781406},
                                                                                           'growth_valuation': {'score': 0, 'peg_ratio': 6.275206333123455, 'price_to_sales_ratio': 8.091},
                                                                                           'margin_expansion': {'score': 0.2, 'gross_margin': 0.479, 'gross_margin_trend': -0.0040000000000000036, 'operating_margin': 0.3271073581988384, 'operating_margin_trend': -0.0035395269437578313, 'net_margin': 0.272, 'net_margin_trend': -0.008800000000000007}, 
                                                                                           'insider_conviction': {'score': 0.5, 'net_flow_ratio': -0.027826493780360468, 'buys': 155676291.16, 'sells': 164588127.0}, 
                                                                                           'financial_health': {'score': 0.3, 'debt_to_equity': 2.485, 'current_ratio': 1.07}, 
                                                                                           'final_analysis': {'signal': 'bearish', 'confidence': 74, 'weighted_score': 0.13}}}}, 
    'news_sentiment_analyst_agent': {'AAPL': {'signal': 'neutral', 'confidence': 0.0, 'reasoning': {'news_sentiment': {'signal': 'neutral', 'confidence': 0.0, 'metrics': {'total_articles': 0, 'bullish_articles': 0, 'bearish_articles': 0, 'neutral_articles': 0, 'articles_classified_by_llm': 0}}}}}, 
    'sentiment_analyst_agent': {'AAPL': {'signal': 'bullish', 'confidence': 62.39, 'reasoning': {'insider_trading': {'signal': 'bullish', 'confidence': 62, 'metrics': {'total_trades': 117, 'bullish_trades': 73, 'bearish_trades': 44, 'weight': 0.3, 'weighted_bullish': 21.9, 'weighted_bearish': 13.2}}, 
                                                                                                 'news_sentiment': {'signal': 'neutral', 'confidence': 0, 'metrics': {'total_articles': 0, 'bullish_articles': 0, 'bearish_articles': 0, 'neutral_articles': 0, 'weight': 0.7, 'weighted_bullish': 0.0, 'weighted_bearish': 0.0}}, 
                                                                                                 'combined_analysis': {'total_weighted_bullish': 21.9, 'total_weighted_bearish': 13.2, 'signal_determination': 'Bullish based on weighted signal comparison'}}}}, 
    'valuation_analyst_agent': {'AAPL': {'signal': 'bearish', 'confidence': 100, 'reasoning': {'dcf_analysis': {'signal': 'bearish', 'details': 'Value: $1,612,017,603,940.54, Market Cap: $3,652,667,632,000.00, Gap: -55.9%, Weight: 35%\n WACC: 10.5%, Bear: $1,121,735,927,359.66, Bull: $2,145,407,702,188.27, Range: $1,023,671,774,828.61'},
                                                                                               'owner_earnings_analysis': {'signal': 'bearish', 'details': 'Value: $889,727,246,576.85, Market Cap: $3,652,667,632,000.00, Gap: -75.6%, Weight: 35%'}, 
                                                                                               'ev_ebitda_analysis': {'signal': 'neutral', 'details': 'Value: $3,943,659,100,158.99, Market Cap: $3,652,667,632,000.00, Gap: 8.0%, Weight: 20%'},
                                                                                               'residual_income_analysis': {'signal': 'neutral', 'details': 'Value: $3,144,772,339,605.42, Market Cap: $3,652,667,632,000.00, Gap: -13.9%, Weight: 10%'}, 
                                                                                               'dcf_scenario_analysis': {'bear_case': '$1,121,735,927,359.66', 'base_case': '$1,597,648,130,051.58', 'bull_case': '$2,145,407,702,188.27','wacc_used': '10.5%', 'fcf_periods_analyzed': 8}}}}}
"""