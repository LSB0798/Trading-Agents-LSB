# planner.py
import json
import time
from openai import OpenAI
from typing import Dict, List, Optional, Any

class Planner:
    def __init__(self, config):
        self.client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY
        )
        self.model = config.LLM_MODEL
        self.max_sub_queries = config.MAX_SUB_QUERIES
        self.max_retries = config.MAX_ITERATIONS  # 最多重试2次

    def _extract_facts_from_context(self, context: Dict[str, Any]) -> str:
        """从 context 中提取关键事实，返回紧凑的事实描述字符串"""
        if not context:
            return ""
        
        facts = []
        # 需要提取的关键字段（这些字段可能包含长文本）
        for key, value in context.items():
            if value is None:
                continue
            if isinstance(value, str):
                # 对长文本进行事实提取
                if len(value) > 500:   # 超过500字符认为过长，需要提取
                    prompt = f"""Extract the most important key facts from the following {key} section. 
Output a JSON object with a field "facts" containing a list of strings (each string is one fact). 
Maximum 5 facts, each fact should be a short sentence.

Section content:
{value[:2000]}
"""
                    try:
                        resp = self.client.chat.completions.create(
                            model=self.model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.2,
                            max_tokens=4096,
                            response_format={"type": "json_object"}  # 期望返回 {"facts": [...]}
                        )
                        result = json.loads(resp.choices[0].message.content)
                        if isinstance(result, dict) and "facts" in result:
                            facts.extend(result["facts"])
                        elif isinstance(result, list):
                            facts.extend(result)
                        else:
                            # 降级：简单截断
                            facts.append(f"{key}: {value[:200]}...")
                    except Exception as e:
                        facts.append(f"{key}: {value[:200]}...")
                else:
                    # 短文本直接保留
                    facts.append(f"{key}: {value}")
            elif isinstance(value, (int, float, bool)):
                facts.append(f"{key}: {value}")
            elif isinstance(value, list):
                # 对列表简单处理
                facts.append(f"{key}: {', '.join(str(v) for v in value[:3])}")
            # 其他类型忽略或简单转换
        return "\n".join(facts)
    

    def generate_sub_queries(self, user_query: str, context: Dict = None,
                             previous_queries: List[str] = None,
                             missing_info: str = None,
                             role: str = None) -> List[str]:
        
        # 如果启用直接解析模式
        self.max_lines = 2
        
        # 提取事实
        context_facts = self._extract_facts_from_context(context)
        context_str = f"Key facts from analysis:\n{context_facts}"
        # 按换行分割，过滤空行和标题
        base_facts = [line.strip() for line in context_facts.split('\n') if line.strip()]
        base_facts = base_facts[:self.max_lines]   # 限制数量
        
        if base_facts:

            all_generated_sub_queries = []   # 收集所有 LLM 生成的子查询
    
            for fact in base_facts:

                user_message = f"User question: {user_query}"
                if fact:
                    user_message += f"\n\nFocus on this specific aspect: {fact}"
                if previous_queries:
                    user_message += f"\n\nAlready queried: {previous_queries}"
                if missing_info:
                    user_message += f"\n\nMissing information to focus on: {missing_info}"
                
                role_guidance = {
                    "research_manager": "You are a professional research manager. Generate detailed, technical, and comprehensive sub-queries. Include financial metrics, valuation terms, and risk factors.",
                    "retail_customer": "You are a retail customer. Generate simple, easy-to-understand sub-queries. Avoid jargon; focus on basic concepts and practical implications.",
                    "default": "Generate clear and relevant sub-queries that cover the key aspects of the question."
                }
                guidance = role_guidance.get(role, role_guidance["default"])

                system_prompt = f"""{guidance}
        Your task: Based on the user's question and any missing information, generate up to {self.max_sub_queries} sub-queries for retrieval.
        Output a JSON object with a field "sub_queries" containing an array of strings.
        Example: {{"sub_queries": ["query1", "query2"]}}"""
                
                functions = [{
                    "type": "function",
                    "function": {
                        "name": "generate_sub_queries",
                        "description": "Generate sub-queries for information retrieval",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "sub_queries": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": f"List of up to {self.max_sub_queries} sub-queries",
                                    "minItems": 1,
                                    "maxItems": self.max_sub_queries
                                }
                            },
                            "required": ["sub_queries"]
                        }
                    }
                }]

                for attempt in range(self.max_retries + 1):
                    try:
                        # 重试时逐步提高 temperature，增加随机性
                        temp = 0.2 + attempt * 0.1
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_message}
                            ],
                            tools=functions,
                            tool_choice={"type": "function", "function": {"name": "generate_sub_queries"}},
                            temperature=temp,
                            max_tokens=40960
                        )
                        msg = response.choices[0].message
                        if msg.tool_calls and len(msg.tool_calls) > 0:
                            tool_call = msg.tool_calls[0]
                            args = json.loads(tool_call.function.arguments)
                            sub_queries = args.get("sub_queries", [])
                            if isinstance(sub_queries, list) and sub_queries:
                                all_generated_sub_queries.extend(sub_queries[:self.max_sub_queries])
                                break  # 成功则跳出重试循环
                        time.sleep(30.0)
                    except Exception as e:
                        time.sleep(30.0)
                    if attempt < self.max_retries:
                        time.sleep(1.0)
            # 去重并返回所有收集到的子查询
            seen = set()
            unique_queries = []
            for q in all_generated_sub_queries:
                if q not in seen:
                    seen.add(q)
                    unique_queries.append(q)
            return unique_queries

        # 所有重试均失败
        return []