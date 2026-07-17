# test_ta_news_fixed.py
import os
from datetime import datetime, timedelta
from tradingagents.agents.utils.agent_utils import get_news

def test_tradingagents_news(ticker, days_back=7, save_dir="news"):
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    print(f"Testing get_news for {ticker} from {start_date} to {end_date}")
    try:
        news_str = get_news.invoke({
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date
        })
    except Exception as e:
        print(f"Error using invoke: {e}")
        news_str = get_news.func(ticker, start_date, end_date)
    
    if news_str and "No news found" not in news_str:
        print("✅ News retrieved successfully.")
        # 保存新闻到文件
        os.makedirs(save_dir, exist_ok=True)
        filename = f"{ticker}_news_{start_date}_to_{end_date}.txt"
        filepath = os.path.join(save_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(news_str)
        print(f"✅ News saved to {filepath}")
        print("Preview (first 500 chars):")
        print(news_str)
        # print(news_str[:500])
        return True
    else:
        print("❌ No news retrieved.")
        if news_str:
            print(news_str)
        return False

if __name__ == "__main__":
    ticker = "NVDA"
    success = test_tradingagents_news(ticker)
    print("\n" + "="*60)
    print("Testing another ticker: AAPL")
    test_tradingagents_news("AAPL")