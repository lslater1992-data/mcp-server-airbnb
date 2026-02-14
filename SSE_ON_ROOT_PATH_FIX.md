# SSE on Root Path Fix

## Problem Discovered

**ThoughtSpot's MCP Connection Flow:**
1. **Step 1:** POST to `/` with JSON-RPC `initialize`
   ```http
   POST / HTTP/1.1
   Content-Type: application/json

   {"jsonrpc":"2.0","method":"initialize","params":{...}}
   ```

2. **Step 2:** GET to `/` with `Accept: text/event-stream`
   ```http
   GET / HTTP/1.1
   Accept: text/event-stream
   ```

**The Issue:**
- Step 1 worked ✅
- Step 2 failed ❌ - Server returned JSON info instead of opening SSE stream
- ThoughtSpot expected SSE on `/`, not `/sse`

---

## Solution: Dynamic GET / Handler

The GET / endpoint now **detects the Accept header** and responds accordingly:

### **Scenario A: SSE Request**
```http
GET / HTTP/1.1
Accept: text/event-stream
```
**→ Opens SSE connection** ✅

### **Scenario B: Regular Request**
```http
GET / HTTP/1.1
Accept: application/json
```
**→ Returns server info JSON** ✅

---

## Updated Code

```typescript
app.get('/', async (req, res) => {
  const acceptHeader = req.get('accept') || '';

  // Check if client wants SSE
  if (acceptHeader.includes('text/event-stream')) {
    // Open SSE connection (same logic as /sse endpoint)
    const sessionId = Math.random().toString(36).substring(7);

    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    const transport = new SSEServerTransport('/messages', res);
    activeTransports.set(sessionId, transport);
    await server.connect(transport);

    // Handle connection cleanup...
  } else {
    // Return regular JSON info
    res.json({ name: 'Airbnb MCP Server', ... });
  }
});
```

---

## Complete ThoughtSpot Flow

### **1. Initialize (JSON-RPC)**
```
ThoughtSpot → POST /
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": { "name": "thoughtspot" }
  }
}

Server → Response
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2025-06-18",  ✅ Matches!
    "capabilities": { "tools": {} },
    "serverInfo": { "name": "airbnb" }
  }
}
```

### **2. Open SSE Connection**
```
ThoughtSpot → GET /
Accept: text/event-stream

Server → SSE Stream  ✅ (was returning JSON before)
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"endpoint":"..."}
```

### **3. List Tools (via SSE)**
```
ThoughtSpot → (via SSE messages)
{
  "jsonrpc": "2.0",
  "method": "tools/list"
}

Server → (via SSE)
{
  "result": {
    "tools": [
      { "name": "airbnb_search", ... },
      { "name": "airbnb_listing_details", ... }
    ]
  }
}
```

### **4. Call Tool (via SSE)**
```
ThoughtSpot → (via SSE)
{
  "method": "tools/call",
  "params": {
    "name": "airbnb_search",
    "arguments": { "location": "San Francisco", ... }
  }
}

Server → (via SSE)
{
  "result": {
    "content": [{ "type": "text", "text": "{...search results...}" }]
  }
}
```

---

## Railway Logs - What to Expect

### **Step 1: Initialize**
```
[INFO] Incoming HTTP request: { "method": "POST", "path": "/" }
[INFO] JSON-RPC request received on root path
[INFO] Processing JSON-RPC method: { "method": "initialize" }
[INFO] Initialize response prepared: { "requestedVersion": "2025-06-18" }
[INFO] Sending JSON-RPC response
```

### **Step 2: SSE Connection (NEW!)**
```
[INFO] Incoming HTTP request: { "method": "GET", "path": "/" }
[INFO] Root endpoint accessed via GET: {
  "acceptHeader": "text/event-stream",
  "isSSERequest": true  ✅
}
[INFO] SSE connection requested on root path
[INFO] Creating SSE transport on root path
[INFO] Connecting MCP server to transport
[INFO] SSE connection established on root path
```

### **Step 3: Tools/List**
```
[INFO] ListTools request received
[INFO] Returning tools list: { "toolCount": 2 }
```

### **Step 4: Tools/Call**
```
[INFO] CallTool request received: { "tool": "airbnb_search" }
[INFO] Processing Airbnb search request
[INFO] Fetching Airbnb search page
[INFO] Search completed successfully: { "resultCount": 20 }
[INFO] Tool call completed successfully
```

---

## Key Differences from Before

### **Before:**
- GET / → Always returned JSON (even with `Accept: text/event-stream`)
- ThoughtSpot got JSON when it wanted SSE
- Connection failed after `initialize`

### **After:**
- GET / with `Accept: text/event-stream` → Opens SSE ✅
- GET / without SSE header → Returns JSON ✅
- ThoughtSpot gets SSE stream as expected
- Connection proceeds to `tools/list` and `tools/call`

---

## Why This Pattern?

This is the **combined transport pattern** where:
- **One endpoint (`/`)** handles both:
  - JSON-RPC initialization (POST)
  - SSE streaming (GET with proper header)

**Benefits:**
- Simpler URL structure
- Client doesn't need to know multiple endpoints
- Standard MCP pattern for HTTP transport

**Alternative pattern** (what we had before):
- POST / → JSON-RPC
- GET /sse → SSE (separate endpoint)

ThoughtSpot expects the **combined pattern**, not the separate endpoints.

---

## Testing

### **Test SSE Connection:**
```bash
curl -N -H "Accept: text/event-stream" https://your-railway-url.up.railway.app/
```

Should return:
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {...}
```

### **Test Regular GET:**
```bash
curl https://your-railway-url.up.railway.app/
```

Should return:
```json
{
  "name": "Airbnb MCP Server",
  "version": "0.1.3",
  ...
}
```

---

## Deploy

```bash
cd "/Users/luke.slater/Documents/Agentic Workflows/Airbnb-MCP-Railway-Deployment"
./push-to-github.sh
```

---

## Compatibility

### **Still Works:**
- ✅ GET /sse (legacy SSE endpoint)
- ✅ POST / (JSON-RPC)
- ✅ GET /health
- ✅ GET / without SSE header (info page)

### **Now Also Works:**
- ✅ **GET / with `Accept: text/event-stream`** (ThoughtSpot's pattern)

---

**Status:** Ready to deploy - SSE now available on root path with proper header detection
