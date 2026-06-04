# test.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# from rag_agent import RAGAgent, RAGAgentConfig
from core import RAGAgent
from config import RAGAgentConfig

def main():
    config = RAGAgentConfig()
    agent = RAGAgent(config)
    
    query = "margin of safet"
    context = {"ticker": "AAPL", "market": "margin of safet"}
    role = "research_manager"
    
    answer = agent.run(query, context=context, role=role)
    print("\n" + "="*60)
    print(answer)
    print("="*60)

if __name__ == "__main__":
    for _ in range(1):
        main()