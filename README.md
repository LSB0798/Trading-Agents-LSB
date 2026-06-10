<p align="center">
  <img src="assets/schema.png" style="width: 80%; height: auto;">
</p>

# TradingAgents‑RAG

---

## ✨ Selective RAG Integration

This fork selectively adds **retrieval‑augmented generation (RAG)** to the agents where investment wisdom is most valuable – analysts and the research manager. Other agents (researchers, trader, risk analysts, portfolio manager) rely on their original reasoning and the already enriched reports; they do not directly query the knowledge base. The model can (or is forced to) query a local knowledge base of investment classics (Buffett letters, Munger speeches, seminal books) and use the retrieved wisdom as arguments, evidence, or decision support.

> **Note**: “-” in the table below means the agent does not use RAG by design (its role does not benefit from direct quotes).

### 🧠 RAG Role per Agent

| Role | RAG Purpose | Injection Method |
|------|-------------|------------------|
| **Market Analyst** | Technical analysis & market psychology | Tool‑call (Agentic RAG) |
| **Social Media Analyst** | Sentiment & crowd behavior quotes | Tool‑call (Agentic RAG) |
| **News Analyst** | Macroeconomic & event insights | Tool‑call (Agentic RAG) |
| **Fundamentals Analyst** | Valuation & moat principles | Tool‑call (Agentic RAG) |
| **Bull / Bear Researcher** | Support bull/bear arguments with master quotes | - |
| **Research Manager** | Multi‑turn RAG Agent: plans sub‑queries, critiques results, iteratively retrieves until sufficient wisdom is gathered | **RAG Agent** (internal Planner + Evaluator + Retriever) |
| **Trader** | Trade discipline & position sizing | - |
| **Risk Analyst** | Risk control & margin of safety | - |
| **Portfolio Manager** | Final decision backing | - |

### 🤖 RAG Agent: Autonomous Multi‑Turn Retrieval for Research Manager

The **Research Manager** no longer uses a simple tool‑call or active injection. Instead, it runs a complete **autonomous RAG agent** that internally performs **planning, retrieval, critique, filtering, and iterative refinement** – all without human intervention.

#### How It Works

1. **Context Fact Extraction**  
   The incoming context (market report, sentiment report, news, fundamentals, debate history) is automatically decomposed into a list of key facts using a dedicated LLM call (`_extract_facts_from_context`). Each fact is a short, self‑contained statement relevant to the investment decision.

2. **Sub‑query Generation (Planner)**  
   For each extracted fact, the RAG agent calls the planner LLM **using JSON mode** (`response_format={"type": "json_object"}`) to generate 1‑3 targeted sub‑queries. This replaces the earlier function‑calling approach, which was unstable with the deployed model. The planner receives:
   - Original user query
   - The specific fact to focus on
   - Already queried terms (to avoid repetition)
   - Missing information feedback from previous iterations

3. **Retrieval**  
   Each sub‑query is sent to the underlying RAG retrieval service (Milvus Lite + Qwen embeddings), which returns the top‑k relevant document passages.

4. **Critique & Filtering (Evaluator)**  
   Every retrieved passage is independently judged by a critic LLM on four metrics:
   - *Relevance* (0‑1)
   - *Factual consistency* (0‑1)
   - *Role appropriateness* (0‑1)
   - *Actionable insight* (0‑1)  
   Only passages with `relevance ≥ 0.6` and `factual ≥ 0.6` are kept. Others are discarded.

5. **Overall Sufficiency Assessment**  
   After all sub‑queries for a fact are processed, the evaluator assesses whether the collected information sufficiently answers the user’s question. **To avoid overloading the LLM with extremely long inputs**, the overall assessment now uses **random sampling**: if the combined text exceeds a threshold (e.g., 3000 chars), it randomly samples up to three 2048‑character excerpts, scores each individually, and averages the results. This robustly prevents connection errors caused by oversized prompts.

6. **Iteration & Termination**  
   The loop continues until either:
   - The evaluator declares the information sufficient (score ≥ 0.7), or
   - A maximum of 2‑3 iterations is reached, or
   - No new sub‑queries can be generated.

7. **Final Output**  
   All kept passages are deduplicated and returned as a numbered list (e.g., `1. ...\n2. ...`). The Research Manager then uses these high‑quality, filtered passages to write the final investment plan.

#### Key Technical Features

