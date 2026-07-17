# evaluator.py
import json
from openai import OpenAI
from typing import Dict, List, Optional
from typing import Dict, Any, List, Optional
import time, random

class Evaluator_v0:
    def __init__(self, config):
        self.client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY
        )
        self.model = config.LLM_MODEL
        self.threshold = config.SUFFICIENCY_THRESHOLD
    
    def evaluate_v0(self, user_query: str, retrieved_texts: list) -> dict:
        
        combined = "\n\n---\n\n".join(retrieved_texts) if retrieved_texts else "无检索结果"
        
        prompt = f"""你是一个信息充分性评估专家。请评估以下检索到的信息是否足以回答用户的问题。
        用户问题: {user_query}
        检索到的信息:
        {combined[:3000]}  # 限制长度

        请输出一个 JSON 对象，包含:
        - "sufficient": true/false
        - "score": 0.0-1.0 的分数，表示信息充分程度
        - "missing": 如果不充分，简要描述缺失什么信息；如果充分，为 null
        
        只输出 JSON，不要有其他解释。
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2048 # 300
        )
        content = response.choices[0].message.content
        try:
            result = json.loads(content)
            score = result.get("score", 0.0)
            sufficient = score >= self.threshold
            return {
                "sufficient": sufficient,
                "score": score,
                "missing": result.get("missing")
            }
        except:
            if len(combined) > 500:
                return {"sufficient": True, "score": 0.8, "missing": None}
            else:
                return {"sufficient": False, "score": 0.2, "missing": "检索结果太少，需要更多信息"}
    
    def evaluate(self, user_query: str, retrieved_texts: List[str], 
                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        combined = "\n\n---\n\n".join(retrieved_texts) if retrieved_texts else "No retrieved results."
        context_str = json.dumps(context, ensure_ascii=False, indent=2) if context else "No additional context."

        prompt = f"""You are a professional information evaluation expert. Your task is to assess whether the **retrieved information** is sufficient to fulfill the user's **information need** given the **goal/objective** and **additional context**.

**Goal / User Question**:
{user_query}

**Additional Context (e.g., ticker, market sentiment, etc.)**:
{context_str}

**Retrieved Information**:
{combined[:4000]}

Please score the retrieved information on the following four dimensions (each score 0-1, two decimal places):
1. **Relevance**: How directly does the information address the user's question? Is it focused on the core topic?
2. **Completeness**: Does the information cover all key aspects of the question? Are there obvious gaps?
3. **Factual Accuracy**: Is the information based on reliable facts, data, or citations? Are there contradictions or speculations?
4. **Actionable Insight**: Does the information provide clear insights, recommendations, or conclusions rather than just background?

Compute an **overall score** as a weighted average: Relevance 0.4, Completeness 0.3, Factual Accuracy 0.2, Actionable Insight 0.1.

**Scoring guidelines**:
- 0.9-1.0: Fully sufficient, rich and directly usable information.
- 0.7-0.9: Largely sufficient, minor gaps that can be filled by common sense.
- 0.5-0.7: Partially sufficient, additional retrieval or inference needed.
- 0.3-0.5: Severely insufficient, most key information missing.
- 0.0-0.3: Almost useless, need to re-retrieve.

**Output requirements**: Only output a valid JSON object with the following structure:
{{
    "breakdown": {{"relevance": 0.xx, "completeness": 0.xx, "factual_accuracy": 0.xx, "actionable_insight": 0.xx}},
    "score": 0.xx,
    "sufficient": true/false,
    "missing": "If insufficient, describe the missing key information in one sentence; otherwise null",
    "suggested_next_queries": ["If insufficient, provide 1-3 query phrases to retrieve missing information; if sufficient, empty list"]
}}

Note: The `sufficient` field should be determined based on `score >= {self.threshold}` (your threshold is {self.threshold}). Do not output any additional explanation.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2048, # 800,
                response_format={"type": "json_object"}  # if the model supports it
            )
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # ensure required fields exist
            if "breakdown" not in result:
                result["breakdown"] = {}
            result.setdefault("score", 0.5)
            result.setdefault("sufficient", result.get("score", 0) >= self.threshold)
            result.setdefault("missing", None)
            result.setdefault("suggested_next_queries", [])
            
            return result
            
        except Exception as e:
            print(f"Evaluation failed: {e}")
            # fallback: simple heuristic based on text length
            if len(combined) > 500:
                return {"sufficient": True, "score": 0.8, "breakdown": {}, "missing": None, "suggested_next_queries": []}
            else:
                return {"sufficient": False, "score": 0.2, "breakdown": {}, 
                        "missing": "Retrieved results are too few, more information needed", 
                        "suggested_next_queries": [user_query]}



# evaluator.py
import json
from openai import OpenAI
from typing import Dict, Any, List, Optional

