#!/bin/bash

# Script to push Airbnb MCP files directly to your GitHub fork
# This is much easier than copy-pasting through the web editor!

set -e  # Exit on any error

echo "🚀 Airbnb MCP Server - GitHub Push Script"
echo "=========================================="
echo ""

# Get GitHub username
read -p "Enter your GitHub username: " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo "❌ Error: GitHub username is required"
    exit 1
fi

echo ""
echo "📋 Summary:"
echo "   Fork URL: https://github.com/$GITHUB_USERNAME/mcp-server-airbnb"
echo "   Local directory: $(pwd)"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo ""
echo "📁 Creating temporary workspace..."

# Clone the forked repository
echo "📥 Cloning your fork..."
git clone "https://github.com/$GITHUB_USERNAME/mcp-server-airbnb.git" "$TEMP_DIR"

# Copy modified files
echo "📝 Copying modified files..."
cp package.json "$TEMP_DIR/"
cp Dockerfile "$TEMP_DIR/"
cp server.ts "$TEMP_DIR/"
cp util.ts "$TEMP_DIR/"
cp types.d.ts "$TEMP_DIR/"
cp tsconfig.json "$TEMP_DIR/"

# Change to repo directory
cd "$TEMP_DIR"

# Configure git
echo "⚙️  Configuring git..."
git config user.name "Railway Deployment"
git config user.email "deploy@local"

# Add files
echo "➕ Adding files to git..."
git add package.json Dockerfile server.ts util.ts types.d.ts tsconfig.json

# Check if there are changes
if git diff --cached --quiet; then
    echo "ℹ️  No changes detected - files might already be up to date"
    cd -
    rm -rf "$TEMP_DIR"
    exit 0
fi

# Show what will be committed
echo ""
echo "📦 Changes to commit:"
git status --short

# Commit
echo ""
echo "💾 Creating commit..."
git commit -m "Add HTTP/SSE transport for Railway deployment

- Updated package.json with Express dependency
- Modified Dockerfile to run HTTP server on port 8080
- Added server.ts with SSE transport wrapper
- Included required utility files (util.ts, types.d.ts, tsconfig.json)

This enables the MCP server to be accessed via public URL endpoint."

# Push
echo ""
echo "🚢 Pushing to GitHub..."
echo "   You may be prompted for your GitHub password or personal access token"
echo ""

git push origin main

# Cleanup
cd -
rm -rf "$TEMP_DIR"

echo ""
echo "✅ SUCCESS! Files pushed to GitHub"
echo ""
echo "🎯 Next steps:"
echo "   1. Go to https://github.com/$GITHUB_USERNAME/mcp-server-airbnb"
echo "   2. Verify the files are updated"
echo "   3. Go to Railway and deploy/redeploy your project"
echo "   4. Railway will automatically detect the changes and rebuild"
echo ""
