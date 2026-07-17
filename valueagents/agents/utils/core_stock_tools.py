from langchain_core.tools import tool
from typing import Annotated
from valueagents.dataflows.interface import route_to_vendor

# ======================================================================= #
import datetime
import os

LOG_FILE = "/data/lishuaibing/valueagents/ValueAgents/valueagents.log"

def debug_log(label, data):
    """Write debug info to a persistent log file."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"[{timestamp}] {label}\n")
        f.write(f"{'='*60}\n")
        if isinstance(data, dict):
            for k, v in data.items():
                v_str = str(v)[:500] if v is not None else "None"
                f.write(f"  {k}: {v_str}\n")
        else:
            f.write(f"  {str(data)[:2000]}\n")
        f.write("\n")

# 新增：同时输出到终端和日志的辅助函数
def log_print(label, message="", data=None):
    """同时打印到终端和写入日志文件"""
    # 终端输出（可能被Rich覆盖，但保留）
    print(f"\n[{label}] {message}")
    
    # 写入日志文件
    log_data = {"message": message}
    if data is not None:
        log_data.update(data)
    debug_log(label, log_data)
# ======================================================================= #


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
    # RUN THIS WAY

    # ===== 使用 log_print 替代 print =====
    log_print("TOOL CALL", "get_stock_data invoked", {
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date
    })
    # ======================================

    result = route_to_vendor("get_stock_data", symbol, start_date, end_date)
    # return route_to_vendor("get_stock_data", symbol, start_date, end_date)

    # ===== 记录返回结果 =====
    log_print("TOOL RESULT", f"get_stock_data returned {len(result)} chars", {
        "preview": result[:300] if len(result) > 300 else result
    })
    # ========================

    return result
