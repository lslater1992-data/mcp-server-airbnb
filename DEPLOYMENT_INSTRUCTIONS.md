# Deploy Airbnb MCP Server to Railway - Complete Guide

## What You'll Get
A live URL endpoint like: `https://your-project.up.railway.app/sse`

This URL can be used to connect the MCP server to external platforms that support Server-Sent Events (SSE) transport.

---

## Step-by-Step Instructions

### **Step 1: Fork the Repository on GitHub**

1. Go to: https://github.com/openbnb-org/mcp-server-airbnb
2. Click the **"Fork"** button in the top-right corner
3. This creates your own copy of the repository under your GitHub account
4. Once forked, you'll be redirected to your copy: `https://github.com/YOUR-USERNAME/mcp-server-airbnb`

---

### **Step 2: Upload the Modified Files**

You need to replace 3 files and add 1 new file in your forked repository. Here's how to do it through GitHub's web interface (no coding required):

#### **A. Replace `package.json`**

1. In your forked repo, click on the file `package.json`
2. Click the **pencil icon** (Edit this file) in the top-right
3. **Delete all the existing content**
4. Open the file: `package.json` from the folder I created for you
5. Copy ALL the content from my file
6. Paste it into the GitHub editor
7. Scroll down and click **"Commit changes"**
8. Click **"Commit changes"** again in the popup

#### **B. Replace `Dockerfile`**

1. Go back to the main page of your forked repo
2. Click on the file `Dockerfile`
3. Click the **pencil icon** (Edit this file)
4. **Delete all the existing content**
5. Open the file: `Dockerfile` from the folder I created for you
6. Copy ALL the content from my file
7. Paste it into the GitHub editor
8. Scroll down and click **"Commit changes"**
9. Click **"Commit changes"** again

#### **C. Create New File `server.ts`**

1. Go back to the main page of your forked repo
2. Click **"Add file"** → **"Create new file"**
3. In the filename box, type: `server.ts`
4. Open the file: `server.ts` from the folder I created for you
5. Copy ALL the content from my file
6. Paste it into the GitHub editor
7. Scroll down and click **"Commit new file"**

---

### **Step 3: Create a Railway Account**

1. Go to: https://railway.app
2. Click **"Start a New Project"** or **"Sign up"**
3. Sign up with your **GitHub account** (this is the easiest method)
4. Authorize Railway to access your GitHub account

---

### **Step 4: Deploy to Railway**

1. Once logged into Railway, click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Find and select your forked repository: `mcp-server-airbnb`
4. Railway will automatically detect the Dockerfile
5. Click **"Deploy Now"** or **"Deploy"**

Railway will now:
- Read your Dockerfile
- Install all dependencies
- Build the project
- Start the server
- Assign you a public URL

This process takes about 2-5 minutes.

---

### **Step 5: Get Your URL**

1. Once deployment is complete (you'll see "Success" or a green checkmark), click on your project
2. Click on the **"Settings"** tab
3. Scroll down to **"Domains"** or **"Networking"**
4. Click **"Generate Domain"** if one isn't already created
5. You'll see a URL like: `https://mcp-server-airbnb-production-XXXX.up.railway.app`

**Your SSE endpoint is:** `https://your-railway-url.up.railway.app/sse`

---

### **Step 6: Test Your Endpoint**

1. Copy your Railway URL
2. Add `/health` to the end: `https://your-url.up.railway.app/health`
3. Paste this in your browser
4. You should see a JSON response like:
   ```json
   {
     "status": "healthy",
     "version": "0.1.3",
     "timestamp": "2026-02-13T..."
   }
   ```

If you see this, your server is working! ✅

---

### **Step 7: Use Your MCP Server**

Your final endpoint to paste into external tools is:

```
https://your-railway-url.up.railway.app/sse
```

**Available endpoints:**
- `/sse` - Main Server-Sent Events endpoint (this is what you need)
- `/health` - Health check endpoint
- `/` - Info page

---

## Troubleshooting

### **Build Failed**
- Check Railway logs (click "Deployments" → Click on the failed deployment → View logs)
- Most common issue: Missing files. Make sure you uploaded all 3 modified files

### **Server Not Responding**
- Wait 1-2 minutes after deployment completes
- Check that PORT environment variable is set (Railway does this automatically)
- View runtime logs in Railway dashboard

### **404 Error**
- Make sure you're accessing `/sse` endpoint, not just the root URL
- Example: `https://your-app.up.railway.app/sse` ✅
- Not: `https://your-app.up.railway.app` ❌ (this just shows info)

---

## Cost Information

**Railway Free Tier:**
- $5 free credit per month
- Sufficient for testing and light usage
- Unused credits don't roll over
- Upgrade anytime if you need more resources

---

## Environment Variables (Optional)

If you want to ignore robots.txt restrictions:

1. In Railway dashboard, click your project
2. Go to **"Variables"** tab
3. Click **"New Variable"**
4. Name: `IGNORE_ROBOTS_TXT`
5. Value: `true`
6. Click **"Add"**
7. Railway will automatically restart your server

---

## Files I Created for You

All modified files are in this folder:
- `package.json` - Updated dependencies
- `Dockerfile` - Updated to run HTTP server
- `server.ts` - New HTTP/SSE wrapper
- `DEPLOYMENT_INSTRUCTIONS.md` - This guide

---

## What Changed from the Original?

The original MCP server was designed for desktop use (stdio transport). I added:

1. **HTTP/SSE Transport** - Allows web access via URL
2. **Express Server** - Handles HTTP requests
3. **Port Configuration** - Exposes port 8080 for Railway
4. **Health Check Endpoint** - So you can verify it's running

All original functionality remains intact!

---

## Need Help?

If you get stuck at any step, let me know:
1. Which step you're on
2. What error message you see (if any)
3. Screenshot of the issue (if possible)

I'll walk you through it!
