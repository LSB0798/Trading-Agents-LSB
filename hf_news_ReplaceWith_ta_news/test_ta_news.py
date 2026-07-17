# test_ta_news_fixed.py
import os
from datetime import datetime, timedelta
from tradingagents.agents.utils.agent_utils import get_news

def test_tradingagents_news(ticker, days_back=7):
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    print(f"Testing get_news for {ticker} from {start_date} to {end_date}")
    # 调用 StructuredTool 的 invoke 方法，传入参数字典
    try:
        news_str = get_news.invoke({
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date
        })
    except Exception as e:
        print(f"Error using invoke: {e}")
        # 备选：直接调用底层函数
        news_str = get_news.func(ticker, start_date, end_date)
    
    if news_str and "No news found" not in news_str:
        print("✅ News retrieved successfully. Preview:")
        print(news_str)
        # print(news_str[:1000])
        return True
    else:
        print("❌ No news retrieved.")
        print(news_str)
        return False

if __name__ == "__main__":
    ticker = "NVDA"
    success = test_tradingagents_news(ticker)
    print("\n" + "="*60)
    print("Testing another ticker: AAPL")
    test_tradingagents_news("AAPL")