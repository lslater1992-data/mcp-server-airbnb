# Quick Deploy - Fixed server.ts

## What's Been Fixed
✅ server.ts now has comprehensive logging
✅ SSE transport properly handles tool responses
✅ Session management prevents connection interference
✅ You'll be able to see exactly what's happening in Railway logs

## Deploy to Railway (3 Options)

### **Option 1: Use the Push Script (Easiest)**

```bash
cd "/Users/luke.slater/Documents/Agentic Workflows/Airbnb-MCP-Railway-Deployment"
./push-to-github.sh
```

Enter your GitHub username and token when prompted.

---

### **Option 2: Manual Git Commands**

```bash
cd "/Users/luke.slater/Documents/Agentic Workflows/Airbnb-MCP-Railway-Deployment"

# Clone your fork
git clone https://github.com/YOUR-USERNAME/mcp-server-airbnb.git temp-clone
cd temp-clone

# Copy the fixed file
cp ../server.ts ./server.ts

# Commit and push
git add server.ts
git commit -m "Fix SSE transport and add comprehensive logging"
git push origin main

# Clean up
cd ..
rm -rf temp-clone
```

---

### **Option 3: GitHub Web Editor (Copy-Paste)**

1. Go to your fork: `https://github.com/YOUR-USERNAME/mcp-server-airbnb`
2. Click on `server.ts`
3. Click the pencil icon (Edit)
4. Open the local file at:
   `/Users/luke.slater/Documents/Agentic Workflows/Airbnb-MCP-Railway-Deployment/server.ts`
5. Copy ALL content
6. Paste into GitHub editor (replace everything)
7. Commit: "Fix SSE transport and add comprehensive logging"

---

## After Deployment

### Railway Will:
1. Detect the change automatically
2. Start a new build (~2-3 minutes)
3. Deploy the updated server
4. You'll see "Deployed" with green checkmark

### Check the Logs:
1. Go to Railway dashboard
2. Click your project
3. Click "Deployments"
4. Click the latest deployment
5. Click "View Logs"

### You'll Now See:
```
[INFO] Starting Airbnb MCP Server
[INFO] Successfully fetched robots.txt
[INFO] Airbnb MCP Server running successfully
```

When ThoughtSpot connects:
```
[INFO] New SSE connection request: { "sessionId": "abc123", ... }
[INFO] SSE connection established successfully
```

When a tool is called:
```
[INFO] CallTool request received: { "tool": "airbnb_search", "arguments": {...} }
[INFO] Processing Airbnb search request
[INFO] Built search URL
[INFO] Fetching Airbnb search page
[INFO] Search completed successfully: { "resultCount": 20 }
[INFO] Tool call completed successfully: { "duration": "3421ms", "success": true }
```

---

## Test It Works

### Step 1: Health Check
Visit: `https://your-railway-url.up.railway.app/health`

Should return:
```json
{
  "status": "healthy",
  "version": "0.1.3",
  "timestamp": "2026-02-13T...",
  "activeConnections": 0
}
```

### Step 2: Check Logs
You should see in Railway:
```
[INFO] Health check requested
```

### Step 3: Test from ThoughtSpot
Make a query, then check Railway logs - you'll see the full request flow!

---

## If the Response is Still `undefined`

Check Railway logs for:

1. **Connection Issues:**
   ```
   [ERROR] Failed to establish SSE connection
   ```

2. **Tool Errors:**
   ```
   [ERROR] Tool call failed: { "error": "..." }
   ```

3. **Parsing Errors:**
   ```
   [ERROR] Failed to parse search results
   ```

With the new logging, you'll know exactly where it's failing!

---

## Files Updated
- ✅ `server.ts` - Completely rewritten with logging and fixes

## Files That Should Already Be Deployed
- ✅ `util.ts`
- ✅ `types.d.ts`
- ✅ `tsconfig.json`
- ✅ `package.json`
- ✅ `Dockerfile`

Only `server.ts` needs to be updated now!
