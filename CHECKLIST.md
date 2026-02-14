# Deployment Checklist ✓

Print this out or keep it open while you work through the deployment!

---

## Pre-Deployment

- [ ] I have a GitHub account
- [ ] I can access https://github.com/openbnb-org/mcp-server-airbnb
- [ ] I have located the deployment files on my computer at:
      `/Users/luke.slater/Documents/Agentic Workflows/Review Scraper/.tmp/mcp-railway-deployment/`

---

## GitHub Setup

- [ ] **Step 1:** Forked the repository
      ✓ My fork URL: `https://github.com/___________/mcp-server-airbnb`

- [ ] **Step 2A:** Replaced `package.json` with the new version
      ✓ Committed changes

- [ ] **Step 2B:** Replaced `Dockerfile` with the new version
      ✓ Committed changes

- [ ] **Step 2C:** Created new file `server.ts`
      ✓ Committed new file

---

## Railway Setup

- [ ] **Step 3:** Created Railway account
      ✓ Signed up at https://railway.app
      ✓ Connected GitHub account

- [ ] **Step 4:** Deployed to Railway
      ✓ Created new project
      ✓ Selected my forked repo
      ✓ Railway detected Dockerfile
      ✓ Deployment started

- [ ] **Deployment Status:**
      ✓ Build completed (2-5 minutes)
      ✓ Deployment successful (green checkmark)

---

## Get Your URL

- [ ] **Step 5:** Generated Railway domain
      ✓ My Railway URL: `https://_________________________________.up.railway.app`

- [ ] **Step 6:** Tested the health endpoint
      ✓ Visited: `https://my-url.up.railway.app/health`
      ✓ Saw JSON response with "status": "healthy"

---

## Final URL

**My SSE Endpoint (copy this to use in external tools):**

```
https://_________________________________________________.up.railway.app/sse
```

---

## Post-Deployment (Optional)

- [ ] Set `IGNORE_ROBOTS_TXT=true` environment variable (if needed)
- [ ] Bookmarked my Railway dashboard
- [ ] Bookmarked my GitHub fork
- [ ] Tested the endpoint in my external tool

---

## Troubleshooting Notes

If something went wrong, write notes here:

**Issue:**
_______________________________________________________________________

**Step where it happened:**
_______________________________________________________________________

**Error message (if any):**
_______________________________________________________________________

---

## Success! 🎉

Once all boxes are checked, you're done! Your MCP server is live and accessible via URL.

**Time to complete:** Approximately 15-20 minutes (mostly waiting for Railway to build)
