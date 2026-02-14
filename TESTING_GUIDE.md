# Testing Your MCP Server

## Step 1: Get Your Railway Domain

You're at: https://railway.com/project/b27c797f-a5be-40f8-913b-ca88601262a0

**Find your public URL:**
1. In the Railway dashboard, look for the **"Domains"** section in Settings
2. Or check the deployment page - the URL should be visible
3. It will look like: `https://web-production-XXXX.up.railway.app` or similar

**Common places to find it:**
- Top of the Railway project page
- Settings → Networking → Domains
- Deployments → Click latest → Look for the public URL

---

## Step 2: Run the Test Script

Once you have your Railway URL, open Terminal:

```bash
cd "/Users/luke.slater/Documents/Agentic Workflows/Airbnb-MCP-Railway-Deployment"

./test_mcp_server.sh https://YOUR-RAILWAY-URL.up.railway.app
```

**Example:**
```bash
./test_mcp_server.sh https://web-production-abc123.up.railway.app
```

---

## Step 3: What You'll See

The script will run 3 tests:

### ✅ Test 1: Health Check
```json
{
  "status": "healthy",
  "version": "0.1.3",
  "timestamp": "...",
  "activeConnections": 0
}
```

### ✅ Test 2: JSON-RPC tools/list
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

### ✅ Test 3: JSON-RPC initialize
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo": { "name": "airbnb", "version": "0.1.3" }
  }
}
```

---

## Alternative: Manual Test with curl

If you prefer, just run this command (replace YOUR-URL):

```bash
curl -X POST https://YOUR-RAILWAY-URL.up.railway.app/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Should return:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [ ... ]
  }
}
```

---

## If You Don't Have jq Installed

The test script uses `jq` to format JSON output. If you get an error about `jq`:

**Install it:**
```bash
brew install jq
```

Or just use the manual curl command above - it works without jq.

---

## After Testing Succeeds

**Your URL for ThoughtSpot:**
```
https://YOUR-RAILWAY-URL.up.railway.app/
```

**Important Notes:**
- Use the **root path `/`** (not `/sse`)
- ThoughtSpot will POST JSON-RPC requests to this URL
- The server will respond with tool lists and search results

---

## Troubleshooting

### Can't Find Railway URL?
1. Click on your service in Railway
2. Go to "Settings" tab
3. Scroll to "Networking" section
4. Click "Generate Domain" if none exists
5. Copy the generated URL

### Test Fails?
Check Railway logs:
1. Railway dashboard → Deployments
2. Click latest deployment
3. View Logs
4. Look for startup messages

### 404 Error?
Make sure you:
- Deployed the latest `server.ts` with JSON-RPC support
- Used the correct Railway URL
- Are POSTing to `/` (root path)

---

## Quick Reference

**Files Location:**
```
/Users/luke.slater/Documents/Agentic Workflows/Airbnb-MCP-Railway-Deployment/
```

**Test Script:**
```bash
./test_mcp_server.sh https://YOUR-URL.up.railway.app
```

**Railway Dashboard:**
https://railway.com/project/b27c797f-a5be-40f8-913b-ca88601262a0
