import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import type { GameState } from '~/game-state/GameState.types';

export interface McpGameStateResult {
  success: boolean;
  gameState?: GameState;
  error?: string;
}

export class McpClient {
  private client: Client | null = null;
  private transport: StdioClientTransport | null = null;
  private isConnected = false;

  async connect(): Promise<void> {
    if (this.isConnected) {
      return;
    }

    try {
      this.transport = new StdioClientTransport({
        command: 'uv',
        args: ['run', 'python', '-m', 'open_llms_play_pokemon.mcp_server'],
        cwd: process.cwd().replace('/ui', ''),
        stderr: 'ignore',
      });

      this.client = new Client(
        {
          name: 'pokemon-ui-client',
          version: '1.0.0',
        },
        {
          capabilities: {},
        },
      );

      await this.client.connect(this.transport);
      this.isConnected = true;
      if (this.transport.stderr) {
        this.transport.stderr.on('data', (data) => {
          console.error('MCP Server stderr:', data.toString());
        });
      }
    } catch (error) {
      console.error('Failed to connect to MCP server:', error);
      this.isConnected = false;
      throw error;
    }
  }

  async disconnect(): Promise<void> {
    if (this.client && this.transport) {
      await this.client.close();
      this.client = null;
      this.transport = null;
      this.isConnected = false;
    }
  }

  async getGameStateFromFile(stateFilePath: string): Promise<McpGameStateResult> {
    if (!this.isConnected || !this.client) {
      await this.connect();
    }

    try {
      const result = await this.client?.callTool({
        name: 'get_game_state_json',
        arguments: {
          state_file_path: stateFilePath,
        },
      });

      if (!result) {
        return {
          success: false,
          error: 'MCP client not available',
        };
      }

      if (result.isError) {
        return {
          success: false,
          error: `MCP tool error: ${Array.isArray(result.content) ? result.content[0]?.text : 'Unknown error'}`,
        };
      }

      const content = Array.isArray(result.content) ? result.content[0]?.text : undefined;
      if (!content) {
        return {
          success: false,
          error: 'No content returned from MCP server',
        };
      }

      const gameState = JSON.parse(content) as GameState;
      return {
        success: true,
        gameState,
      };
    } catch (error) {
      return {
        success: false,
        error:
          error instanceof Error ? error.message : 'Unknown error parsing game state',
      };
    }
  }

  isClientConnected(): boolean {
    return this.isConnected;
  }
}

let mcpClientInstance: McpClient | null = null;
export function getMcpClient(): McpClient {
  if (!mcpClientInstance) {
    mcpClientInstance = new McpClient();
  }
  return mcpClientInstance;
}
