from langchain_core.tools import tool
from typing import Annotated
from valueagents.dataflows.interface import route_to_vendor


@tool
def get_fundamentals(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
) -> str:
    """
    Retrieve comprehensive fundamental data for a given ticker symbol.
    Uses the configured fundamental_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing comprehensive fundamental data
    """
    # return route_to_vendor("get_fundamentals", ticker, curr_date)
    result = route_to_vendor("get_fundamentals", ticker, curr_date)

    # print("="*30 + "FUNDAMENTALS DATA (Alpha Vantage)" + "="*30)
    # print(f"📊 [Fundamentals] Raw data for {ticker} ({curr_date}):")
    # print(f"   Total characters: {len(result)}")
    # preview = result[:200].replace('\n', ' ')
    # print(f"   Preview: {preview}...")
    # print("="*30 + "FUNDAMENTALS DATA END" + "="*30)

    return result


@tool
def get_balance_sheet(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "reporting frequency: annual/quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"] = None,
) -> str:
    """
    Retrieve balance sheet data for a given ticker symbol.
    Uses the configured fundamental_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
        freq (str): Reporting frequency: annual/quarterly (default quarterly)
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing balance sheet data
    """
    # return route_to_vendor("get_balance_sheet", ticker, freq, curr_date)
    result = route_to_vendor("get_balance_sheet", ticker, freq, curr_date)

    # print("="*30 + "BALANCE SHEET DATA (Alpha Vantage)" + "="*30)
    # print(f"📊 [Balance Sheet] Raw data for {ticker} ({curr_date if curr_date else 'latest'}):")
    # print(f"   Frequency: {freq}")
    # print(f"   Total characters: {len(result)}")
    # preview = result[:200].replace('\n', ' ')
    # print(f"   Preview: {preview}...")
    # print("="*30 + "BALANCE SHEET DATA END" + "="*30)

    return result


@tool
def get_cashflow(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "reporting frequency: annual/quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"] = None,
) -> str:
    """
    Retrieve cash flow statement data for a given ticker symbol.
    Uses the configured fundamental_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
        freq (str): Reporting frequency: annual/quarterly (default quarterly)
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing cash flow statement data
    """
    # return route_to_vendor("get_cashflow", ticker, freq, curr_date)
    result = route_to_vendor("get_cashflow", ticker, freq, curr_date)

    # print("="*30 + "CASHFLOW DATA (Alpha Vantage)" + "="*30)
    # print(f"📊 [Cashflow] Raw data for {ticker} ({curr_date if curr_date else 'latest'}):")
    # print(f"   Frequency: {freq}")
    # print(f"   Total characters: {len(result)}")
    # preview = result[:200].replace('\n', ' ')
    # print(f"   Preview: {preview}...")
    # print("="*30 + "CASHFLOW DATA END" + "="*30)

    return result


@tool
def get_income_statement(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "reporting frequency: annual/quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"] = None,
) -> str:
    """
    Retrieve income statement data for a given ticker symbol.
    Uses the configured fundamental_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
        freq (str): Reporting frequency: annual/quarterly (default quarterly)
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing income statement data
    """
    # return route_to_vendor("get_income_statement", ticker, freq, curr_date)
    result = route_to_vendor("get_income_statement", ticker, freq, curr_date)

    # print("="*30 + "INCOME STATEMENT DATA (Alpha Vantage)" + "="*30)
    # print(f"📊 [Income Statement] Raw data for {ticker} ({curr_date if curr_date else 'latest'}):")
    # print(f"   Frequency: {freq}")
    # print(f"   Total characters: {len(result)}")
    # preview = result[:200].replace('\n', ' ')
    # print(f"   Preview: {preview}...")
    # print("="*30 + "INCOME STATEMENT DATA END" + "="*30)

    return result