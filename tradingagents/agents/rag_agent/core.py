# core.py
from typing import Dict, Any, Optional, List

from .config import RAGAgentConfig
from .retriever import RAGRetriever
from .planner import Planner
from .evaluator import Evaluator
from .generator import Generator

class RAGAgent:
    def __init__(self, config: RAGAgentConfig = None):
        self.config = config or RAGAgentConfig()
        self.retriever = RAGRetriever(self.config.RAG_API_URL)
        self.planner = Planner(self.config)
        self.evaluator = Evaluator(self.config)
        self.generator = Generator(self.config)
    
    def run_v0(self, query: str, context: Optional[Dict[str, Any]] = None, 
            role: Optional[str] = None) -> str:
        """
        主入口：执行迭代检索直至信息充分，生成答案。
        """
        all_retrieved_texts = []
        previous_queries = []
        missing_info = None
        
        for iteration in range(self.config.MAX_ITERATIONS):
            # 1. 规划：生成本次迭代需要检索的子查询
            sub_queries = self.planner.generate_sub_queries(
                user_query=query,
                context=context,
                previous_queries=previous_queries,
                missing_info=missing_info,
                role=role
            )
            
            if not sub_queries:
                break
            
            # 2. 检索：对每个子查询进行检索，收集结果
            iteration_texts = []
            for sub_q in sub_queries:
                retrieved = self.retriever.retrieve(sub_q, context, role)
                if retrieved:
                    iteration_texts.append(f"查询 '{sub_q}' 的结果:\n{retrieved}")
                    all_retrieved_texts.append(retrieved)
                previous_queries.append(sub_q)
            
            # 3. 评估：判断当前所有信息是否足够
            if all_retrieved_texts:
                eval_result = self.evaluator.evaluate(query, all_retrieved_texts, context=context)
                if eval_result["sufficient"]:
                    break
                else:
                    missing_info = eval_result.get("missing")
                    # 继续下一轮迭代
            else:
                # 没有检索到任何信息，直接结束
                break
        
        # 4. 生成最终答案
        answer = self.generator.generate(query, all_retrieved_texts, context)
        return answer
    
    def run(self, query: str, context: Optional[Dict[str, Any]] = None,
            role: Optional[str] = None) -> str:
        all_retrieved_texts = []
        previous_queries = []
        missing_info = None
        pending_suggested_queries = []   # 用于存储 Evaluator 返回的下一轮建议查询
        iteration = 0
        max_iterations = self.config.MAX_ITERATIONS

        while iteration < max_iterations:
            # 1. 确定本轮子查询
            if pending_suggested_queries:
                # 优先使用 Evaluator 的建议，跳过 Planner
                sub_queries = pending_suggested_queries
                pending_suggested_queries = []   # 清空，避免重复
            else:
                # 初始轮或无建议时调用 Planner
                sub_queries = self.planner.generate_sub_queries(
                    user_query=query,
                    context=context,
                    previous_queries=previous_queries,
                    missing_info=missing_info,
                    role=role
                )
                if not sub_queries:
                    break

            # 2. 检索
            new_texts = []
            for sub_q in sub_queries:
                retrieved = self.retriever.retrieve(sub_q, context, role)
                if retrieved:
                    new_texts.append(retrieved)
                previous_queries.append(sub_q)

            # 3. 合并候选结果
            all_candidates = all_retrieved_texts + new_texts

            # 新增：基于文本相似度的去重
            def _deduplicate(texts, threshold=0.85):
                """基于简单指纹去重，避免同一文档被多次索引"""
                seen = set()
                unique = []
                for text in texts:
                    # 用前 200 字符的 hash 作为指纹
                    fingerprint = hash(text[:200].strip())
                    if fingerprint not in seen:
                        seen.add(fingerprint)
                        unique.append(text)
                return unique
            
            all_candidates = _deduplicate(all_candidates)

            # 4. 批判与过滤
            eval_result = self.evaluator.evaluate(
                user_query=query,
                retrieved_texts=all_candidates,
                context=context,
                role=role
            )
            filtered_texts = eval_result["filtered_texts"]
            all_retrieved_texts = filtered_texts   # 只保留合格的片段

            # 5. 输出评估详情
            score = eval_result.get("score", 0.0)
            sufficient = eval_result.get("sufficient", False)
            missing = eval_result.get("missing", "")

            # 6. 判断是否充分
            if sufficient:
                break

            # 7. 准备下一轮：保存建议查询并更新缺失信息
            suggested = eval_result.get("suggested_next_queries", [])
            if suggested:
                # 去重：过滤掉已经查询过的
                pending_suggested_queries = [q for q in suggested if q not in previous_queries]
            else:
                pending_suggested_queries = []
            missing_info = eval_result.get("missing")

            iteration += 1

        # 最终输出：编号列表形式返回过滤后的原始文本
        if all_retrieved_texts:
            numbered_context = "\n".join([f"{i+1}. {text}" for i, text in enumerate(all_retrieved_texts)])
            return numbered_context
        else:
            return "未找到相关信息。"