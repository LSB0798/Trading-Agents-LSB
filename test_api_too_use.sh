curl http://10.20.223.83:61273/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3_32B",
    "messages": [{"role": "user", "content": "Get stock data for 0700.HK from 2026-04-12 to 2026-05-12"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_stock_data",
        "description": "Retrieve stock price data",
        "parameters": {
          "type": "object",
          "properties": {
            "symbol": {"type": "string"},
            "start_date": {"type": "string"},
            "end_date": {"type": "string"}
          },
          "required": ["symbol", "start_date", "end_date"]
        }
      }
    }],
    "stream": false
  }'