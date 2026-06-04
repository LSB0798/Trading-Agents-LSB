# evaluator.py
import json
from openai import OpenAI
from typing import Dict, List, Optional
from typing import Dict, Any, List, Optional
import time

class Evaluator_v0:
    def __init__(self, config):
        self.client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY
        )
        self.model = config.LLM_MODEL
        self.threshold = config.SUFFICIENCY_THRESHOLD
    
    def evaluate_v0(self, user_query: str, retrieved_texts: list) -> dict:
        """
        评估当前检索到的所有文本是否足以回答用户问题。
        返回: {"sufficient": bool, "score": float, "missing": str (optional)}
        """
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
            max_tokens=300
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
            # 降级：简单根据文本长度判断
            if len(combined) > 500:
                return {"sufficient": True, "score": 0.8, "missing": None}
            else:
                return {"sufficient": False, "score": 0.2, "missing": "检索结果太少，需要更多信息"}
    
    def evaluate(self, user_query: str, retrieved_texts: List[str], 
                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluate whether the retrieved information is sufficient to answer the user query.
        Returns:
            {
                "sufficient": bool,
                "score": float (0-1),
                "breakdown": {"relevance": float, "completeness": float, "factual_accuracy": float, "actionable_insight": float},
                "missing": str (optional),
                "suggested_next_queries": list (optional)
            }
        """
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
                max_tokens=800,
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
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            # ---- 改进2：降级逻辑更严格 ----
            print(f"Critique failed: {e}")
            time.sleep(30.0)
            return {
                "relevance_score": 0.0,
                "factual_score": 0.0,
                "role_score": 0.0,
                "actionable_score": 0.0,
                "reason": "Critique error, reject to be safe"
            }
            # -----------------------------

    def _overall_assessment(self, query: str, filtered_texts: List[str], context: dict, role: str) -> dict:
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
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            print(f"Overall assessment failed: {e}")
            return {"score": 0.5, "missing": "Assessment error"}

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
                max_tokens=200,
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