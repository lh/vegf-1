#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { PythonShell } from 'python-shell';
import { Project, SourceFile } from 'ts-morph';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = process.env.PROJECT_ROOT || '/Users/rose/Code/aided';

interface DocGenArgs {
  module_path: string;
  strict_validation?: boolean;
}

interface DocValidationArgs {
  check_coverage?: boolean;
}

const isValidDocGenArgs = (args: any): args is DocGenArgs =>
  typeof args === 'object' &&
  args !== null &&
  typeof args.module_path === 'string' &&
  (args.strict_validation === undefined || typeof args.strict_validation === 'boolean');

const isValidDocValidationArgs = (args: any): args is DocValidationArgs =>
  typeof args === 'object' &&
  args !== null &&
  (args.check_coverage === undefined || typeof args.check_coverage === 'boolean');

class DocGenServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: 'docgen-server',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
    
    // Error handling
    this.server.onerror = (error: Error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  private createPythonShell(): PythonShell {
    return new PythonShell('docstring_parser.py', {
      mode: 'text',
      pythonPath: 'python3',
      pythonOptions: ['-u'],
      scriptPath: __dirname,
    });
  }

  private setupHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'generate_module_docs',
          description: 'Generate documentation for a Python module with Numpy docstrings',
          inputSchema: {
            type: 'object',
            properties: {
              module_path: {
                type: 'string',
                description: 'Path to the Python module',
              },
              strict_validation: {
                type: 'boolean',
                description: 'Enable strict docstring validation',
              },
            },
            required: ['module_path'],
          },
        },
        {
          name: 'validate_docstrings',
          description: 'Validate Numpy docstrings across the project',
          inputSchema: {
            type: 'object',
            properties: {
              check_coverage: {
                type: 'boolean',
                description: 'Check documentation coverage',
              },
            },
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      try {
        switch (request.params.name) {
          case 'generate_module_docs':
            if (!isValidDocGenArgs(request.params.arguments)) {
              throw new McpError(
                ErrorCode.InvalidParams,
                'Invalid generate_module_docs arguments'
              );
            }
            return await this.generateModuleDocs(request.params.arguments);

          case 'validate_docstrings':
            if (!isValidDocValidationArgs(request.params.arguments)) {
              throw new McpError(
                ErrorCode.InvalidParams,
                'Invalid validate_docstrings arguments'
              );
            }
            return await this.validateDocstrings(request.params.arguments);

          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${request.params.name}`
            );
        }
      } catch (error) {
        if (error instanceof McpError) {
          throw error;
        }
        console.error('[DocGen Error]', error);
        throw new McpError(
          ErrorCode.InternalError,
          `Internal server error: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    });
  }

  private async parseDocstrings(sourceCode: string, strict: boolean = false): Promise<any> {
    const pyshell = this.createPythonShell();
    try {
      const result = await new Promise((resolve, reject) => {
        pyshell.send(JSON.stringify({
          code: sourceCode,
          strict,
        }));

        pyshell.once('message', (message) => {
          resolve(JSON.parse(message));
        });

        pyshell.once('error', reject);
      });
      await new Promise<void>((resolve) => pyshell.end(() => resolve()));
      return result;
    } catch (error) {
      await new Promise<void>((resolve) => pyshell.end(() => resolve()));
      throw error;
    }
  }

  private async generateModuleDocs(args: DocGenArgs) {
    const modulePath = path.resolve(PROJECT_ROOT, args.module_path);
    
    if (!fs.existsSync(modulePath)) {
      return {
        content: [
          {
            type: 'text',
            text: `Error: Module not found at ${modulePath}`,
          },
        ],
        isError: true,
      };
    }

    try {
      // Read the Python file
      const sourceCode = fs.readFileSync(modulePath, 'utf-8');

      // Parse docstrings using Python
      const docstrings = await this.parseDocstrings(sourceCode, args.strict_validation);

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(docstrings, null, 2),
          },
        ],
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: 'text',
            text: `Error processing module: ${error?.message || 'Unknown error'}`,
          },
        ],
        isError: true,
      };
    }
  }

  private async validateDocstrings(args: DocValidationArgs) {
    try {
      const pythonFiles = this.findPythonFiles(PROJECT_ROOT);
      const results = {
        total_files: pythonFiles.length,
        files_with_issues: 0,
        issues: [] as Array<{file: string, message: string}>,
      };

      // Process files in batches of 5
      const batchSize = 5;
      for (let i = 0; i < pythonFiles.length; i += batchSize) {
        const batch = pythonFiles.slice(i, i + batchSize);
        const batchPromises = batch.map(async (file) => {
          try {
            const sourceCode = fs.readFileSync(file, 'utf-8');
            const docstrings = await this.parseDocstrings(sourceCode, true);

            const relativePath = path.relative(PROJECT_ROOT, file);
            if (args.check_coverage) {
              const doc = docstrings as any;
              if (!doc.module) {
                results.issues.push({
                  file: relativePath,
                  message: 'Missing module docstring',
                });
              }

              for (const [className, classData] of Object.entries<any>(doc.classes)) {
                if (!classData.docstring) {
                  results.issues.push({
                    file: relativePath,
                    message: `Missing docstring for class ${className}`,
                  });
                }
              }

              for (const [funcName, funcData] of Object.entries<any>(doc.functions)) {
                if (!funcData.summary) {
                  results.issues.push({
                    file: relativePath,
                    message: `Missing or incomplete docstring for function ${funcName}`,
                  });
                }
              }
            }
          } catch (error) {
            console.error(`Error processing ${file}:`, error);
          }
        });

        await Promise.all(batchPromises);
      }

      results.files_with_issues = results.issues.length;

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(results, null, 2),
          },
        ],
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: 'text',
            text: `Error validating docstrings: ${error?.message || 'Unknown error'}`,
          },
        ],
        isError: true,
      };
    }
  }

  private findPythonFiles(dir: string): string[] {
    const files: string[] = [];
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory() && !entry.name.startsWith('.')) {
        files.push(...this.findPythonFiles(fullPath));
      } else if (entry.isFile() && entry.name.endsWith('.py')) {
        files.push(fullPath);
      }
    }

    return files;
  }

  async run() {
    try {
      const transport = new StdioServerTransport();
      await this.server.connect(transport);
      console.error('DocGen MCP server running on stdio');
    } catch (error) {
      console.error('Failed to start server:', error);
      process.exit(1);
    }
  }
}

const server = new DocGenServer();
server.run().catch(console.error);
