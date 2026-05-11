from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_stock_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve stock price data (OHLCV) for a given ticker symbol.
    Uses the configured core_stock_apis vendor.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
    Returns:
        str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
    
        
    在 LangChain 中，使用 @tool 装饰器将普通函数转换为可供 LLM 调用的工具。这个 get_stock_data 工具的作用是：
        输入：股票代码（symbol）、起始日期（start_date）、结束日期（end_date）。
        处理：调用 route_to_vendor("get_stock_data", ...)，该函数会根据 DEFAULT_CONFIG 中配置的 core_stock_apis 供应商（例如 Yahoo Finance、Alpha Vantage 等），路由到对应的数据获取实现。
        输出：返回一个格式化的字符串（通常是 DataFrame 的文本表示），包含指定时间范围内的开盘、最高、最低、收盘、成交量（OHLCV）数据。
    """
    return route_to_vendor("get_stock_data", symbol, start_date, end_date)
