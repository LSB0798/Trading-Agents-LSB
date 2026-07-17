# valueagents/agents/utils/gnews_data_tools.py
from langchain_core.tools import tool
from typing import Annotated
import requests
import os
from datetime import datetime, timedelta

# 从环境变量读取 GNews API Key（默认使用你测试过的 key）
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "**********************")
GNEWS_BASE_URL = "https://gnews.io/api/v4/search"

def _format_gnews_articles(articles: list, ticker: str, start_date: str, end_date: str) -> str:
    """将 GNews 返回的文章列表格式化为 Markdown 字符串"""
    if not articles:
        return f"No news found for {ticker} between {start_date} and {end_date}"
    lines = [f"## {ticker} News, from {start_date} to {end_date}:\n"]
    for art in articles:
        title = art.get('title', 'No title')
        source = art.get('source', {}).get('name', 'Unknown')
        description = art.get('description', '')
        link = art.get('url', '')
        lines.append(f"### {title} (source: {source})")
        if description:
            lines.append(description)
        if link:
            lines.append(f"Link: {link}")
        lines.append("")
    return "\n".join(lines)

@tool
def get_news_gnews(
    ticker: Annotated[str, "Ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve news for a specific stock ticker using GNews API.
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
    Returns:
        Formatted string containing news articles
    """
    params = {
        'q': f'"{ticker}" stock',
        'apikey': GNEWS_API_KEY,
        'from': start_date,
        'to': end_date,
        'lang': 'en',
        'sortby': 'publishedAt',
        'max': 10,  # 免费版最多10条，付费可调高
    }
    try:
        resp = requests.get(GNEWS_BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        articles = data.get('articles', [])

        # # ========== 添加打印 ==========
        # print("="*30 + "GNEWS" + "="*30 +"\n")
        # print(f"📰 [GNews] Raw news for {ticker} ({start_date} to {end_date}):")
        # print(f"   Total articles fetched: {len(articles)}")
        # if articles:
        #     print("   First 3 article titles:")
        #     for i, art in enumerate(articles[:3], 1):
        #         print(f"      {i}. {art.get('title', 'No title')}")
        # print("="*30 + "GNEWS" + "="*30 +"\n")
        # # ==============================

        return _format_gnews_articles(articles, ticker, start_date, end_date)
    except Exception as e:
        return f"Error fetching news for {ticker} via GNews: {str(e)}"

@tool
def get_global_news_gnews(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles to return"] = 10,
) -> str:
    """
    Retrieve global/macro economic news using GNews API.
    Args:
        curr_date: Current date in yyyy-mm-dd format
        look_back_days: Number of days to look back
        limit: Maximum number of articles to return
    Returns:
        Formatted string containing global news articles
    """
    start_date = (datetime.strptime(curr_date, "%Y-%m-%d") - timedelta(days=look_back_days)).strftime("%Y-%m-%d")
    queries = [
        "stock market economy",
        "Federal Reserve interest rates",
        "inflation economic outlook",
        "global markets trading"
    ]
    all_articles = []
    seen_titles = set()
    for query in queries:
        params = {
            'q': query,
            'apikey': GNEWS_API_KEY,
            'from': start_date,
            'to': curr_date,
            'lang': 'en',
            'sortby': 'relevance',
            'max': min(limit, 10),
        }
        try:
            resp = requests.get(GNEWS_BASE_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            articles = data.get('articles', [])
            for art in articles:
                title = art.get('title')
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_articles.append(art)
        except Exception:
            continue
    all_articles = all_articles[:limit]

    # # ========== 添加打印 ==========
    # print("="*30 + "GNEWS" + "="*30 +"\n")
    # print(f"🌍 [GNews] Global news from {start_date} to {curr_date}:")
    # print(f"   Total articles fetched: {len(all_articles)}")
    # if all_articles:
    #     print("   First 3 article titles:")
    #     for i, art in enumerate(all_articles[:3], 1):
    #         print(f"      {i}. {art.get('title', 'No title')}")
    # print("="*30 + "GNEWS" + "="*30 +"\n")
    # # ==============================

    if not all_articles:
        return f"No global news found for {curr_date}"
    lines = [f"## Global Market News, from {start_date} to {curr_date}:\n"]
    for art in all_articles:
        title = art.get('title', 'No title')
        source = art.get('source', {}).get('name', 'Unknown')
        description = art.get('description', '')
        link = art.get('url', '')
        lines.append(f"### {title} (source: {source})")
        if description:
            lines.append(description)
        if link:
            lines.append(f"Link: {link}")
        lines.append("")
    return "\n".join(lines)