- **JSON mode for planning** – replaced unstable function calling with robust `response_format={"type": "json_object"}`.
- **Random‑sampling overall assessment** – prevents input‑length induced crashes.
- **Automatic retry & exponential backoff** – handles temporary LLM or network failures.
- **Input length hard limits** – all prompts are truncated to safe lengths (e.g., 8000 chars) before being sent.
- **Full observability** – logs every iteration, sub‑query, critique score, and filtered count.

This design makes the Research Manager the most sophisticated agent in the framework, capable of **planning its own knowledge gaps and actively seeking the most relevant investment wisdom** before committing to a decision.

### 🔧 Three RAG Integration Modes

1. **Guided Tool Injection (Agentic RAG)**  
   - Used for analysts (market, social, news, fundamentals).  
   - `retrieve_xxx_wisdom` is registered as a LangChain `Tool` and bound with `bind_tools`.  
   - The LLM decides when and what to retrieve, generating its own query.  
   - The graph includes a dedicated `ToolNode` that executes the tool call.

2. **Active Injection (Modular RAG)**  
   - Used for researchers, trader, risk analysts, and portfolio manager.  
   - The RAG function is called directly inside the node, and the retrieved content is forcibly appended to the system prompt.  
   - No dependency on the model’s willingness to call tools; guarantees that master wisdom is always available.  
   - Particularly useful in debate and decision nodes to increase argument authority.

3. **RAG Agent (Autonomous Multi‑Turn Retrieval)**  
   - Used exclusively for the **Research Manager**.  
   - Invokes a dedicated `RAGAgent` that internally plans sub‑queries (using JSON mode), retrieves, critiques each passage, filters low‑quality results, and iterates until information is sufficient.  
   - Automatically splits the analysis context into key facts and generates targeted sub‑queries for each fact.  
   - Returns a numbered list of high‑relevance, fact‑filtered passages for the final investment decision.  
   - Completely autonomous – does not rely on hand‑crafted prompts or forced tool injection.

### 📚 RAG Knowledge Base

The knowledge base is built from three sources (converted by `marker‑pdf`):
- `Reminiscences of a Stock Operator 2006`
- `pdfs`

It contains:
- Warren Buffett’s annual shareholder letters
- Charlie Munger’s speeches and interviews
- Classic investment books (e.g., *Poor Charlie’s Almanack*, *Margin of Safety*)

### 🖥️ RAG Service Setup

A standalone retrieval service (`start_rag.py`) provides the RAG backend:

- **Vector database**: Milvus Lite (embedded)
- **Embedding model**: Qwen3‑Embedding‑0.6B (local)
- **Reranker**: Qwen3‑Reranker‑0.6B (local)
- **Documents**: place `.md`, `.txt`, `.docx`, or `.pdf` files in the `./documents/` directory (supports large corpora; tested with 30 GB).

#### Step 1: Prepare the document corpus
```bash
mkdir documents
# Copy your investment books, speeches, or reports into ./documents
# The system recursively processes all supported files.

#### Step 2: Start the RAG service
```
python start_rag.py
```
On first run, the service will:
- Load all documents from ./documents/
- Split text into chunks (smart chunking for mixed Chinese/English)
- Generate embeddings using Qwen3‑0.6B
- Build a Milvus Lite index (stored locally)
- Launch a FastAPI server on http://localhost:8000

You can test the service with:
```
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "value investing margin of safety"}'
```
Note: The full document corpus is 30 GB in size. During the first startup, the RAG system will chunk and index these documents. On subsequent startups, the pre‑built index will be reused directly.
Once the RAG service is running, the TradingAgents agents will automatically call its retrieve_*_wisdom tools to perform retrieval.

### 🚀 Typical Impact

- The **Market Analyst** may cite Buffett’s “Mr. Market” metaphor when describing volatility.  
- **Bull/Bear researchers** can directly quote Munger on “moats” or “circle of competence” during debates.  
- The **Research Manager** employs a fully autonomous RAG agent that robustly retrieves and filters relevant investment wisdom, avoiding service crashes through JSON mode and length‑safe sampling.
- The **Portfolio Manager** often includes a classic quote to back the final BUY/HOLD/SELL recommendation.
---

## 📦 Installation & Usage (same as original)

### Requirements

- Python 3.13+
- Docker (optional but recommended)

### Clone & Install

```bash
git clone https://github.com/LSB0798/Trading-Agents-LSB.git
cd Trading-Agents-LSB
conda create -n tradingagents-rag python=3.13
conda activate tradingagents-rag
pip install .