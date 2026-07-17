# valueagents/ValueAgents/valueagents/agents/utils/investment_rag.py
import requests
from langchain_core.tools import tool

@tool
def retrieve_investment_wisdom(query: str) -> str:
    """
    从巴菲特、查理·芒格等投资大师的书籍、演讲中检索相关的投资智慧和原则。
    当你需要引用经典投资理念、格言、案例来支持你的分析或决策时，可以使用此工具。
    输入：查询问题，例如“巴菲特对市场波动的看法”、“芒格关于护城河的论述”
    返回：相关的文本片段。
    """
    print(f"[RAG] LLM generated query: {query}")
    try:
        resp = requests.post(
            "http://10.10.29.53:8000/search",  # 你的 RAG API 地址
            json={"query": query},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        context = data.get("context", "")
        print('>>>>>> context : {}'.format(context))
        if not context:
            return "未找到相关信息。"
        # 限制返回长度，避免超过 token 限制
        return context[:4000] + "..." if len(context) > 4000 else context
    except Exception as e:
        return f"检索失败: {str(e)}"

# 01 市场分析师
@tool
def retrieve_market_wisdom(query: str) -> str:
    """
    从巴菲特、查理·芒格等投资大师的书籍、演讲中检索相关的投资智慧和原则。
    当你需要引用经典投资理念、格言、案例来支持你的分析或决策时，可以使用此工具。
    输入：查询问题，例如“巴菲特对市场波动的看法”、“芒格关于护城河的论述”
    返回：相关的文本片段。
    """
    print(f"[RAG] LLM generated query: {query}")
    try:
        resp = requests.post(
            "http://10.10.29.53:8000/search",  # 你的 RAG API 地址
            json={"query": query},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        context = data.get("context", "")
        print('市场分析师 context : {}'.format(context))
        if not context:
            return "未找到相关信息。"
        # 限制返回长度，避免超过 token 限制
        return context[:4000] + "..." if len(context) > 4000 else context
    except Exception as e:
        return f"检索失败: {str(e)}"


#  02 社交媒体分析师
@tool
def retrieve_sentiment_wisdom(query: str) -> str:
    """
    从巴菲特、查理·芒格等投资大师的书籍、演讲中检索相关的投资智慧和原则。
    当你需要引用经典投资理念、格言、案例来支持你的分析或决策时，可以使用此工具。
    输入：查询问题，例如“巴菲特对市场波动的看法”、“芒格关于护城河的论述”
    返回：相关的文本片段。
    """
    print(f"[RAG] LLM generated query: {query}")
    try:
        resp = requests.post(
            "http://10.10.29.53:8000/search",  # 你的 RAG API 地址
            json={"query": query},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        context = data.get("context", "")
        print('社交媒体分析师 context : {}'.format(context))
        if not context:
            return "未找到相关信息。"
        # 限制返回长度，避免超过 token 限制
        return context[:4000] + "..." if len(context) > 4000 else context
    except Exception as e:
        return f"检索失败: {str(e)}"


# 03 新闻分析师
@tool
def retrieve_news_wisdom(query: str) -> str:
    """
    从巴菲特、查理·芒格等投资大师的书籍、演讲中检索相关的投资智慧和原则。
    当你需要引用经典投资理念、格言、案例来支持你的分析或决策时，可以使用此工具。
    输入：查询问题，例如“巴菲特对市场波动的看法”、“芒格关于护城河的论述”
    返回：相关的文本片段。
    """
    print(f"[RAG] LLM generated query: {query}")
    try:
        resp = requests.post(
            "http://10.10.29.53:8000/search",  # 你的 RAG API 地址
            json={"query": query},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        context = data.get("context", "")
        print('新闻分析师 context : {}'.format(context))
        if not context:
            return "未找到相关信息。"
        # 限制返回长度，避免超过 token 限制
        return context[:4000] + "..." if len(context) > 4000 else context
    except Exception as e:
        return f"检索失败: {str(e)}"

# 04 基本面分析师
@tool
def retrieve_fundamentals_wisdom(query: str) -> str:
    """
    从巴菲特、查理·芒格等投资大师的书籍、演讲中检索相关的投资智慧和原则。
    当你需要引用经典投资理念、格言、案例来支持你的分析或决策时，可以使用此工具。
    输入：查询问题，例如“巴菲特对市场波动的看法”、“芒格关于护城河的论述”
    返回：相关的文本片段。
    """
    print(f"[RAG] LLM generated query: {query}")
    try:
        resp = requests.post(
            "http://10.10.29.53:8000/search",  # 你的 RAG API 地址
            json={"query": query},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        context = data.get("context", "")
        print('基本面分析师 context : {}'.format(context))
        if not context:
            return "未找到相关信息。"
        # 限制返回长度，避免超过 token 限制
        return context[:4000] + "..." if len(context) > 4000 else context
    except Exception as e:
        return f"检索失败: {str(e)}"

# 05 Bull Researcher
@tool
def retrieve_bull_wisdom(query: str) -> str:
    """
    从巴菲特、查理·芒格等投资大师的书籍、演讲中检索相关的投资智慧和原则。
    当你需要引用经典投资理念、格言、案例来支持你的分析或决策时，可以使用此工具。
    输入：查询问题，例如“巴菲特对市场波动的看法”、“芒格关于护城河的论述”
    返回：相关的文本片段。
    """
    print(f"[RAG] LLM generated query: {query}")
    try:
        resp = requests.post(
            "http://10.10.29.53:8000/search",  # 你的 RAG API 地址
            json={"query": query},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        context = data.get("context", "")
        print('Bull Researcher context : {}'.format(context))
        if not context:
            return "未找到相关信息。"
        # 限制返回长度，避免超过 token 限制
        return context[:4000] + "..." if len(context) > 4000 else context
    except Exception as e:
        return f"检索失败: {str(e)}"

# 06 Bear Researcher
@tool
def retrieve_bear_wisdom(query: str) -> str:
    """
    从巴菲特、查理·芒格等投资大师的书籍、演讲中检索相关的投资智慧和原则。
    当你需要引用经典投资理念、格言、案例来支持你的分析或决策时，可以使用此工具。
    输入：查询问题，例如“巴菲特对市场波动的看法”、“芒格关于护城河的论述”
    返回：相关的文本片段。
    """
    print(f"[RAG] LLM generated query: {query}")
    try:
        resp = requests.post(
            "http://10.10.29.53:8000/search",  # 你的 RAG API 地址
            json={"query": query},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        context = data.get("context", "")
        print('Bear Researcher context : {}'.format(context))
        if not context:
            return "未找到相关信息。"
        # 限制返回长度，避免超过 token 限制
        return context[:4000] + "..." if len(context) > 4000 else context
    except Exception as e:
        return f"检索失败: {str(e)}"

# 07 Research Manager
@tool
def retrieve_research_manager_wisdom_v0(query: str, context: dict = None, role: list = None) -> str:
    """
    从巴菲特、查理·芒格等投资大师的书籍、演讲中检索相关的投资智慧和原则。
    当你需要引用经典投资理念、格言、案例来支持你的分析或决策时，可以使用此工具。
    输入：查询问题，例如“巴菲特对市场波动的看法”、“芒格关于护城河的论述”
    返回：相关的文本片段。
    """
    print(f"[RAG] Research Manager generated query: {query}")
    if context is not None:
        print(' ======================= RAG DICT BEGIN ======================= ')
        print(f"[RAG] Received context dict: {context}")
        print(f"[RAG] role: {role}")
        print(' ======================= RAG DICT ENDED ======================= ')
    else:
        print("[RAG] No context provided")
    try:
        resp = requests.post(
            "http://10.10.29.53:9000/search",  # 你的 RAG API 地址
            json={"query": query, "context": context, "role": role},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        context = data.get("context", "")
        print('Research Manager context : {}'.format(context))
        if not context:
            return "未找到相关信息。"
        # 限制返回长度，避免超过 token 限制
        return context[:4000] + "..." if len(context) > 4000 else context
    except Exception as e:
        return f"检索失败: {str(e)}"


from ..rag_agent.core import RAGAgent
from ..rag_agent.config import RAGAgentConfig

_rag_agent_instance = None

def get_rag_agent():
    global _rag_agent_instance
    if _rag_agent_instance is None:
        config = RAGAgentConfig()
        # 注意：RAGAgentConfig 中的 RAG_API_URL 应该指向底层检索服务（9000端口），而非自身
        # 默认值可能已正确，无需修改
        _rag_agent_instance = RAGAgent(config)
    return _rag_agent_instance

@tool
def retrieve_research_manager_wisdom(query: str, context: dict = None, role: list = None) -> str:
    """
    使用增强版 RAG Agent 检索投资智慧。
    """
    print(f"[RAG] Research Manager generated query: {query}")
    if context is not None:
        print(' ======================= RAG DICT BEGIN ======================= ')
        print(f"[RAG] Received context dict: {context}")
        print(f"[RAG] role: {role}")
        print(' ======================= RAG DICT ENDED ======================= ')
    else:
        print("[RAG] No context provided")
    
    try:
        agent = get_rag_agent()
        # 转换 role 为字符串（如果存在）
        role_str = role[0] if isinstance(role, list) and role else "research_manager"
        result = agent.run(query, context=context, role=role_str)
        print(f'Research Manager RAG Agent result length: {len(result)}')
        if not result or result == "未找到相关信息。":
            return "未找到相关信息。"
        # 限制返回长度，避免超过 token 限制
        return result[:4000] + "..." if len(result) > 4000 else result
    except Exception as e:
        print(f"RAG Agent 调用失败: {e}")
        return f"检索失败: {str(e)}"



# 08 Trader
@tool
def retrieve_trader_wisdom(query: str) -> str:
    """
    从巴菲特、查理·芒格等投资大师的书籍、演讲中检索相关的投资智慧和原则。
    当你需要引用经典投资理念、格言、案例来支持你的分析或决策时，可以使用此工具。
    输入：查询问题，例如“巴菲特对市场波动的看法”、“芒格关于护城河的论述”
    返回：相关的文本片段。
    """
    print(f"[RAG] LLM generated query: {query}")
    try:
        resp = requests.post(
            "http://10.10.29.53:8000/search",  # 你的 RAG API 地址
            json={"query": query},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        context = data.get("context", "")
        print('Trader context : {}'.format(context))
        if not context:
            return "未找到相关信息。"
        # 限制返回长度，避免超过 token 限制
        return context[:4000] + "..." if len(context) > 4000 else context
    except Exception as e:
        return f"检索失败: {str(e)}"

# 09 风险分析师
@tool
def retrieve_risk_wisdom(query: str) -> str:
    """
    从巴菲特、查理·芒格等投资大师的书籍、演讲中检索相关的投资智慧和原则。
    当你需要引用经典投资理念、格言、案例来支持你的分析或决策时，可以使用此工具。
    输入：查询问题，例如“巴菲特对市场波动的看法”、“芒格关于护城河的论述”
    返回：相关的文本片段。
    """
    print(f"[RAG] LLM generated query: {query}")
    try:
        resp = requests.post(
            "http://10.10.29.53:8000/search",  # 你的 RAG API 地址
            json={"query": query},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        context = data.get("context", "")
        print('风险分析师 context : {}'.format(context))
        if not context:
            return "未找到相关信息。"
        # 限制返回长度，避免超过 token 限制
        return context[:4000] + "..." if len(context) > 4000 else context
    except Exception as e:
        return f"检索失败: {str(e)}"

# 10 Portfolio Manager
@tool
def retrieve_portfolio_manager_wisdom(query: str) -> str:
    """
    从巴菲特、查理·芒格等投资大师的书籍、演讲中检索相关的投资智慧和原则。
    当你需要引用经典投资理念、格言、案例来支持你的分析或决策时，可以使用此工具。
    输入：查询问题，例如“巴菲特对市场波动的看法”、“芒格关于护城河的论述”
    返回：相关的文本片段。
    """
    print(f"[RAG] LLM generated query: {query}")
    try:
        resp = requests.post(
            "http://10.10.29.53:8000/search",  # 你的 RAG API 地址
            json={"query": query},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        context = data.get("context", "")
        print('Portfolio Manager context : {}'.format(context))
        if not context:
            return "未找到相关信息。"
        # 限制返回长度，避免超过 token 限制
        return context[:4000] + "..." if len(context) > 4000 else context
    except Exception as e:
        return f"检索失败: {str(e)}"



