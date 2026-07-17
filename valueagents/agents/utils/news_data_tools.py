from langchain_core.tools import tool
from typing import Annotated
from valueagents.dataflows.interface import route_to_vendor

@tool
def get_news(
    ticker: Annotated[str, "Ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve news data for a given ticker symbol.
    Uses the configured news_data vendor.
    Args:
        ticker (str): Ticker symbol
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
    Returns:
        str: A formatted string containing news data
    """
    # return route_to_vendor("get_news", ticker, start_date, end_date)

    result = route_to_vendor("get_news", ticker, start_date, end_date)

    # # ========== 添加打印 ==========
    # print("="*30 + "NEWS (Alpha Vantage)" + "="*30)
    # print(f"📰 [News] Raw news for {ticker} ({start_date} to {end_date}):")
    # print(f"   Total characters: {len(result)}")
    # preview = result[:200].replace('\n', ' ')
    # print(f"   Preview: {preview}...")
    # article_count = result.count("### ")
    # if article_count:
    #     print(f"   Total articles: {article_count}")
    # print("="*30 + "NEWS END" + "="*30)
    # # ==============================

    return result

@tool
def get_global_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles to return"] = 5,
) -> str:
    """
    Retrieve global news data.
    Uses the configured news_data vendor.
    Args:
        curr_date (str): Current date in yyyy-mm-dd format
        look_back_days (int): Number of days to look back (default 7)
        limit (int): Maximum number of articles to return (default 5)
    Returns:
        str: A formatted string containing global news data
    """
    # return route_to_vendor("get_global_news", curr_date, look_back_days, limit)
    result = route_to_vendor("get_global_news", curr_date, look_back_days, limit)

    # # ========== 添加打印（修正版） ==========
    # print("="*30 + "GLOBAL NEWS (Alpha Vantage)" + "="*30)
    # print(f"🌍 [Global News] from {curr_date} (look_back {look_back_days}d, limit {limit}):")
    # print(f"   Total characters: {len(result)}")
    # preview = result[:200].replace('\n', ' ')
    # print(f"   Preview: {preview}...")
    # # 统计文章数（如果格式中有 "### "）
    # article_count = result.count("### ")
    # if article_count:
    #     print(f"   Total articles: {article_count}")
    # print("="*30 + "GLOBAL NEWS END" + "="*30)
    # # ==============================

    return result

@tool
def get_insider_transactions(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Retrieve insider transaction information about a company.
    Uses the configured news_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
    Returns:
        str: A report of insider transaction data
    """
    return route_to_vendor("get_insider_transactions", ticker)
