from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
import json
import re
from datetime import datetime, timedelta

# 使用绝对导入，确保与项目结构匹配
from valueagents.agents.src.graph.state import AgentState, show_agent_reasoning
from valueagents.agents.src.utils.api_key import get_api_key_from_state
from valueagents.agents.src.utils.llm import call_llm
from valueagents.agents.src.utils.progress import progress
from typing_extensions import Literal

from valueagents.agents.utils.agent_utils import get_news


class Sentiment(BaseModel):
    """Represents the sentiment of a news article."""
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: int = Field(description="Confidence 0-100")


def parse_news_text(news_str: str) -> list[dict]:
    """
    解析 get_news 返回的 Markdown 格式字符串，提取每条新闻的标题和摘要。
    """
    articles = []
    parts = news_str.split("### ")
    for part in parts[1:]:
        lines = part.strip().split("\n")
        if not lines:
            continue
        title = lines[0].strip()
        summary = "\n".join(lines[1:]) if len(lines) > 1 else ""
        if "Link:" in summary:
            summary = summary.split("Link:")[0].strip()
        articles.append({"title": title, "summary": summary})
    return articles


def news_sentiment_agent(state: AgentState, agent_id: str = "news_sentiment_agent"):
    data = state.get("data", {})
    end_date = data.get("end_date")
    tickers = data.get("tickers")
    
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    start_dt = end_dt - timedelta(days=7)
    start_date = start_dt.strftime("%Y-%m-%d")
    
    sentiment_analysis = {}

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Fetching company news via ValueAgents")
        news_str = get_news.invoke({
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date
        })

        print(f"\n[DEBUG] Raw news_str for {ticker}:\n{news_str[:500]}\n")
        print(f"[DEBUG] Start date: {start_date}, end_date: {end_date}")
        
        articles = parse_news_text(news_str) if news_str and "No news found" not in news_str else []
        
        news_signals = []
        sentiment_confidences = {}
        sentiments_classified_by_llm = 0
        
        if articles:
            recent_articles = articles[:10]
            num_articles_to_analyze = min(5, len(recent_articles))
            for idx, article in enumerate(recent_articles[:num_articles_to_analyze]):
                progress.update_status(agent_id, ticker, f"Analyzing sentiment for article {idx+1}/{num_articles_to_analyze}")
                prompt = (
                    f"Please analyze the sentiment of the following news headline "
                    f"for the stock {ticker}. "
                    f"Determine if sentiment is 'positive', 'negative', or 'neutral' for the stock {ticker} only. "
                    f"Also provide a confidence score from 0 to 100. "
                    f"Respond in JSON format.\n\n"
                    f"Headline: {article['title']}"
                )
                response = call_llm(prompt, Sentiment, agent_name=agent_id, state=state)
                if response:
                    sentiment = response.sentiment.lower()
                    confidence = response.confidence
                else:
                    sentiment = "neutral"
                    confidence = 0
                if sentiment == "positive":
                    news_signals.append("bullish")
                elif sentiment == "negative":
                    news_signals.append("bearish")
                else:
                    news_signals.append("neutral")
                sentiment_confidences[idx] = confidence
                sentiments_classified_by_llm += 1

        if not news_signals:
            overall_signal = "neutral"
            confidence = 0.0
            total_signals = 0
            bullish_signals = bearish_signals = neutral_signals = 0
        else:
            bullish_signals = news_signals.count("bullish")
            bearish_signals = news_signals.count("bearish")
            neutral_signals = news_signals.count("neutral")
            total_signals = len(news_signals)
            
            if bullish_signals > bearish_signals:
                overall_signal = "bullish"
            elif bearish_signals > bullish_signals:
                overall_signal = "bearish"
            else:
                overall_signal = "neutral"
            
            confidence = _calculate_confidence_score(
                sentiment_confidences=sentiment_confidences,
                total_signals=total_signals,
                overall_signal=overall_signal,
                bullish_signals=bullish_signals,
                bearish_signals=bearish_signals,
            )

        reasoning = {
            "news_sentiment": {
                "signal": overall_signal,
                "confidence": confidence,
                "metrics": {
                    "total_articles": total_signals,
                    "bullish_articles": bullish_signals,
                    "bearish_articles": bearish_signals,
                    "neutral_articles": neutral_signals,
                    "articles_classified_by_llm": sentiments_classified_by_llm,
                },
            }
        }

        sentiment_analysis[ticker] = {
            "signal": overall_signal,
            "confidence": confidence,
            "reasoning": reasoning,
        }

        progress.update_status(agent_id, ticker, "Done", analysis=json.dumps(reasoning, indent=4))

    message = HumanMessage(content=json.dumps(sentiment_analysis), name=agent_id)

    if state.get("metadata", {}).get("show_reasoning"):
        show_agent_reasoning(sentiment_analysis, "News Sentiment Analysis Agent")

    if "analyst_signals" not in state["data"]:
        state["data"]["analyst_signals"] = {}
    state["data"]["analyst_signals"][agent_id] = sentiment_analysis

    progress.update_status(agent_id, None, "Done")
    return {"messages": [message], "data": state["data"]}


def _calculate_confidence_score(
    sentiment_confidences: dict,
    total_signals: int,
    overall_signal: str,
    bullish_signals: int,
    bearish_signals: int,
) -> float:
    if total_signals == 0:
        return 0.0
    
    if sentiment_confidences:
        avg_conf = sum(sentiment_confidences.values()) / len(sentiment_confidences)
        max_count = max(bullish_signals, bearish_signals)
        prop = max_count / total_signals if total_signals > 0 else 0
        return round(0.7 * avg_conf + 0.3 * prop * 100, 2)
    else:
        max_count = max(bullish_signals, bearish_signals)
        return round((max_count / total_signals) * 100, 2)