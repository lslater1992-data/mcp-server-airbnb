# Push Files Directly to GitHub (Easy Method!)

## Why This is Better

Instead of copy-pasting files through the web editor (which can cause corruption), this script:
- ✅ Pushes files directly from your computer to GitHub
- ✅ Avoids copy-paste errors and character encoding issues
- ✅ Commits all 6 files at once (not one-by-one)
- ✅ Takes 30 seconds instead of 10 minutes

---

## Prerequisites

1. **GitHub Account** - Already have this ✓
2. **Forked Repository** - Fork https://github.com/openbnb-org/mcp-server-airbnb
3. **GitHub Authentication** - One of these:
   - Personal Access Token (recommended)
   - GitHub password (if you don't have 2FA)

---

## How to Get a GitHub Personal Access Token (PAT)

You'll need this to push from the command line:

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Name it: `Railway MCP Deployment`
4. Set expiration: **30 days** (or longer)
5. Check these permissions:
   - ✅ `repo` (Full control of private repositories)
6. Click **"Generate token"** at the bottom
7. **COPY THE TOKEN** (you'll only see it once!)
8. Save it somewhere safe (you'll paste it when the script asks for password)

---

## Running the Script

### Option 1: Double-click (Easiest)

1. In Finder, navigate to:
   ```
   /Users/luke.slater/Documents/Agentic Workflows/Airbnb-MCP-Railway-Deployment
   ```
2. Double-click `push-to-github.sh`
3. If it opens in TextEdit, right-click → **Open With** → **Terminal**
4. Follow the prompts

### Option 2: From Terminal

1. Open Terminal (Cmd + Space, type "Terminal")
2. Run:
   ```bash
   cd "/Users/luke.slater/Documents/Agentic Workflows/Airbnb-MCP-Railway-Deployment"
   ./push-to-github.sh
   ```
3. Follow the prompts

---

## What the Script Will Do

1. **Ask for your GitHub username** (e.g., `yourname`)
2. **Clone your fork** temporarily
3. **Copy all 6 modified files**:
   - package.json
   - Dockerfile
   - server.ts
   - util.ts
   - types.d.ts
   - tsconfig.json
4. **Create a commit** with a descriptive message
5. **Push to your fork**
6. **Clean up** temporary files

---

## During the Push

When you see: `Username for 'https://github.com':`
- Type your GitHub username

When you see: `Password for 'https://yourname@github.com':`
- **Paste your Personal Access Token** (NOT your GitHub password)
- The token won't show as you paste (that's normal)
- Press Enter

---

## After Success

Once you see: **✅ SUCCESS! Files pushed to GitHub**

1. Go to your fork: `https://github.com/YOUR-USERNAME/mcp-server-airbnb`
2. You should see 6 updated files
3. Go to Railway dashboard
4. Click your project
5. Railway will automatically detect changes and rebuild
6. Wait 2-5 minutes for build to complete
7. Your endpoint will be ready: `https://your-app.up.railway.app/sse`

---

## Troubleshooting

### "Permission denied"
Run: `chmod +x push-to-github.sh` then try again

### "Authentication failed"
- Make sure you're using a Personal Access Token (not password)
- Check that the token has `repo` permissions
- Generate a new token if needed

### "Repository not found"
- Verify you've forked the repo to your GitHub account
- Check your username is spelled correctly

### "No changes detected"
The files might already be up-to-date in your fork. Check GitHub to confirm.

---

## What Changed from Before

**Added missing files:**
- `util.ts` - Utility functions (was missing, caused build errors!)
- `types.d.ts` - TypeScript types
- `tsconfig.json` - TypeScript configuration

These were causing the "Invalid character" errors because server.ts was trying to import from files that didn't exist.

---

## Alternative: Manual Upload (If Script Doesn't Work)

If the script fails, you can upload files via GitHub web interface:

1. Go to your fork on GitHub
2. For EACH file (package.json, Dockerfile, server.ts, util.ts, types.d.ts, tsconfig.json):
   - Click the filename
   - Click pencil icon (edit)
   - Delete all content
   - Open the local file from this folder
   - Copy contents (Cmd+A, Cmd+C)
   - Paste into GitHub (Cmd+V)
   - Commit changes
3. Make sure to add `server.ts`, `util.ts`, `types.d.ts` as NEW files (Add file → Create new file)

But the script is **much** faster and more reliable!

---

## Files Ready to Push

All 6 files are in:
```
/Users/luke.slater/Documents/Agentic Workflows/Airbnb-MCP-Railway-Deployment/
```

✅ package.json
✅ Dockerfile
✅ server.ts
✅ util.ts (NEW - was missing!)
✅ types.d.ts (NEW - was missing!)
✅ tsconfig.json (NEW - was missing!)

---

**Ready to go!** Run the script and you'll have everything pushed in 30 seconds. 🚀
