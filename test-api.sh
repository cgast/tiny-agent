#!/bin/bash
# Test script for agent-api.py
# This demonstrates both auto-respond mode and interactive mode

set -e

API_URL="http://localhost:5000"
SESSION_ID="test-$(date +%s)"

echo "========================================="
echo "Testing tiny-agent API"
echo "========================================="
echo ""

# Test 1: Health check
echo "Test 1: Health Check"
echo "-------------------"
curl -s "${API_URL}/health" | jq .
echo ""
echo ""

# Test 2: Simple prompt with auto-respond mode (fire-and-forget)
echo "Test 2: Auto-respond mode (fire-and-forget)"
echo "-------------------------------------------"
echo "Session ID: ${SESSION_ID}-auto"
echo "Prompt: List files in current directory"
echo ""
echo "Response stream:"

curl -X POST "${API_URL}/prompt" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"${SESSION_ID}-auto\",
    \"prompt\": \"List files in current directory\",
    \"auto_respond\": true
  }" \
  2>/dev/null

echo ""
echo ""

# Test 3: Interactive mode (requires manual response)
echo "Test 3: Interactive mode"
echo "------------------------"
echo "Session ID: ${SESSION_ID}-interactive"
echo "Prompt: What is 2+2?"
echo ""
echo "This test requires sending a response via another terminal window:"
echo ""
echo "  curl -X POST ${API_URL}/respond \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"session_id\": \"${SESSION_ID}-interactive\", \"response\": \"/done\"}'"
echo ""
echo "Starting stream (waiting for your response)..."
echo ""

# This will block until we send a response
curl -X POST "${API_URL}/prompt" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"${SESSION_ID}-interactive\",
    \"prompt\": \"What is 2+2?\",
    \"auto_respond\": false
  }" \
  2>/dev/null &

STREAM_PID=$!

# Give the stream a moment to start
sleep 2

# Auto-send response after 2 seconds (simulating user interaction)
echo ""
echo "(Auto-sending response in background after 2s...)"
curl -X POST "${API_URL}/respond" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"${SESSION_ID}-interactive\",
    \"response\": \"/done\"
  }" \
  2>/dev/null | jq .

# Wait for stream to complete
wait $STREAM_PID

echo ""
echo ""
echo "========================================="
echo "All tests completed!"
echo "========================================="
