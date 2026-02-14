# Protocol Version Fix - 2025-06-18 Support

## Problem Identified
ThoughtSpot sends:
```json
{
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18"
  }
}
```

But the server was responding with:
```json
{
  "result": {
    "protocolVersion": "2024-11-05"  // ❌ Mismatch!
  }
}
```

**Result:** ThoughtSpot accepted the response but then sent a GET to / and stopped. Never proceeded to `tools/list` or `tools/call`.

---

## Solution Applied

### 1. **Echo Back Client's Protocol Version**

The server now responds with whatever protocol version the client requests:

```typescript
const requestedVersion = request.params?.protocolVersion || '2024-11-05';

result = {
  protocolVersion: requestedVersion,  // ✅ Now matches client's request
  capabilities: { tools: {} },
  serverInfo: { name: 'airbnb', version: VERSION }
};
```

### 2. **Added notifications/initialized Handler**

Some MCP protocol versions expect a `notifications/initialized` message after `initialize`:

```typescript
case 'notifications/initialized':
  log('info', 'Handling notifications/initialized (client confirms initialization)');
  return res.status(200).json({
    jsonrpc: '2.0',
    result: null,
    id: request.id
  });
```

### 3. **Enhanced GET / Logging**

When ThoughtSpot sends GET to /, we now log:
- User agent
- Query parameters
- Accept headers
- Note about potential SSE upgrade expectation

The GET / response now also includes:
```json
{
  "protocolVersion": "2025-06-18",
  "capabilities": { "tools": {} }
}
```

---

## MCP Protocol Version Differences

### **2024-11-05 (Original)**
Handshake flow:
1. Client → `initialize` request
2. Server → `initialize` response
3. Client → `tools/list` or `tools/call`

### **2025-06-18 (Newer)**
Handshake flow may include:
1. Client → `initialize` request
2. Server → `initialize` response
3. Client → `notifications/initialized` (confirms ready)
4. Client → `tools/list` or `tools/call`

Or possibly:
1. Client → GET / (check server capabilities)
2. Client → POST / `initialize` request
3. Server → `initialize` response
4. Client → `tools/list` or `tools/call`

---

## Expected Railway Logs Now

### When ThoughtSpot Connects:

```
[INFO] Incoming HTTP request: { "method": "POST", "path": "/" }

[INFO] JSON-RPC request received on root path: {
  "body": {
    "method": "initialize",
    "params": { "protocolVersion": "2025-06-18" }
  }
}

[INFO] Processing JSON-RPC method: { "method": "initialize" }

[INFO] Handling initialize request: {
  "params": { "protocolVersion": "2025-06-18" }
}

[INFO] Initialize response prepared: {
  "requestedVersion": "2025-06-18",  // ✅ Now matches!
  "result": { "protocolVersion": "2025-06-18", ... }
}

[INFO] Sending JSON-RPC response
```

### If ThoughtSpot Sends GET:

```
[INFO] Root endpoint accessed via GET: {
  "userAgent": "python-httpx/...",
  "query": {},
  "headers": { ... },
  "note": "Client may be checking server availability or expecting SSE upgrade"
}
```

### If ThoughtSpot Sends notifications/initialized:

```
[INFO] JSON-RPC request received: {
  "method": "notifications/initialized"
}

[INFO] Handling notifications/initialized (client confirms initialization)
```

### Then tools/list Should Follow:

```
[INFO] JSON-RPC request received: {
  "method": "tools/list"
}

[INFO] Handling tools/list request

[INFO] Tools list response prepared: { "toolCount": 2 }
```

---

## What Changed in server.ts

### ✅ Initialize Handler
- Now echoes back client's requested protocol version
- Logs the requested version for debugging

### ✅ New notifications/initialized Handler
- Handles the initialization confirmation message
- Returns null result (standard for notifications)

### ✅ Enhanced GET / Handler
- Logs more details about why client might be doing GET
- Returns protocol version and capabilities in response

---

## Testing After Deploy

### Expected Flow:
1. ThoughtSpot → POST / `initialize` with `"protocolVersion": "2025-06-18"`
2. Server → Response with `"protocolVersion": "2025-06-18"` ✅
3. ThoughtSpot → (optional) GET / or `notifications/initialized`
4. ThoughtSpot → POST / `tools/list` ✅ (should now happen!)
5. ThoughtSpot → POST / `tools/call` with Airbnb search ✅

---

## What to Watch in Railway Logs

**Before (Problem):**
```
[INFO] Initialize response: "2024-11-05"
[INFO] Root endpoint accessed via GET
# ❌ Then stops - no tools/list
```

**After (Fixed):**
```
[INFO] Initialize response: "2025-06-18"  // ✅ Matches request
[INFO] Root endpoint accessed via GET (if sent)
[INFO] Handling tools/list request          // ✅ Should appear now!
[INFO] Handling tools/call request          // ✅ Should appear now!
```

---

## Deploy This Update

```bash
cd "/Users/luke.slater/Documents/Agentic Workflows/Airbnb-MCP-Railway-Deployment"
./push-to-github.sh
```

Or manually:
1. Go to your GitHub fork
2. Edit `server.ts`
3. Copy the updated content
4. Commit: "Fix protocol version mismatch and add notifications/initialized support"

Railway will auto-deploy in ~3 minutes.

---

## Additional Notes

### Why Protocol Version Matters
- Clients check protocol version for compatibility
- If server returns incompatible version, client may abort
- Echoing back the requested version ensures compatibility

### Why GET / Matters
- Some clients check server availability with GET before POSTing
- May be checking for SSE upgrade headers
- Now returns protocol info so client knows we support JSON-RPC

### Why notifications/initialized Matters
- Newer MCP protocol may require explicit confirmation
- Client tells server "I received your initialize response and I'm ready"
- Server acknowledges and waits for tool calls

---

**Status:** Ready to deploy - protocol version now matches client request
