# Airbnb MCP Server - HTTP/SSE Transport for Railway
FROM node:lts-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install --ignore-scripts

# Copy rest of the source code
COPY . .

# Build the project explicitly
RUN npm run build

# Expose port for HTTP/SSE server
EXPOSE 8080

# Set environment variable for PORT (Railway will override this)
ENV PORT=8080

# Run the HTTP server instead of stdio
CMD [ "node", "dist/server.js" ]
