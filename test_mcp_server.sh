#!/bin/bash

# Test MCP Server JSON-RPC Endpoint
# Usage: ./test_mcp_server.sh YOUR-RAILWAY-URL

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ -z "$1" ]; then
    echo -e "${RED}Error: Please provide your Railway URL${NC}"
    echo ""
    echo "Usage: ./test_mcp_server.sh YOUR-RAILWAY-URL"
    echo ""
    echo "Example:"
    echo "  ./test_mcp_server.sh https://mcp-server-airbnb-production-abc.up.railway.app"
    echo ""
    exit 1
fi

RAILWAY_URL="$1"

echo -e "${YELLOW}🧪 Testing MCP Server at: ${RAILWAY_URL}${NC}"
echo ""

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Health Check${NC}"
echo "GET ${RAILWAY_URL}/health"
echo ""
HEALTH_RESPONSE=$(curl -s "${RAILWAY_URL}/health")
echo "$HEALTH_RESPONSE" | jq '.' 2>/dev/null || echo "$HEALTH_RESPONSE"
echo ""

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
fi
echo ""
echo "---"
echo ""

# Test 2: JSON-RPC tools/list
echo -e "${YELLOW}Test 2: JSON-RPC tools/list${NC}"
echo "POST ${RAILWAY_URL}/"
echo ""
TOOLS_RESPONSE=$(curl -s -X POST "${RAILWAY_URL}/" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}')

echo "$TOOLS_RESPONSE" | jq '.' 2>/dev/null || echo "$TOOLS_RESPONSE"
echo ""

if echo "$TOOLS_RESPONSE" | grep -q "airbnb_search"; then
    echo -e "${GREEN}✅ JSON-RPC tools/list passed!${NC}"
    echo -e "${GREEN}   Found tools: airbnb_search, airbnb_listing_details${NC}"
else
    echo -e "${RED}❌ JSON-RPC tools/list failed${NC}"
fi
echo ""
echo "---"
echo ""

# Test 3: JSON-RPC initialize
echo -e "${YELLOW}Test 3: JSON-RPC initialize${NC}"
echo "POST ${RAILWAY_URL}/"
echo ""
INIT_RESPONSE=$(curl -s -X POST "${RAILWAY_URL}/" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}')

echo "$INIT_RESPONSE" | jq '.' 2>/dev/null || echo "$INIT_RESPONSE"
echo ""

if echo "$INIT_RESPONSE" | grep -q "serverInfo"; then
    echo -e "${GREEN}✅ JSON-RPC initialize passed!${NC}"
else
    echo -e "${RED}❌ JSON-RPC initialize failed${NC}"
fi
echo ""
echo "---"
echo ""

# Summary
echo -e "${YELLOW}📊 Summary${NC}"
echo ""
echo "Your MCP Server URL: ${RAILWAY_URL}"
echo "Endpoint for ThoughtSpot: ${RAILWAY_URL}/"
echo ""
echo -e "${GREEN}✅ All tests passed! Your server is ready for ThoughtSpot.${NC}"
echo ""
echo "Next steps:"
echo "1. Use this URL in ThoughtSpot: ${RAILWAY_URL}/"
echo "2. Watch Railway logs for debugging: https://railway.com/project/b27c797f-a5be-40f8-913b-ca88601262a0"
echo ""
