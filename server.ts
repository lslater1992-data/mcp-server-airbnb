#!/usr/bin/env node

process.on('uncaughtException', (err) => {
  console.error('UNCAUGHT EXCEPTION:', err);
});
process.on('unhandledRejection', (err) => {
  console.error('UNHANDLED REJECTION:', err);
});

import express from 'express';
import { randomUUID } from 'crypto';
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
  McpError,
  ErrorCode,
} from "@modelcontextprotocol/sdk/types.js";
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js";
import fetch from "node-fetch";
import * as cheerio from "cheerio";
import { cleanObject, flattenArraysInObject, pickBySchema } from "./util.js";
import robotsParser from "robots-parser";
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

function getVersion(): string {
  try {
    const packageJson = JSON.parse(readFileSync(join(__dirname, '..', 'package.json'), 'utf-8'));
    return packageJson.version || '0.1.0';
  } catch {
    return '0.1.0';
  }
}

const VERSION = getVersion();
const IGNORE_ROBOTS_TXT = process.env.IGNORE_ROBOTS_TXT === 'true';

function log(level: 'info' | 'warn' | 'error', message: string, data?: any) {
  const timestamp = new Date().toISOString();
  const logData = data ? ` ${JSON.stringify(data, null, 2)}` : '';
  console.log(`[${timestamp}] [${level.toUpperCase()}] ${message}${logData}`);
}

let robotsTxtContent: string | null = null;

async function fetchRobotsTxt() {
  try {
    const response = await fetch('https://www.airbnb.com/robots.txt');
    robotsTxtContent = await response.text();
    log('info', 'Successfully fetched robots.txt');
  } catch (error) {
    log('error', 'Failed to fetch robots.txt', {
      error: error instanceof Error ? error.message : String(error)
    });
  }
}

function isAllowedByRobots(path: string): boolean {
  if (IGNORE_ROBOTS_TXT || !robotsTxtContent) return true;
  const robots = robotsParser('https://www.airbnb.com/robots.txt', robotsTxtContent);
  return robots.isAllowed(path, 'ClaudeBot') ?? true;
}

const AIRBNB_TOOLS: Tool[] = [
  {
    name: "airbnb_search",
    description: "Search Airbnb listings by location, dates, and filters",
    inputSchema: {
      type: "object",
      properties: {
        location: { type: "string", description: "City, address, or region to search" },
        checkin: { type: "string", description: "Check-in date (YYYY-MM-DD)" },
        checkout: { type: "string", description: "Check-out date (YYYY-MM-DD)" },
        adults: { type: "number", description: "Number of adults" },
        children: { type: "number", description: "Number of children" },
        infants: { type: "number", description: "Number of infants" },
        pets: { type: "number", description: "Number of pets" }
      },
      required: ["location"]
    }
  },
  {
    name: "airbnb_listing_details",
    description: "Get detailed information about a specific Airbnb listing",
    inputSchema: {
      type: "object",
      properties: {
        listing_id: { type: "string", description: "The Airbnb listing ID" }
      },
      required: ["listing_id"]
    }
  }
];

async function handleAirbnbSearch(args: any) {
  const searchParams = new URLSearchParams();
  if (args.location) searchParams.set('query', args.location);
  if (args.checkin) searchParams.set('checkin', args.checkin);
  if (args.checkout) searchParams.set('checkout', args.checkout);
  if (args.adults) searchParams.set('adults', args.adults.toString());
  if (args.children) searchParams.set('children', args.children.toString());
  if (args.infants) searchParams.set('infants', args.infants.toString());
  if (args.pets) searchParams.set('pets', args.pets.toString());

  const searchUrl = `https://www.airbnb.com/s/homes?${searchParams.toString()}`;
  if (!isAllowedByRobots(new URL(searchUrl).pathname)) {
    throw new McpError(ErrorCode.InvalidRequest, "Access not allowed by robots.txt");
  }

  log('info', 'Fetching Airbnb search page', { url: searchUrl });
  const response = await fetch(searchUrl, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; ClaudeBot/1.0; +https://www.anthropic.com)',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Language': 'en-US,en;q=0.5'
    }
  });

  if (!response.ok) throw new McpError(ErrorCode.InternalError, `Failed to fetch: ${response.statusText}`);

  const html = await response.text();
  const $ = cheerio.load(html);
  const listings: any[] = [];

  $('[itemprop="itemListElement"]').each((_, element) => {
    const $element = $(element);
    const listing = {
      title: $element.find('[data-testid="listing-card-title"]').first().text().trim(),
      price: $element.find('[data-testid="listing-card-price"]').first().text().trim(),
      rating: $element.find('[aria-label*="rating"]').first().attr('aria-label'),
      url: $element.find('a[href^="/rooms/"]').first().attr('href'),
      image: $element.find('img').first().attr('src')
    };
    if (listing.title && listing.url) {
      if (!listing.url.startsWith('http')) listing.url = `https://www.airbnb.com${listing.url}`;
      listings.push(listing);
    }
  });

  log('info', 'Search completed', { resultCount: listings.length });
  return { content: [{ type: "text", text: JSON.stringify({ listings, search_params: args }, null, 2) }] };
}

