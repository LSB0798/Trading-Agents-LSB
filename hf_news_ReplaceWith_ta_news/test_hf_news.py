import os
import json
from tradingagents.agents.src.tools.api import get_company_news
from tradingagents.agents.src.analysts.news_sentiment import news_sentiment_agent

# 1. 设置 API Key（请替换为你的真实 Key）
os.environ["FINANCIAL_DATASETS_API_KEY"] = "7822668c-eb7d-43b6-bee4-fb31a46e182a"

# 2. 测试参数
TICKER = "NVDA"
END_DATE = "2026-06-22"
LIMIT = 1000

print("=" * 60)
print("Step 1: Directly fetch company news via get_company_news")
print("=" * 60)

news = get_company_news(
    ticker=TICKER,
    end_date=END_DATE,
    limit=LIMIT,
    api_key=os.environ["FINANCIAL_DATASETS_API_KEY"]
)

print(f"Retrieved {len(news)} news articles.")
if news:
    # 打印前两条新闻的标题和情感
    for i, article in enumerate(news[:2]):
        print(f"\nArticle {i+1}:")
        print(f"  Title: {article.title}")
        print(f"  Sentiment: {article.sentiment}")
        print(f"  Date: {article.date}")
else:
    print("No news returned. Check API key, ticker, date, or network.")

print("\n" + "=" * 60)
print("Step 2: Run the full news_sentiment_agent")
print("=" * 60)

# 构造 Agent 所需的状态
state = {
    "data": {
        "end_date": END_DATE,
        "tickers": [TICKER],
        # 其他可能需要的字段
    },
    "metadata": {
        "show_reasoning": False,
    },
    "messages": [],
    "analyst_signals": {},
}

# 调用 Agent
result = news_sentiment_agent(state, agent_id="test_news_sentiment")

# 提取并打印信号
signals = result["data"].get("analyst_signals", {})
print("\nAgent output signals:")
print(json.dumps(signals, indent=2))

# 如果有消息，也打印出来
if result.get("messages"):
    print("\nMessages:")
    for msg in result["messages"]:
        print(msg.content)