# config.py
import os

class RAGAgentConfig:
    # RAG API 地址
    # RAG_API_URL = os.getenv("RAG_API_URL", "http://00.00.00.00:0000/search")
    RAG_API_URL = os.getenv("RAG_API_URL", "http://00.00.00.00:9000/search")
    
    # LLM 配置（用于规划、评估、生成）
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://00.00.000.00:00000/v1")   # 地址正确
    LLM_API_KEY = os.getenv("LLM_API_KEY", "EMPTY")
    LLM_MODEL = os.getenv("LLM_MODEL", "xxxxxx")    # ← 修改为正确的模型名

    # LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://xx.xx.xx.xxx:xxxxx/v1")   # 改为vLLM地址
    # LLM_API_KEY = os.getenv("LLM_API_KEY", "dummy")                              # vLLM可接受任意值
    # LLM_MODEL = os.getenv("LLM_MODEL", "/data/models/xxxxx")                # 必须与vLLM注册的模型ID一致
    
    # 迭代参数
    MAX_ITERATIONS = 5
    MAX_SUB_QUERIES = 1  # 每次迭代最多拆分的子查询数
    
    # 评估阈值
    SUFFICIENCY_THRESHOLD = 0.7  # 信息充分性评分阈值
