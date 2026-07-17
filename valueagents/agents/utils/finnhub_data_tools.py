# valueagents/agents/utils/finnhub_data_tools.py
import os
import finnhub
from datetime import datetime, timedelta
from langchain_core.tools import tool
from typing import Annotated

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "**********************")  # 替换为您的 key
_client = None

def get_finnhub_client():
    global _client
    if _client is None:
        _client = finnhub.Client(api_key=FINNHUB_API_KEY)
    return _client

def _format_finnhub_articles(articles: list, ticker: str, start_date: str, end_date: str) -> str:
    """将 Finnhub 返回的新闻列表格式化为 Markdown 字符串"""
    if not articles:
        return f"No news found for {ticker} between {start_date} and {end_date}"
    lines = [f"## Finnhub News for {ticker}, from {start_date} to {end_date}:\n"]
    for art in articles[:10]:  # 限制条数
        headline = art.get('headline', 'No headline')
        source = art.get('source', 'Unknown')
        summary = art.get('summary', '')
        url = art.get('url', '')
        datetime_ts = art.get('datetime')
        if datetime_ts:
            dt = datetime.fromtimestamp(datetime_ts).strftime('%Y-%m-%d %H:%M')
        else:
            dt = 'Unknown'
        lines.append(f"### {headline} (source: {source}, time: {dt})")
        if summary:
            lines.append(f"Summary: {summary[:300]}...")
        if url:
            lines.append(f"Link: {url}")
        lines.append("")
    return "\n".join(lines)

@tool
def get_finnhub_news(
    ticker: Annotated[str, "Ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve company news for a specific stock using Finnhub API.
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
    Returns:
        Formatted string containing news articles.
    """
    client = get_finnhub_client()
    try:
        # 确保日期格式正确
        articles = client.company_news(ticker, _from=start_date, to=end_date)

        # print("="*30 + "FINNHUB NEWS" + "="*30 + "\n")
        # print(f"📰 [Finnhub] Raw news for {ticker} ({start_date} to {end_date}):")
        # print(f"   Total articles fetched: {len(articles)}")
        # if articles:
        #     print("   First 3 article headlines:")
        #     for i, art in enumerate(articles[:3], 1):
        #         print(f"      {i}. {art.get('headline', 'No headline')}")
        # print("="*30 + "FINNHUB NEWS" + "="*30 + "\n")

        return _format_finnhub_articles(articles, ticker, start_date, end_date)
    except Exception as e:
        print(f"❌ [Finnhub] Error fetching news for {ticker}: {e}")
        return f"Error fetching Finnhub news for {ticker}: {str(e)}"

@tool
def get_finnhub_global_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles to return"] = 10,
) -> str:
    """
    Retrieve global/macro news using Finnhub by querying market ETFs like SPY.
    """
    start_date = (datetime.strptime(curr_date, "%Y-%m-%d") - timedelta(days=look_back_days)).strftime("%Y-%m-%d")
    # 用 SPY 作为市场代表，获取市场新闻
    ticker = "SPY"
    client = get_finnhub_client()
    try:
        articles = client.company_news(ticker, _from=start_date, to=curr_date)
        # 限制条数
        articles = articles[:limit]

        # print("="*30 + "FINNHUB NEWS" + "="*30 + "\n")
        # print(f"🌍 [Finnhub] Global market news from {start_date} to {curr_date} (via {ticker}):")
        # print(f"   Total articles fetched: {len(articles)}")
        # if articles:
        #     print("   First 3 article headlines:")
        #     for i, art in enumerate(articles[:3], 1):
        #         print(f"      {i}. {art.get('headline', 'No headline')}")
        # print("="*30 + "FINNHUB NEWS" + "="*30 + "\n")

        if not articles:
            return f"No global news found for {curr_date}"
        lines = [f"## Finnhub Global Market News (via SPY), from {start_date} to {curr_date}:\n"]
        for art in articles[:limit]:
            headline = art.get('headline', 'No headline')
            source = art.get('source', 'Unknown')
            summary = art.get('summary', '')
            url = art.get('url', '')
            dt = datetime.fromtimestamp(art.get('datetime', 0)).strftime('%Y-%m-%d %H:%M') if art.get('datetime') else 'Unknown'
            lines.append(f"### {headline} (source: {source}, time: {dt})")
            if summary:
                lines.append(f"Summary: {summary[:300]}...")
            if url:
                lines.append(f"Link: {url}")
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        print(f"❌ [Finnhub] Error fetching global news: {e}")
        return f"Error fetching global news from Finnhub: {str(e)}"