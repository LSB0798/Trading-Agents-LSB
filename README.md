<p align="center">
  <img src="assets/schema.png" style="width: 80%; height: auto;">
</p>

# TradingAgents with AI Hedge Fund Analysts

**TradingAgents** is a multi‑agent trading decision framework that simulates a hedge fund investment team consisting of **22 AI analysts** — a dedicated news analyst squad plus **19 master analysts** inspired by legendary investors (e.g., Ben Graham, Warren Buffett, Peter Lynch, Charlie Munger), a bull/bear researcher team, risk analysts, and a portfolio manager. The system generates trading decisions through multi‑round debates and comprehensive signal aggregation.

## 🧠 Core Architecture

### Analyst Team

The system currently includes the following analysts:

| Analyst Type | Count | Description |
|--------------|-------|-------------|
| **News Analysts** | 4 | Multi‑source news intelligence squad. Each analyst fetches from a distinct provider to generate a macro environment report and sentiment signals. |
| &nbsp;&nbsp;├─ Alpha News Analyst | 1 | Retrieves market‑moving news via the **Alpha Vantage** API. |
| &nbsp;&nbsp;├─ Finnhub News Analyst | 1 | Retrieves company‑specific and macro news via the **Finnhub** API. |
| &nbsp;&nbsp;├─ GNews Analyst | 1 | Retrieves broad global news and headlines via the **GNews** API. |
| &nbsp;&nbsp;└─ YFinance News Analyst | 1 | Retrieves company‑specific and global macro news via **yfinance**. |
| **Master Analysts** | 19 | Based on the investment philosophies of famous masters (Graham, Buffett, Lynch, Munger, etc.), each performs quantitative analysis and LLM reasoning independently, outputting trading signals (`bullish`/`bearish`/`neutral`) with confidence scores. |

### Workflow

1. **Parallel Analysis**: The News Analysts and the 19 Master Analysts run **in parallel**, each retrieving data and generating reports/signals.
2. **Signal Aggregation**: After all analysts finish, the **SignalAggregator** node collects and prints a consolidated signal summary.
3. **Multi‑Round Debate**: **Bull Researcher** and **Bear Researcher** engage in multi‑round debates based on the aggregated signals and raw reports (number of rounds configurable).
4. **Research Manager Decision**: The **Research Manager** formulates an initial investment plan after the debate.
5. **Trader Execution**: The **Trader** generates specific trade orders.
6. **Risk Debate**: **Aggressive/Conservative/Neutral** risk analysts discuss risk exposure in multiple rounds.
7. **Portfolio Manager**: The **Portfolio Manager** synthesises all information and outputs the final trading decision (`BUY`/`SELL`/`HOLD`/`SHORT` etc.).

### Data Sources

- **Financial Data**: Retrieved via the [Financial Datasets API](https://financialdatasets.ai/) (requires an API key).
- **News Data**: Fetched from multiple providers for cross‑validation and broader coverage:
  - **Alpha Vantage** — global macro and company news.
  - **Finnhub** — real‑time company and market news.
  - **GNews** — worldwide news headlines and articles.
  - **yfinance** — company‑specific and macro news.
- **LLM**: The system uses your locally deployed LLM (e.g., Qwen3‑32B) via an OpenAI‑compatible API endpoint.

### Optional Feature: RAG (Retrieval‑Augmented Generation)

RAG is **disabled by default** but can be enabled optionally. When activated, agents can query a local knowledge base (e.g., Buffett’s letters, Munger’s speeches) to enhance their reasoning. For setup details, see the [RAG Service Setup](#rag-service-setup) section below.

### RAG Service Setup (Optional)

If you wish to enable RAG, you can start a local retrieval service (using Milvus Lite + Qwen Embeddings) and place investment classics in the `./documents/` folder. The service will automatically be used by the agents.

> **Note**: In the default configuration, RAG is **turned off** and does not affect system operation.


## 📦 Installation & Usage

### Requirements

- Python 3.13+
- Docker (optional but recommended)

### Clone & Install

```bash
git clone <your-repo-url>
cd TradingAgents
conda create -n tradingagents python=3.13
conda activate tradingagents
pip install .
```

# Required for financial data
FINANCIAL_DATASETS_API_KEY=your-api-key

# News API keys (optional — only required if you use the corresponding analyst)
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
FINNHUB_API_KEY=your-finnhub-key
GNEWS_API_KEY=your-gnews-key

# For LLM (OpenAI‑compatible local endpoint)
OPENAI_API_BASE=http://your-local-llm:port/v1
OPENAI_API_KEY=dummy

# Run
```
python cli/main.py
```
Or use the test script:
```
python test.py
```