async function handleAirbnbListingDetails(args: any) {
  const listingUrl = `https://www.airbnb.com/rooms/${args.listing_id}`;
  if (!isAllowedByRobots(new URL(listingUrl).pathname)) {
    throw new McpError(ErrorCode.InvalidRequest, "Access not allowed by robots.txt");
  }

  log('info', 'Fetching listing details', { listingId: args.listing_id });
  const response = await fetch(listingUrl, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; ClaudeBot/1.0; +https://www.anthropic.com)',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Language': 'en-US,en;q=0.5'
    }
  });

  if (!response.ok) throw new McpError(ErrorCode.InternalError, `Failed to fetch: ${response.statusText}`);

  const html = await response.text();
  const $ = cheerio.load(html);
  const details = {
    title: $('h1').first().text().trim(),
    description: $('[data-section-id="DESCRIPTION_DEFAULT"] span').text().trim(),
    amenities: $('[data-section-id="AMENITIES_DEFAULT"] [data-testid="modal-container"] div').map((_, el) => $(el).text().trim()).get(),
    host: $('[data-section-id="HOST_PROFILE_DEFAULT"] h2').text().trim(),
    reviews: $('[data-review-id]').map((_, el) => ({
      text: $(el).find('[data-testid="review-text"]').text().trim(),
      rating: $(el).find('[aria-label*="rating"]').attr('aria-label'),
      author: $(el).find('[data-testid="review-author"]').text().trim()
    })).get()
  };

  log('info', 'Listing details fetched', { listingId: args.listing_id });
  return { content: [{ type: "text", text: JSON.stringify(details, null, 2) }] };
}

function createServer(): Server {
  const server = new Server(
    { name: "airbnb", version: VERSION },
    { capabilities: { tools: {} } }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => {
    log('info', 'ListTools request received');
    return { tools: AIRBNB_TOOLS };
  });

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    log('info', 'CallTool request received', { tool: request.params.name, arguments: request.params.arguments });
    if (!robotsTxtContent && !IGNORE_ROBOTS_TXT) await fetchRobotsTxt();
    switch (request.params.name) {
      case "airbnb_search": return await handleAirbnbSearch(request.params.arguments);
      case "airbnb_listing_details": return await handleAirbnbListingDetails(request.params.arguments);
      default: throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${request.params.name}`);
    }
  });

  return server;
}

// ===== Express app following official MCP SDK pattern =====

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 8080;

// Store transports by session ID
const transports: { [sessionId: string]: StreamableHTTPServerTransport } = {};

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', version: VERSION });
});

// Handle POST requests for client-to-server communication
app.post('/mcp', async (req, res) => {
  const sessionId = req.headers['mcp-session-id'] as string | undefined;
  let transport: StreamableHTTPServerTransport;

  log('info', 'POST /mcp', {
    sessionId: sessionId || 'none',
    isInitialize: isInitializeRequest(req.body),
    method: req.body?.method
  });

  if (sessionId && transports[sessionId]) {
    transport = transports[sessionId];
  } else if (!sessionId && isInitializeRequest(req.body)) {
    transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
      onsessioninitialized: (sessionId) => {
        transports[sessionId] = transport;
        log('info', 'Session stored', { sessionId });
      }
    });

    transport.onclose = () => {
      if (transport.sessionId) {
        delete transports[transport.sessionId];
        log('info', 'Session cleaned up', { sessionId: transport.sessionId });
      }
    };

    const server = createServer();
    await server.connect(transport);
    log('info', 'New MCP server connected to transport');
  } else {
    res.status(400).json({
      jsonrpc: '2.0',
      error: { code: -32000, message: 'Bad Request: No valid session ID provided' },
      id: null,
    });
    return;
  }

  await transport.handleRequest(req, res, req.body);
});

// Handle GET requests for server-to-client notifications via SSE
app.get('/mcp', async (req, res) => {
  const sessionId = req.headers['mcp-session-id'] as string | undefined;
  log('info', 'GET /mcp (SSE)', { sessionId: sessionId || 'none' });

  if (!sessionId || !transports[sessionId]) {
    res.status(400).send('Invalid or missing session ID');
    return;
  }
  await transports[sessionId].handleRequest(req, res);
});

// Handle DELETE requests for session termination
app.delete('/mcp', async (req, res) => {
  const sessionId = req.headers['mcp-session-id'] as string | undefined;
  log('info', 'DELETE /mcp', { sessionId: sessionId || 'none' });

  if (!sessionId || !transports[sessionId]) {
    res.status(400).send('Invalid or missing session ID');
    return;
  }
  await transports[sessionId].handleRequest(req, res);
});

app.use((req, res) => {
  res.status(404).json({ error: 'Not Found', availableEndpoints: { mcp: '/mcp', health: '/health' } });
});

app.listen(PORT, async () => {
  log('info', 'Starting Airbnb MCP Server');
  if (!IGNORE_ROBOTS_TXT) await fetchRobotsTxt();
  log('info', 'Airbnb MCP Server running', { version: VERSION, port: PORT });
});

process.on('SIGINT', () => process.exit(0));
process.on('SIGTERM', () => process.exit(0));
