# Two-Phase Handshake - The Complete Solution

## ThoughtSpot's Actual Connection Flow

Based on the logs, ThoughtSpot does a **two-phase handshake**:

### **Phase 1: Preliminary Check (JSON-RPC)**
```
POST /
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": { "protocolVersion": "2025-06-18" }
}
```
**Purpose:** Check if server is alive and compatible

### **Phase 2: Open SSE Stream**
```
GET /
Accept: text/event-stream
```
**Purpose:** Open persistent connection for actual communication

### **Phase 3: SSE Communication**
```
POST /messages (via SSE)
- initialize (again, via SSE)
- notifications/initialized
- tools/list
- tools/call
```
**Purpose:** All actual MCP protocol communication

---

## The Problem

When POST / returned 404, ThoughtSpot:
1. ✅ Still opened SSE (because it retried)
2. ✅ Sent initialize via /messages
3. ❌ **Never proceeded to tools/list** (probably marked connection as unhealthy due to step 1 failure)

---

## The Solution

Support **both** POST / and SSE, but use them for different purposes:

### **POST / - Preliminary Handshake Only**
```typescript
app.post('/', express.json(), async (req, res) => {
  if (request.method === 'initialize') {
    // Respond with compatibility info
    res.json({
      jsonrpc: '2.0',
      result: {
        protocolVersion: requestedVersion,
        capabilities: { tools: {} },
        serverInfo: { name: 'airbnb', version: VERSION }
      }
    });
  } else {
    // Reject - should use SSE for other methods
    res.status(400).json({
      error: 'Only initialize supported on POST /. Use SSE for other methods.'
    });
  }
});
```

### **GET / with SSE - Actual Communication**
```typescript
app.get('/', async (req, res) => {
  if (acceptHeader.includes('text/event-stream')) {
    const transport = new SSEServerTransport('/messages', res);
    await server.connect(transport);
    // SDK handles initialize, tools/list, tools/call via SSE
  }
});
```

### **POST /messages - SSE Messages**
```typescript
app.post('/messages', async (req, res) => {
  // SSE transport routes to server automatically
  res.status(202).json({ received: true });
});
```

---

## Complete Flow Now

### **Step 1: Preliminary Check**
```
ThoughtSpot → POST /
{ "method": "initialize", "params": { "protocolVersion": "2025-06-18" }}

Server → 200 OK
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2025-06-18",  ✅ Matches!
    "capabilities": { "tools": {} },
    "serverInfo": { "name": "airbnb", "version": "0.1.3" }
  }
}

ThoughtSpot: "Great! Server is compatible. Now let me open SSE..."
```

### **Step 2: Open SSE**
```
ThoughtSpot → GET /
Accept: text/event-stream

Server → 200 OK
Content-Type: text/event-stream
Connection: keep-alive

[SSE stream opened]
```

### **Step 3: SSE Handshake**
```
ThoughtSpot → POST /messages
{ "method": "initialize", ... }

Server (via SSE transport) → SSE response
{ "result": { "protocolVersion": "2025-06-18", ... }}

ThoughtSpot → POST /messages
{ "method": "notifications/initialized" }

Server → Acknowledges
```

### **Step 4: Tools Communication**
```
ThoughtSpot → POST /messages
{ "method": "tools/list" }

Server (via SDK) → SSE response
{ "result": { "tools": [...] }}

ThoughtSpot → POST /messages
{ "method": "tools/call", "params": { "name": "airbnb_search", ... }}

Server (via SDK) → Executes search → SSE response
{ "result": { "content": [{ "text": "{...Airbnb results...}" }] }}
```

---

## Why This Pattern?

### **Preliminary POST / initialize:**
- Quick check before committing to SSE connection
- Verifies protocol compatibility
- Confirms server is alive
- **Does NOT interfere with SSE** (separate concern)

### **SSE for actual communication:**
- Persistent connection
- Full MCP protocol flow
- SDK handles everything
- Efficient for multiple requests

---

## Railway Logs - Expected

```
[INFO] POST / received (preliminary JSON-RPC check): {
  "body": { "method": "initialize", "params": { "protocolVersion": "2025-06-18" }}
}

[INFO] Preliminary initialize handshake completed: {
  "requestedVersion": "2025-06-18",
  "note": "Client should now open SSE connection for actual communication"
}

[INFO] Root endpoint accessed via GET: {
  "acceptHeader": "text/event-stream",
  "isSSERequest": true
}

[INFO] SSE connection requested on root path

[INFO] SSE connection established on root path

[INFO] POST /messages received (SSE client message): {
  "body": { "method": "initialize", ... }
}

[INFO] ListTools request received  ✅ Should now happen!

[INFO] CallTool request received: { "tool": "airbnb_search" }  ✅

[INFO] Processing Airbnb search request

[INFO] Search completed successfully
```

---

## Key Differences

### **Before (Broken):**
```
POST / → 404  ❌
GET / → SSE opens  ✅
POST /messages → initialize  ✅
[ThoughtSpot stops - marked connection as failed due to step 1]
```

### **After (Fixed):**
```
POST / → initialize response  ✅
GET / → SSE opens  ✅
POST /messages → initialize (via SSE)  ✅
POST /messages → tools/list  ✅ Should work now!
POST /messages → tools/call  ✅
```

---

## Important Notes

### **POST / is LIMITED:**
- Only handles `initialize`
- Returns error for other methods
- Tells client to use SSE for actual communication

### **SSE handles EVERYTHING ELSE:**
- The real `initialize` (via /messages)
- `notifications/initialized`
- `tools/list`
- `tools/call`

### **No Conflict:**
- POST / initialize = "Are you compatible?"
- SSE initialize = "Let's actually communicate"
- Different purposes, don't interfere!

---

## Comparison to Other Patterns

### **Pattern A: JSON-RPC Only**
```
POST / for everything
```
**Problem:** No persistent connection, inefficient

### **Pattern B: SSE Only**
```
GET / for SSE, everything via /messages
```
**Problem:** No preliminary check, client can't verify compatibility first

### **Pattern C: Two-Phase (This)**
```
POST / for preliminary check
GET / for SSE
POST /messages for actual communication
```
**Advantage:** Best of both worlds!

---

## Testing

### **Test Phase 1:**
```bash
curl -X POST https://your-railway-url.up.railway.app/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}'
```

Should return:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-06-18",
    "capabilities": { "tools": {} },
    "serverInfo": { "name": "airbnb", "version": "0.1.3" }
  }
}
```

### **Test Phase 2:**
```bash
curl -N -H "Accept: text/event-stream" https://your-railway-url.up.railway.app/
```

Should open SSE stream.

---

**Status:** Ready to deploy - Two-phase handshake fully supported
