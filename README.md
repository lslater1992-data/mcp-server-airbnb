# Airbnb MCP Server - Railway Deployment Project

This project contains all the modified files needed to deploy the Airbnb MCP Server to Railway with HTTP/SSE transport.

## Project Purpose

Deploy the [Airbnb MCP Server](https://github.com/openbnb-org/mcp-server-airbnb) to Railway so it can be accessed via a public URL endpoint instead of just local desktop use.

## What's Inside

### Modified Files (to upload to GitHub):
- **`package.json`** - Adds Express and HTTP/SSE dependencies
- **`Dockerfile`** - Configures Railway deployment with port 8080
- **`server.ts`** - HTTP/SSE transport wrapper (NEW FILE)

### Documentation:
- **`DEPLOYMENT_INSTRUCTIONS.md`** - Step-by-step deployment guide
- **`CHECKLIST.md`** - Progress tracking checklist
- **`FILE_SUMMARY.md`** - Quick reference of what each file does

### Reference Files:
- **`*.original`** - Original files from the repo (for comparison)

## Getting Started

1. **Read:** [DEPLOYMENT_INSTRUCTIONS.md](DEPLOYMENT_INSTRUCTIONS.md)
2. **Track progress:** Use [CHECKLIST.md](CHECKLIST.md)
3. **Follow the 7 steps** to deploy

## Expected Outcome

A live URL endpoint: `https://your-project.up.railway.app/sse`

This URL can be used to connect the MCP server to external platforms.

## Time Required

Approximately 15-20 minutes (mostly waiting for Railway to build and deploy)

## Cost

Free (Railway provides $5/month free tier credit)

---

**Status:** Ready to deploy
**Last Updated:** 2026-02-13
