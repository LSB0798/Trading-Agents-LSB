# retriever.py
import requests
from typing import Dict, Any, Optional

class RAGRetriever:
    def __init__(self, api_url: str):
        self.api_url = api_url
    
    def retrieve(self, query: str, context: Optional[Dict[str, Any]] = None, 
                 role: Optional[str] = None) -> str:
        payload = {"query": query}
        if context:
            payload["context"] = context
        if role:
            # API 期望 role 为 List[str]，所以将字符串包装成列表
            if isinstance(role, str):
                payload["role"] = [role]
            else:
                payload["role"] = role
        else:
            # 可选：发送默认角色，避免服务端报错
            payload["role"] = ["unknown"]
        
        try:
            resp = requests.post(self.api_url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            context_str = data.get("context", "")
            print(f"\n[Retriever] Query: {query[:80]}")
            print(f"[Retriever] Retrieved {len(context_str)} chars")
            print(f"[Retriever] Preview:\n{context_str[:600]}\n")
            return context_str
            # return data.get("context", "")
        except Exception as e:
            print(f"Retrieval error: {e}")
            return ""