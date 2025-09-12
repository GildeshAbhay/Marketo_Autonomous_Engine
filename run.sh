curl -X POST http://127.0.0.1:8002/mcp \
-H "Content-Type: application/json" \
-H "Accept: application/json" \
-d '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-04-10"}}'