class Evaluator:
    def __init__(self, config):
        self.client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY
        )
        self.model = config.LLM_MODEL
        self.threshold = config.SUFFICIENCY_THRESHOLD

    def evaluate(self, user_query: str, retrieved_texts: List[str], 
                 context: Optional[Dict[str, Any]] = None,
                 role: Optional[str] = None) -> Dict[str, Any]:
        if not retrieved_texts:
            return {"filtered_texts": [], "score": 0, "sufficient": False,
                    "missing": "No results retrieved", "suggested_next_queries": []}

        results_with_index = list(enumerate(retrieved_texts))
        critiques = []
        filtered_indices = []
        filtered_texts = []

        """ 对每个检索到的文本片段进行批判评估，并根据评分决定是否保留该片段 
            1. 遍历所有检索结果：for idx, text in results_with_index 遍历当前轮次的所有候选片段（results_with_index 是带索引的列表）。
            2. 调用批判函数：critique = self._critique_single(user_query, text, context, role) 让 LLM 对该片段打分，返回一个包含 relevance_score（相关性）、factual_score（事实准确性）、role_score（角色适配度）、actionable_score（可操作性）等字段的 JSON。
            3. 打印和延迟：打印批判结果（便于调试），然后 time.sleep(5.0) 控制请求频率，避免过载 LLM 服务。
            4. 强制决定保留与否：从批判结果中提取 relevance_score 和 factual_score，只有当两者都 ≥ 0.6 时，才将该片段标记为保留（keep = True），否则丢弃。这是硬阈值过滤，不依赖模型返回的 keep 字段，确保只有高相关性且事实准确的片段进入后续环节。
            5. 记录批判和过滤结果：将批判详情存入 critiques 列表，如果 keep 为真，则将片段索引和文本分别加入 filtered_indices 和 filtered_texts，供后续整体评估使用。"""
        for idx, text in results_with_index:
            critique = self._critique_single(user_query, text, context, role)
            time.sleep(5.0)
            # ---- 改进1：强制根据分数决定 keep ----
            relevance = critique.get("relevance_score", 0.0)
            factual = critique.get("factual_score", 0.0)
            # 模型可能返回 keep 字段，但我们强制覆盖
            keep = (relevance >= 0.6 and factual >= 0.6)
            # 可选：更新 critique 中的 keep 字段以反映最终决策
            critique["keep"] = keep
            # ------------------------------------
            critiques.append((idx, critique))
            if keep:
                filtered_indices.append(idx)
                filtered_texts.append(text)

        # 整体评估信息充分性
        """ 对经过批判过滤后保留下来的所有文本片段进行整体评估，判断这些信息是否足以回答用户问题。
        具体功能包括：
            1. 将 filtered_texts 中的所有片段拼接成一个整体。
            2. 调用 LLM，结合用户问题、角色和上下文，评估当前信息的充分性。
            3. 返回一个字典，包含：
                3.1 score：0-1 的充分性得分。
                3.2 sufficient：布尔值，表示是否达到阈值（通常为 0.7）。
                3.3 missing：如果信息不足，描述缺失的关键信息；否则为 None。
                3.4 可能还包括 suggested_next_queries 等。
            4. 上层（RAGAgent.run）根据 sufficient 决定是否停止迭代，若不足则利用 missing 或 suggested_next_queries 指导下一轮检索。 """
        overall = self._overall_assessment(user_query, filtered_texts, context, role)
        # ---- 改进3：使用配置阈值重新计算 sufficient ----
        score = overall.get("score", 0.0)
        sufficient = score >= self.threshold
        overall["sufficient"] = sufficient
        # ------------------------------------------------

        suggested = self._generate_suggested_queries(user_query, filtered_texts, overall, role)

        return {
            "filtered_texts": filtered_texts,
            "score": score,
            "sufficient": sufficient,
            "missing": overall.get("missing", ""),
            "suggested_next_queries": suggested,
            "critiques": critiques,
            "filtered_indices": filtered_indices
        }

    def _critique_single(self, query: str, text: str, context: dict = None, role: str = None) -> dict:
        prompt = f"""You are a strict information critic for a RAG system.
User query: {query}
Role: {role if role else 'general'}
Additional context: {json.dumps(context, ensure_ascii=False) if context else 'None'}

Retrieved passage:
{text[:1500]}

Evaluate this passage against the following criteria:
1. **Relevance**: Does it directly answer or provide key evidence for the query?
2. **Factual consistency**: Is it free from contradictions or speculation?
3. **Role appropriateness**: Is the level of detail/jargon appropriate for the role?
4. **Actionability**: Does it offer concrete insights or steps?

Output a JSON object:
{{
    "relevance_score": 0-1,
    "factual_score": 0-1,
    "role_score": 0-1,
    "actionable_score": 0-1,
    "reason": "brief explanation"
}}
Important: Do NOT include a "keep" field. We will decide based on scores.
"""
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2048, # 300,
                response_format={"type": "json_object"}
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            print(f"Critique failed: {e}")
            time.sleep(30.0)
            return {
                "relevance_score": 0.0,
                "factual_score": 0.0,
                "role_score": 0.0,
                "actionable_score": 0.0,
                "reason": "Critique error, reject to be safe"
            }

    def _overall_assessment_v1(self, query: str, filtered_texts: List[str], context: dict, role: str) -> dict:
        if not filtered_texts:
            return {"score": 0.0, "missing": "All results were rejected."}

        combined = "\n\n---\n\n".join(filtered_texts)
        prompt = f"""Given the user query, role, and filtered passages, assess information sufficiency.

User query: {query}
Role: {role if role else 'general'}
Context: {json.dumps(context) if context else 'None'}
Filtered passages:
{combined[:3000]}

Output JSON:
{{
    "score": 0-1,
    "missing": "if score < 0.7, describe what is missing; otherwise null"
}}
"""
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2048, # 200,
                response_format={"type": "json_object"}
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            print(f"Overall assessment failed: {e}")
            return {"score": 0.5, "missing": "Assessment error"}
    

    def _overall_assessment(self, query: str, filtered_texts: List[str], context: dict, role: str) -> dict:
        if not filtered_texts:
            return {"score": 0.0, "missing": "All results were rejected."}

        combined = "\n\n---\n\n".join(filtered_texts)
        total_len = len(combined)
        
        # 配置采样参数
        SAMPLE_LEN = 2048            # 每次采样的字符数
        MAX_SAMPLES = 3              # 最多采样次数（避免过多请求）
        THRESHOLD = 3000             # 超过此长度启用采样
        
        def call_llm_for_score(text_sample: str) -> float:
            prompt_origin = f"""Given the user query, role, and filtered passages, assess information sufficiency.

User query: {query}
Role: {role if role else 'general'}
Context: {json.dumps(context) if context else 'None'}
Filtered passages (excerpt): {text_sample}

    Output JSON:
    {{
        "score": 0-1,
        "missing": "if score < 0.7, describe what is missing; otherwise null"
    }}
    """
            prompt = f"""You are an expert evaluator of information sufficiency for an AI-powered investment research agent. Your task is to assess whether the provided passages (excerpts) collectively contain enough information to answer the user's query.

**User Query:** {query}
**Role:** {role if role else 'general'}
**Additional Context:** {json.dumps(context, ensure_ascii=False) if context else 'None'}

**Passages to Evaluate (excerpt, may be incomplete):**
{text_sample}

Please evaluate based on the following four criteria (each score 0-1, one decimal place):
1. **Relevance (0-1)** : How directly do the passages address the user's specific question? Are they on‑topic?
2. **Completeness (0-1)** : Do the passages cover all the key aspects needed to fully answer the question? Are there obvious gaps?
3. **Factuality (0-1)** : Are the passages factual, consistent, and free from speculation or contradiction? Do they cite reliable sources?
4. **Actionability (0-1)** : Do the passages provide concrete, actionable insights, recommendations, or conclusions that the investment manager can directly use?

Compute the **Overall Score** as the weighted average:  
**Overall = 0.4 * Relevance + 0.3 * Completeness + 0.2 * Factuality + 0.1 * Actionability**

Then output a **JSON object** with the following fields:
- "score" : the overall score (float, 0-1)
- "missing" : if score < 0.7, a short sentence describing the most critical missing information; otherwise null

Example output:
{{"score": 0.65, "missing": "Lacks specific guidance on debt-to-equity ratio management"}}

Output ONLY the JSON object, no additional text.
"""
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=2048,
                    response_format={"type": "json_object"}
                )
                data = json.loads(resp.choices[0].message.content)
                return data.get("score", 0.5)
            except Exception as e:
                print(f"Overall assessment (sampling) failed: {e}")
                return 0.5  # 降级分数

        # 如果长度在安全范围内，直接使用完整内容
        if total_len <= THRESHOLD:
            score = call_llm_for_score(combined)
            missing = None if score >= 0.7 else "Insufficient information"
            return {"score": score, "missing": missing}
        
        # 否则进行多次随机采样
        scores = []
        # 确定采样次数：最多 MAX_SAMPLES，且确保不超过总长度可采样次数
        num_samples = min(MAX_SAMPLES, max(1, total_len // SAMPLE_LEN))
        for index in range(num_samples):
            if total_len > SAMPLE_LEN:
                start = random.randint(0, total_len - SAMPLE_LEN)
                sample = combined[start:start + SAMPLE_LEN]
            else:
                sample = combined
            score = call_llm_for_score(sample)
            scores.append(score)
        
        avg_score = sum(scores) / len(scores)
        missing = None if avg_score >= 0.7 else "Insufficient information (sampled)"
        return {"score": avg_score, "missing": missing}



    def _generate_suggested_queries(self, query: str, filtered_texts: List[str], overall: dict, role: str) -> List[str]:
        if overall.get("sufficient", False) or not filtered_texts:
            return []
        missing = overall.get("missing", "")
        prompt = f"""Based on the missing information described below, generate up to 2 specific sub-queries to retrieve the missing information.

User query: {query}
Role: {role if role else 'general'}
Missing: {missing}

Output a JSON object with a field "queries" containing an array of strings.
Example: {{"queries": ["query1", "query2"]}}
"""

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2048, # 200,
                response_format={"type": "json_object"}
            )
            data = json.loads(resp.choices[0].message.content)
            queries = data.get("queries", [])
            if isinstance(queries, list):
                return queries[:2]
            else:
                return []
        except Exception:
            return []