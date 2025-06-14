#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import Database from 'better-sqlite3';

interface TableInfo {
  name: string;
}

interface ColumnInfo {
  cid: number;
  name: string;
  type: string;
  notnull: number;
  dflt_value: string | null;
  pk: number;
}

class SQLiteServer {
  private server: Server;
  private connections: Map<string, Database.Database>;

  constructor() {
    this.server = new Server(
      {
        name: 'sqlite-server',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.connections = new Map();
    this.setupToolHandlers();
    
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      // Close all database connections
      for (const db of this.connections.values()) {
        db.close();
      }
      await this.server.close();
      process.exit(0);
    });
  }

  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'execute_query',
          description: 'Execute a SQL query on a SQLite database',
          inputSchema: {
            type: 'object',
            properties: {
              dbPath: {
                type: 'string',
                description: 'Path to the SQLite database file',
              },
              query: {
                type: 'string',
                description: 'SQL query to execute',
              },
              params: {
                type: 'object',
                description: 'Query parameters (optional)',
                additionalProperties: true,
              },
            },
            required: ['dbPath', 'query'],
          },
        },
        {
          name: 'get_schema',
          description: 'Get schema information for a SQLite database',
          inputSchema: {
            type: 'object',
            properties: {
              dbPath: {
                type: 'string',
                description: 'Path to the SQLite database file',
              },
            },
            required: ['dbPath'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      switch (request.params.name) {
        case 'execute_query':
          return this.executeQuery(request.params.arguments);
        case 'get_schema':
          return this.getSchema(request.params.arguments);
        default:
          throw new McpError(
            ErrorCode.MethodNotFound,
            `Unknown tool: ${request.params.name}`
          );
      }
    });
  }

  private getConnection(dbPath: string): Database.Database {
    let db = this.connections.get(dbPath);
    if (!db) {
      try {
        db = new Database(dbPath);
        this.connections.set(dbPath, db);
      } catch (error: any) {
        throw new McpError(
          ErrorCode.InternalError,
          `Failed to connect to database: ${error?.message || 'Unknown error'}`
        );
      }
    }
    return db;
  }

  private executeQuery(args: any) {
    if (!args.dbPath || typeof args.dbPath !== 'string') {
      throw new McpError(ErrorCode.InvalidParams, 'Database path is required');
    }
    if (!args.query || typeof args.query !== 'string') {
      throw new McpError(ErrorCode.InvalidParams, 'Query is required');
    }

    const db = this.getConnection(args.dbPath);
    try {
      const stmt = db.prepare(args.query);
      let result;
      
      if (args.query.trim().toLowerCase().startsWith('select')) {
        result = stmt.all(args.params || {});
      } else {
        result = stmt.run(args.params || {});
      }

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: 'text',
            text: `SQLite error: ${error?.message || 'Unknown error'}`,
          },
        ],
        isError: true,
      };
    }
  }

  private getSchema(args: any) {
    if (!args.dbPath || typeof args.dbPath !== 'string') {
      throw new McpError(ErrorCode.InvalidParams, 'Database path is required');
    }

    const db = this.getConnection(args.dbPath);
    try {
      const tables = db.prepare<TableInfo[]>(`
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
      `).all() as TableInfo[];

      const schema: Record<string, ColumnInfo[]> = {};
      
      for (const table of tables) {
        const columns = db.prepare<ColumnInfo[]>(`PRAGMA table_info(${table.name})`).all() as ColumnInfo[];
        schema[table.name] = columns;
      }

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(schema, null, 2),
          },
        ],
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: 'text',
            text: `SQLite error: ${error?.message || 'Unknown error'}`,
          },
        ],
        isError: true,
      };
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('SQLite MCP server running on stdio');
  }
}

const server = new SQLiteServer();
server.run().catch(console.error);
