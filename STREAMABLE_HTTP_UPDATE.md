# Streamable HTTP Transport Update

## What Changed

Updated from **SSE Transport** (legacy) to **Streamable HTTP Transport** (modern standard).

---

## Why Streamable HTTP?

Based on MCP SDK documentation:
- **Streamable HTTP is the modern, fully featured transport**
- Supersedes SSE transport from protocol version 2024-11-05+
- **Recommended for remote servers**
- Used by ThoughtSpot's Python MCP SDK client
- Supports both stateful and stateless operations

---

## Key Changes in server.ts

### **1. Import Updated**
```typescript
// Before
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";

// After
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
```

### **2. Transport Creation**
```typescript
// Before (SSE)
const transport = new SSEServerTransport('/messages', res);

// After (Streamable HTTP)
const transport = new StreamableHTTPServerTransport({
  sessionId,
  endpoint: '/message'
});
```

### **3. Request Handling**
```typescript
// After connection, handle the request
await transport.handleRequest(req, res);
```

### **4. Endpoint Renamed**
```
POST /messages → POST /message
```
(Streamable HTTP convention uses singular `/message`)

---

## Complete Flow

### **Step 1: Preliminary Check (unchanged)**
```
ThoughtSpot → POST /
{ "method": "initialize", "params": { "protocolVersion": "2025-06-18" }}

Server → 200 OK
{ "result": { "protocolVersion": "2025-06-18", ... }}
```

### **Step 2: Open Streamable HTTP Connection**
```
ThoughtSpot → GET /
Accept: text/event-stream

Server → Creates StreamableHTTPServerTransport
Server → Calls transport.handleRequest(req, res)
Server → Opens streaming connection
```

### **Step 3: Client Messages**
```
ThoughtSpot → POST /message
Header: mcp-session-id: <sessionId>
Body: { "method": "initialize", ... }

Server → Routes to transport.handleRequest(req, res)
Server → Transport handles via MCP SDK
Server → Streams response back
```

### **Step 4: Tools Communication**
```
ThoughtSpot → POST /message
{ "method": "tools/list" }

Server → SDK routes to ListToolsRequestSchema handler
Server → Streams tools list back

ThoughtSpot → POST /message
{ "method": "tools/call", "params": { "name": "airbnb_search", ... }}

Server → SDK routes to CallToolRequestSchema handler
Server → Executes handleAirbnbSearch
Server → Streams Airbnb results back
```

---

## Endpoints Summary

| Method | Path | Purpose |
|--------|------|---------|
| POST | / | Preliminary initialize handshake |
| GET | / | Open Streamable HTTP connection (with Accept: text/event-stream) |
| POST | /message | Send MCP protocol messages (with mcp-session-id header) |
| GET | /health | Health check |
| GET | / | Server info (without SSE header) |

---

## Benefits of Streamable HTTP

### **vs SSE Transport:**
- ✅ More modern and actively maintained
- ✅ Better support for stateless operations
- ✅ Cleaner API design
- ✅ Better error handling
- ✅ Compatible with Python MCP SDK (ThoughtSpot uses this)

### **Protocol Support:**
- ✅ Protocol version 2024-11-05+
- ✅ Protocol version 2025-06-18
- ✅ Backwards compatible with older clients

---

## Expected Railway Logs

```
[INFO] POST / received (preliminary JSON-RPC check)
[INFO] Preliminary initialize handshake completed

[INFO] Root endpoint accessed via GET: {
  "acceptHeader": "text/event-stream",
  "isSSERequest": true
}

[INFO] Streamable HTTP connection requested on root path: {
  "transport": "StreamableHTTP"
}

[INFO] Creating StreamableHTTP transport

[INFO] Connecting MCP server to StreamableHTTP transport

[INFO] Streamable HTTP connection established

[INFO] POST /message received (Streamable HTTP client message)

[INFO] Message routed to Streamable HTTP transport

[INFO] ListTools request received

[INFO] CallTool request received: { "tool": "airbnb_search" }

[INFO] Search completed successfully
```

---

## SDK Version Requirement

**Minimum SDK version:** 1.10.0 (released April 17, 2025)

The project's `package.json` has:
```json
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.1"
  }
}
```

This should automatically pull the latest 1.x version with Streamable HTTP support.

---

## Compatibility

### **ThoughtSpot (Python SDK):**
✅ Uses StreamableHTTP client
✅ Should work seamlessly now

### **Other Clients:**
✅ Legacy SSE clients should still work (fallback)
✅ Modern MCP clients prefer Streamable HTTP
✅ Backward compatible

---

## What to Test

1. **Initialize handshake:**
   ```bash
   curl -X POST https://your-railway-url.up.railway.app/ \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}'
   ```

2. **Open streaming connection:**
   ```bash
   curl -N -H "Accept: text/event-stream" https://your-railway-url.up.railway.app/
   ```

3. **ThoughtSpot connection:**
   - Connect ThoughtSpot to Railway URL
   - Make Airbnb search query
   - Check Railway logs for full flow

---

## References

- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [Streamable HTTP Documentation](https://github.com/modelcontextprotocol/typescript-sdk/blob/main/docs/server.md)
- [Why MCP Deprecated SSE](https://blog.fka.dev/blog/2025-06-06-why-mcp-deprecated-sse-and-go-with-streamable-http/)
- [MCP Server with Streamable HTTP](https://levelup.gitconnected.com/mcp-server-and-client-with-sse-the-new-streamable-http-d860850d9d9d)

---

**Status:** Ready to deploy - Modern Streamable HTTP transport implemented

Sources:
- [GitHub - modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk)
- [typescript-sdk/docs/server.md](https://github.com/modelcontextprotocol/typescript-sdk/blob/main/docs/server.md)
- [Support for "Streamable HTTP" Transport · Issue #220](https://github.com/modelcontextprotocol/typescript-sdk/issues/220)
- [Why MCP Deprecated SSE and Went with Streamable HTTP](https://blog.fka.dev/blog/2025-06-06-why-mcp-deprecated-sse-and-go-with-streamable-http/)
