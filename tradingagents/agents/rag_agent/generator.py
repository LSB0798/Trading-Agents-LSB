# generator.py
from openai import OpenAI
import json

class Generator:
    def __init__(self, config):
        self.client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY
        )
        self.model = config.LLM_MODEL
    
    def generate(self, user_query: str, retrieved_texts: list, context: dict = None) -> str:
        """基于检索结果生成最终答案"""
        combined = "\n\n".join(retrieved_texts) if retrieved_texts else "未找到相关信息。"
        context_str = f"额外上下文: {json.dumps(context, ensure_ascii=False)}" if context else ""
        
        prompt = f"""你是一个知识渊博的智能助手。请基于以下检索到的信息，回答用户的问题。
        用户问题: {user_query}
        {context_str}
        检索到的信息:
        {combined[:4000]}

        请给出准确、清晰、有条理的答案。如果信息不足以回答，请明确说明。
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024
        )
        return response.choices[0].message.content