# valueagents/agents/utils/alpha_news_data_tools.py
import os
import requests
from datetime import datetime, timedelta
from langchain_core.tools import tool
from typing import Annotated

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "*************************")  # 可替换为您的 key

def _format_alpha_news(articles: list, ticker: str, start_date: str, end_date: str) -> str:
    """将 Alpha Vantage 返回的新闻列表格式化为 Markdown 字符串"""
    if not articles:
        return f"No news found for {ticker} between {start_date} and {end_date}"
    lines = [f"## Alpha Vantage News for {ticker}, from {start_date} to {end_date}:\n"]
    for art in articles[:10]:  # 限制条数
        title = art.get('title', 'No title')
        source = art.get('source', 'Unknown')
        summary = art.get('summary', '')
        link = art.get('url', '')
        sentiment_score = art.get('overall_sentiment_score', 0)
        sentiment_label = art.get('overall_sentiment_label', 'Neutral')
        # 该 ticker 的具体情感
        ticker_sent = None
        for ts in art.get('ticker_sentiment', []):
            if ts.get('ticker') == ticker:
                ticker_sent = ts.get('ticker_sentiment_label', 'Neutral')
                break
        lines.append(f"### {title} (source: {source})")
        lines.append(f"Sentiment: {sentiment_label} (score: {sentiment_score:.2f})")
        if ticker_sent:
            lines.append(f"  → {ticker} specific sentiment: {ticker_sent}")
        if summary:
            lines.append(f"Summary: {summary[:300]}...")
        if link:
            lines.append(f"Link: {link}")
        lines.append("")
    return "\n".join(lines)

@tool
def get_alpha_news(
    ticker: Annotated[str, "Ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve news sentiment for a specific stock ticker using Alpha Vantage API.
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        start_date: Start date in yyyy-mm-dd format (not directly used by API, but for reference)
        end_date: End date in yyyy-mm-dd format (not directly used by API)
    Returns:
        Formatted string containing news articles with sentiment.
    """
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,
        "limit": 10,  # 最多10条
        "apikey": ALPHA_VANTAGE_API_KEY,
        "sort": "LATEST"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if "Error Message" in data:
            return f"Error: {data['Error Message']}"
        feed = data.get("feed", [])

        # # ========== 添加打印 ==========
        # print("="*30 + "ALPHA NEWS" + "="*30 + "\n")
        # print(f"📰 [Alpha News] Raw news for {ticker} ({start_date} to {end_date}):")
        # if "Error Message" in data:
        #     print(f"   ❌ API Error: {data['Error Message']}")
        #     print("="*30 + "ALPHA NEWS" + "="*30 + "\n")
        #     return f"Error: {data['Error Message']}"
        # feed = data.get("feed", [])
        # print(f"   Total articles fetched: {len(feed)}")
        # if feed:
        #     print("   First 3 article titles:")
        #     for i, art in enumerate(feed[:3], 1):
        #         print(f"      {i}. {art.get('title', 'No title')}")
        # print("="*30 + "ALPHA NEWS" + "="*30 + "\n")
        # # ==============================

        return _format_alpha_news(feed, ticker, start_date, end_date)
    except Exception as e:
        print(f"❌ [Alpha News] Error fetching news for {ticker}: {e}")
        return f"Error fetching Alpha Vantage news for {ticker}: {str(e)}"

@tool
def get_alpha_global_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles to return"] = 10,
) -> str:
    """
    Retrieve global/macro news using Alpha Vantage without a specific ticker.
    """
    # 计算起始日期（仅用于显示）
    start_date = (datetime.strptime(curr_date, "%Y-%m-%d") - timedelta(days=look_back_days)).strftime("%Y-%m-%d")
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "limit": limit,
        "apikey": ALPHA_VANTAGE_API_KEY,
        "sort": "LATEST"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # # ========== 添加打印 ==========
        # print("="*30 + "ALPHA NEWS" + "="*30 + "\n")
        # print(f"🌍 [Alpha News] Global news from {start_date} to {curr_date}:")
        # if "Error Message" in data:
        #     print(f"   ❌ API Error: {data['Error Message']}")
        #     print("="*30 + "ALPHA NEWS" + "="*30 + "\n")
        #     return f"Error: {data['Error Message']}"
        # feed = data.get("feed", [])
        # print(f"   Total articles fetched: {len(feed)}")
        # if feed:
        #     print("   First 3 article titles:")
        #     for i, art in enumerate(feed[:3], 1):
        #         print(f"      {i}. {art.get('title', 'No title')}")
        # print("="*30 + "ALPHA NEWS" + "="*30 + "\n")
        # # ==============================

        if "Error Message" in data:
            return f"Error: {data['Error Message']}"
        feed = data.get("feed", [])
        if not feed:
            return f"No global news found for {curr_date}"
        lines = [f"## Alpha Vantage Global Market News, from {start_date} to {curr_date}:\n"]
        for art in feed[:limit]:
            title = art.get('title', 'No title')
            source = art.get('source', 'Unknown')
            summary = art.get('summary', '')
            link = art.get('url', '')
            sentiment = art.get('overall_sentiment_label', 'Neutral')
            lines.append(f"### {title} (source: {source})")
            lines.append(f"Overall Sentiment: {sentiment}")
            if summary:
                lines.append(f"Summary: {summary[:300]}...")
            if link:
                lines.append(f"Link: {link}")
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        print(f"❌ [Alpha News] Error fetching global news: {e}")
        return f"Error fetching global news from Alpha Vantage: {str(e)}"