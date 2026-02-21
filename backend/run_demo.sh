#!/bin/bash
cd "$(dirname "$0")"

# Cleanup on exit
trap 'echo "Shutting down..."; kill $(jobs -p) 2>/dev/null; exit' SIGINT SIGTERM

echo "=== Multi-Agent Negotiation System ==="
echo ""

echo "Starting Registry on port 8000..."
python3 -m uvicorn registry:app --port 8000 --log-level warning &

sleep 2

echo "Starting Alice's agent on port 8001..."
python3 base_agent.py --user-name Alice --port 8001 &

echo "Starting Bob's agent on port 8002..."
python3 base_agent.py --user-name Bob --port 8002 &

echo "Starting Charlie's agent on port 8003..."
python3 base_agent.py --user-name Charlie --port 8003 &

sleep 2

echo "Starting API Gateway on port 8080..."
python3 api_gateway.py &

echo ""
echo "All services started!"
echo "  Registry:  http://localhost:8000"
echo "  Alice:     http://localhost:8001"
echo "  Bob:       http://localhost:8002"
echo "  Charlie:   http://localhost:8003"
echo "  Gateway:   http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop all services."
wait
