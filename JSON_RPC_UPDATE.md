# JSON-RPC Support Added to server.ts

## Problem Discovered
ThoughtSpot was sending **JSON-RPC requests via POST to `/`**, but the server only handled:
- GET / - Info page
- GET /sse - SSE transport
- POST /messages - SSE message handling

**Result:** 404 errors because POST / wasn't configured

---

## Solution: Dual Transport Support

The server now supports **BOTH transports**:

### 1. **JSON-RPC over HTTP POST** (for ThoughtSpot)
- Endpoint: `POST /`
- Format: JSON-RPC 2.0
- Content-Type: `application/json`

### 2. **Server-Sent Events** (for other clients)
- Endpoint: `GET /sse`
- Format: SSE
- Content-Type: `text/event-stream`

---

## JSON-RPC Methods Supported

### **initialize**
Request:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "thoughtspot",
      "version": "1.0"
    }
  }
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "serverInfo": {
      "name": "airbnb",
      "version": "0.1.3"
    }
  }
}
```

---

### **tools/list**
Request:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "airbnb_search",
        "description": "Search for Airbnb listings...",
        "inputSchema": { ... }
      },
      {
        "name": "airbnb_listing_details",
        "description": "Get detailed information...",
        "inputSchema": { ... }
      }
    ]
  }
}
```

---

### **tools/call**
Request:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "airbnb_search",
    "arguments": {
      "location": "San Francisco",
      "checkin": "2026-03-01",
      "checkout": "2026-03-05",
      "adults": 2
    }
  }
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"searchUrl\":\"...\",\"searchResults\":[...],\"paginationInfo\":{...}}"
      }
    ],
    "isError": false
  }
}
```

---

### **ping**
Request:
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "ping"
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {}
}
```

---

## What Changed in server.ts

### **Added POST / Handler**
```typescript
app.post('/', async (req, res) => {
  // 1. Validate JSON-RPC request
  // 2. Route to appropriate MCP method handler
  // 3. Execute tool if tools/call
  // 4. Return JSON-RPC response
});
```

### **Updated GET / to Show Both Transports**
```typescript
app.get('/', (req, res) => {
  res.json({
    transports: ['http+json-rpc', 'sse'],
    endpoints: {
      'json-rpc': 'POST /',
      sse: 'GET /sse',
      ...
    }
  });
});
```

### **Comprehensive Logging for JSON-RPC**
Every JSON-RPC request logs:
- Method being called
- Request ID
- Parameters
- Execution time
- Response preview
- Any errors

---

## Expected Railway Logs

### When ThoughtSpot Connects:
```
[INFO] Incoming HTTP request: {
  "method": "POST",
  "path": "/",
  "headers": { "content-type": "application/json", "user-agent": "python-httpx" }
}

[INFO] JSON-RPC request received on root path: {
  "contentType": "application/json",
  "userAgent": "python-httpx/...",
  "body": { "jsonrpc": "2.0", "id": 1, "method": "initialize", ... }
}

[INFO] Processing JSON-RPC method: {
  "method": "initialize",
  "id": 1,
  "hasParams": true
}

[INFO] Handling initialize request

[INFO] Initialize response prepared

[INFO] Sending JSON-RPC response: {
  "method": "initialize",
  "id": 1,
  "resultPreview": "{\"protocolVersion\":\"2024-11-05\",..."
}
```

### When ThoughtSpot Calls a Tool:
```
[INFO] JSON-RPC request received on root path

[INFO] Processing JSON-RPC method: {
  "method": "tools/call",
  "id": 3
}

[INFO] Handling tools/call request: {
  "toolName": "airbnb_search",
  "arguments": { "location": "San Francisco", ... }
}

[INFO] Executing airbnb_search via JSON-RPC

[INFO] Processing Airbnb search request: {
  "location": "San Francisco",
  "checkin": "2026-03-01",
  ...
}

[INFO] Built search URL

[INFO] Fetching Airbnb search page

[INFO] Received HTML response: { "size": 487234 }

[INFO] Search completed successfully: { "resultCount": 20 }

[INFO] Tool execution completed: {
  "tool": "airbnb_search",
  "duration": "3421ms",
  "success": true
}

[INFO] Sending JSON-RPC response: {
  "method": "tools/call",
  "id": 3,
  "resultPreview": "{\"content\":[{\"type\":\"text\",\"text\":\"{\\\"searchUrl\\\"..."
}
```

---

## Error Handling

### Invalid JSON-RPC Request
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid Request"
  },
  "id": null
}
```

### Method Not Found
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32601,
    "message": "Method not found: unknown_method"
  },
  "id": 1
}
```

### Internal Error
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Error message here",
    "data": "Stack trace (in development)"
  },
  "id": 1
}
```

---

## Backwards Compatibility

✅ **SSE transport still works** - clients using GET /sse are unaffected
✅ **Health endpoint unchanged** - GET /health still works
✅ **All existing functionality preserved**

**New capability:** JSON-RPC clients (like ThoughtSpot) can now use POST /

---

## Testing

### Test JSON-RPC with curl:
```bash
curl -X POST https://your-railway-url.up.railway.app/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

Expected response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      { "name": "airbnb_search", ... },
      { "name": "airbnb_listing_details", ... }
    ]
  }
}
```

---

## Deploy This Update

Same as before:
```bash
cd "/Users/luke.slater/Documents/Agentic Workflows/Airbnb-MCP-Railway-Deployment"
./push-to-github.sh
```

Railway will auto-deploy in ~3 minutes.

---

## What This Fixes

**Before:**
- ThoughtSpot POST / → 404 error
- No JSON-RPC support
- Only SSE transport available

**After:**
- ThoughtSpot POST / → ✅ JSON-RPC response
- Full JSON-RPC 2.0 support
- Both JSON-RPC and SSE transports available
- ThoughtSpot gets actual search results!

---

**Status:** Ready to deploy - server.ts updated with JSON-RPC support
