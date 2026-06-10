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
                print('iteration : {}, sub_q : {}, retrieved : {}'.format(iteration, sub_q, retrieved))
                if retrieved:
                    iteration_texts.append(f"查询 '{sub_q}' 的结果:\n{retrieved}")
                    all_retrieved_texts.append(retrieved)
                previous_queries.append(sub_q)
            
            # 3. 评估：判断当前所有信息是否足够
            if all_retrieved_texts:
                eval_result = self.evaluator.evaluate(query, all_retrieved_texts, context=context)
                print('...eval_result : {}'.format(eval_result))
                if eval_result["sufficient"]:
                    print(' ==================== BREAK 0 ==================== ')
                    break
                else:
                    missing_info = eval_result.get("missing")
                    # 继续下一轮迭代
            else:
                # 没有检索到任何信息，直接结束
                print(' ==================== BREAK 1 ==================== ')
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

        print(f"\n{'='*60}")
        print(f"RAG Agent 开始处理查询: {query}")
        if context:
            print(f"上下文: {context}")
        if role:
            print(f"角色: {role}")
        print(f"最大迭代次数: {max_iterations}")

        while iteration < max_iterations:
            print(f"\n--- 迭代 {iteration + 1} / {max_iterations} ---")
            # 1. 确定本轮子查询
            if pending_suggested_queries:
                # 优先使用 Evaluator 的建议，跳过 Planner
                sub_queries = pending_suggested_queries
                pending_suggested_queries = []   # 清空，避免重复
                print(f"[RAGAgent] Using suggested queries: {sub_queries}")
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
                    print("Planner failed to generate sub-queries. Stopping iteration.")
                    break
                print(f"📌 Planner 生成子查询: {sub_queries}")

            # 2. 检索
            new_texts = []
            for sub_q in sub_queries:
                retrieved = self.retriever.retrieve(sub_q, context, role)
                if retrieved:
                    new_texts.append(retrieved)
                previous_queries.append(sub_q)
            print(f"🔍 检索到 {len(new_texts)} 个新文档片段")

            # 3. 合并候选结果
            all_candidates = all_retrieved_texts + new_texts
            print(f"📚 当前累积候选片段总数: {len(all_candidates)}")

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
            print('aaaaaaaaaaaaaaa query : {}'.format(query))
            print('bbbbbbbbbbbbbbb all_candidates : {}'.format(all_candidates))
            print('ccccccccccccccc context : {}'.format(context))
            print('ddddddddddddddd role : {}'.format(role))
            eval_result = self.evaluator.evaluate(
                user_query=query,
                retrieved_texts=all_candidates,
                context=context,
                role=role
            )
            filtered_texts = eval_result["filtered_texts"]
            all_retrieved_texts = filtered_texts   # 只保留合格的片段
            print(f"🔎 过滤后保留片段数: {len(filtered_texts)}")

            # 5. 输出评估详情
            print('???????????????????????? eval_result : {}'.format(eval_result))
            score = eval_result.get("score", 0.0)
            sufficient = eval_result.get("sufficient", False)
            missing = eval_result.get("missing", "")
            print(f"📊 评估得分: {score:.2f} / 1.0, 充分性: {sufficient}")
            if missing:
                print(f"⚠️ 缺失信息: {missing}")

            # 6. 判断是否充分
            if sufficient:
                print("✅ 信息已充分，停止迭代")
                break

            # 7. 准备下一轮：保存建议查询并更新缺失信息
            suggested = eval_result.get("suggested_next_queries", [])
            if suggested:
                # 去重：过滤掉已经查询过的
                pending_suggested_queries = [q for q in suggested if q not in previous_queries]
                print(f"💡 建议下一轮查询 (已去重): {pending_suggested_queries}")
            else:
                pending_suggested_queries = []
            missing_info = eval_result.get("missing")

            iteration += 1

        # 最终输出
        print(f"\n{'='*60}")
        print(f"迭代结束，共进行 {iteration + 1 if iteration < max_iterations else max_iterations} 轮")
        
        # 最终输出：编号列表形式返回过滤后的原始文本
        if all_retrieved_texts:
            print(f"最终输出 {len(all_retrieved_texts)} 个合格片段")
            numbered_context = "\n".join([f"{i+1}. {text}" for i, text in enumerate(all_retrieved_texts)])
            return numbered_context
        else:
            return "未找到相关信息。"