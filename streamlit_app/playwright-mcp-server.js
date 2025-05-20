// Custom MCP Playwright server
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const http = require('http');

// Create log directory if it doesn't exist
const logDir = path.join(__dirname, 'logs');
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

// Configure logging
const logStream = fs.createWriteStream(path.join(logDir, 'playwright-mcp-server.log'), { flags: 'a' });
const errorStream = fs.createWriteStream(path.join(logDir, 'playwright-mcp-server-error.log'), { flags: 'a' });

// Redirect console output to logs
const originalConsoleLog = console.log;
const originalConsoleError = console.error;

console.log = (...args) => {
  const message = args.map(arg => 
    typeof arg === 'object' ? JSON.stringify(arg, null, 2) : arg
  ).join(' ');
  logStream.write(`${new Date().toISOString()} - ${message}\n`);
  originalConsoleLog(...args);
};

console.error = (...args) => {
  const message = args.map(arg => 
    typeof arg === 'object' ? JSON.stringify(arg, null, 2) : arg
  ).join(' ');
  errorStream.write(`${new Date().toISOString()} - ERROR: ${message}\n`);
  originalConsoleError(...args);
};

// Log startup information
console.log('Starting custom MCP Playwright server...');
console.log(`Current directory: ${__dirname}`);
console.log(`Node version: ${process.version}`);
console.log(`Platform: ${process.platform}`);

// Handle process signals
process.on('SIGINT', () => {
  console.log('Received SIGINT signal, shutting down gracefully...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('Received SIGTERM signal, shutting down gracefully...');
  process.exit(0);
});

process.on('uncaughtException', (err) => {
  console.error('Uncaught exception:', err);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection at:', promise, 'reason:', reason);
});

// Create a simple HTTP server for health checks
const PORT = 5006; // Changed from 5000 to avoid conflicts
const server = http.createServer((req, res) => {
  if (req.url === '/healthz') {
    res.statusCode = 200;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ status: 'healthy', service: 'playwright-mcp' }));
  } else if (req.url === '/playwright') {
    // Handle Playwright commands in future
    res.statusCode = 200;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ status: 'ready' }));
  } else {
    res.statusCode = 404;
    res.end('Not found');
  }
});

// Start the server
server.listen(PORT, () => {
  console.log(`Playwright MCP server running on http://localhost:${PORT}`);
  console.log('Available endpoints:');
  console.log(`- Health check: http://localhost:${PORT}/healthz`);
  console.log(`- Playwright API: http://localhost:${PORT}/playwright`);
});

// Log that we're ready to accept connections
console.log('Playwright MCP server started successfully');