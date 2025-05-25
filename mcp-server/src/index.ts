import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
  ToolSchema
} from '@modelcontextprotocol/sdk/types.js';
import axios, { AxiosInstance } from 'axios';
import https from 'https';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// InfoBlox API configuration
const INFOBLOX_HOST = process.env.INFOBLOX_GRID_MASTER || '192.168.1.222';
const INFOBLOX_USERNAME = process.env.INFOBLOX_USERNAME || 'admin';
const INFOBLOX_PASSWORD = process.env.INFOBLOX_PASSWORD || 'infoblox';
const WAPI_VERSION = process.env.INFOBLOX_WAPI_VERSION || '2.13.1';

// Create axios instance with InfoBlox configuration
const infobloxApi: AxiosInstance = axios.create({
  baseURL: `https://${INFOBLOX_HOST}/wapi/v${WAPI_VERSION}/`,
  auth: {
    username: INFOBLOX_USERNAME,
    password: INFOBLOX_PASSWORD
  },
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  httpsAgent: new https.Agent({
    rejectUnauthorized: false // Allow self-signed certificates
  }),
  timeout: 30000
});

// Define available tools
const tools: Tool[] = [
  {
    name: 'infoblox_create_network',
    description: 'Create a network in InfoBlox with optional Extended Attributes',
    inputSchema: {
      type: 'object',
      properties: {
        network: { type: 'string', description: 'Network in CIDR format (e.g., 10.0.0.0/24)' },
        network_view: { type: 'string', description: 'Network view name', default: 'default' },
        comment: { type: 'string', description: 'Network comment' },
        extattrs: { type: 'object', description: 'Extended attributes as key-value pairs' }
      },
      required: ['network']
    }
  },
  {
    name: 'infoblox_get_network',
    description: 'Get network information from InfoBlox',
    inputSchema: {
      type: 'object',
      properties: {
        network: { type: 'string', description: 'Network in CIDR format' },
        network_view: { type: 'string', description: 'Network view name', default: 'default' },
        return_fields: { 
          type: 'array', 
          items: { type: 'string' },
          description: 'Fields to return'
        }
      },
      required: ['network']
    }
  }
];
// Add more tools
tools.push(
  {
    name: 'infoblox_update_network',
    description: 'Update an existing network in InfoBlox',
    inputSchema: {
      type: 'object',
      properties: {
        network: { type: 'string', description: 'Network in CIDR format' },
        network_view: { type: 'string', description: 'Network view name', default: 'default' },
        updates: { type: 'object', description: 'Fields to update' }
      },
      required: ['network', 'updates']
    }
  },
  {
    name: 'infoblox_search_networks',
    description: 'Search for networks in InfoBlox with filters',
    inputSchema: {
      type: 'object',
      properties: {
        filters: { type: 'object', description: 'Search filters' },
        return_fields: { 
          type: 'array', 
          items: { type: 'string' },
          description: 'Fields to return'
        },
        max_results: { type: 'number', description: 'Maximum results to return', default: 100 }
      }
    }
  },
  {
    name: 'infoblox_check_overlaps',
    description: 'Check if a network overlaps with existing networks',
    inputSchema: {
      type: 'object',
      properties: {
        network: { type: 'string', description: 'Network in CIDR format' },
        network_view: { type: 'string', description: 'Network view name', default: 'default' }
      },
      required: ['network']
    }
  }
);
// Extended Attribute tools
tools.push(
  {
    name: 'infoblox_create_ea_definition',
    description: 'Create an Extended Attribute definition in InfoBlox',
    inputSchema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'EA name' },
        type: { 
          type: 'string', 
          description: 'EA type',
          enum: ['STRING', 'INTEGER', 'ENUM', 'EMAIL', 'URL', 'DATE']
        },
        comment: { type: 'string', description: 'EA comment' },
        list_values: { 
          type: 'array', 
          items: { type: 'string' },
          description: 'List values for ENUM type'
        }
      },
      required: ['name', 'type']
    }
  },
  {
    name: 'infoblox_get_ea_definition',
    description: 'Get Extended Attribute definition',
    inputSchema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'EA name' }
      },
      required: ['name']
    }
  },
  {
    name: 'infoblox_list_ea_definitions',
    description: 'List all Extended Attribute definitions',
    inputSchema: {
      type: 'object',
      properties: {}
    }
  }
);
// Utility tools
tools.push(
  {
    name: 'infoblox_get_schema',
    description: 'Get WAPI schema information',
    inputSchema: {
      type: 'object',
      properties: {
        object_type: { type: 'string', description: 'Object type to get schema for' }
      }
    }
  },
  {
    name: 'infoblox_test_connection',
    description: 'Test connection to InfoBlox Grid Master',
    inputSchema: {
      type: 'object',
      properties: {}
    }
  }
);

// Create MCP server
const server = new Server(
  {
    name: 'infoblox-mcp-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {}
    }
  }
);

// Handle tool listing
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: tools.map(tool => ({
      name: tool.name,
      description: tool.description,
      inputSchema: tool.inputSchema as ToolSchema
    }))
  };
});
// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'infoblox_create_network': {
        const { network, network_view = 'default', comment = '', extattrs } = args as any;
        const data = {
          network,
          network_view,
          comment,
          ...(extattrs && { extattrs })
        };
        
        const response = await infobloxApi.post('network', data);
        return {
          content: [{ type: 'text', text: JSON.stringify({ 
            success: true, 
            ref: response.data,
            message: `Network ${network} created successfully`
          }, null, 2) }]
        };
      }

      case 'infoblox_get_network': {
        const { network, network_view = 'default', return_fields } = args as any;
        const params: any = { network, network_view };
        
        if (return_fields && return_fields.length > 0) {
          params._return_fields = return_fields.join(',');
        }
        
        const response = await infobloxApi.get('network', { params });
        const networks = response.data;
        
        return {
          content: [{ type: 'text', text: JSON.stringify({
            success: true,
            network: networks.length > 0 ? networks[0] : null,
            found: networks.length > 0
          }, null, 2) }]
        };
      }
      case 'infoblox_update_network': {
        const { network, network_view = 'default', updates } = args as any;
        
        // First get the network to find its reference
        const getParams = { network, network_view };
        const getResponse = await infobloxApi.get('network', { params: getParams });
        const networks = getResponse.data;
        
        if (networks.length === 0) {
          return {
            content: [{ type: 'text', text: JSON.stringify({
              success: false,
              error: `Network ${network} not found`
            }, null, 2) }]
          };
        }
        
        const ref = networks[0]._ref;
        const updateResponse = await infobloxApi.put(ref, updates);
        
        return {
          content: [{ type: 'text', text: JSON.stringify({
            success: true,
            ref: updateResponse.data,
            message: `Network ${network} updated successfully`
          }, null, 2) }]
        };
      }

      case 'infoblox_search_networks': {
        const { filters = {}, return_fields, max_results = 100 } = args as any;
        const params: any = { ...filters, _max_results: max_results };
        
        if (return_fields && return_fields.length > 0) {
          params._return_fields = return_fields.join(',');
        }
        
        const response = await infobloxApi.get('network', { params });
        
        return {
          content: [{ type: 'text', text: JSON.stringify({
            success: true,
            networks: response.data,
            count: response.data.length
          }, null, 2) }]
        };
      }
      case 'infoblox_check_overlaps': {
        const { network, network_view = 'default' } = args as any;
        
        // Get all networks in the view
        const params = { network_view, _return_fields: 'network,comment,extattrs' };
        const response = await infobloxApi.get('network', { params });
        const existingNetworks = response.data;
        
        // Check for overlaps using subnet calculations
        const overlaps = [];
        for (const existing of existingNetworks) {
          // Simple overlap check - in production, use proper IP library
          if (existing.network === network || 
              existing.network.includes(network.split('/')[0]) ||
              network.includes(existing.network.split('/')[0])) {
            overlaps.push(existing);
          }
        }
        
        return {
          content: [{ type: 'text', text: JSON.stringify({
            success: true,
            has_overlaps: overlaps.length > 0,
            overlapping_networks: overlaps
          }, null, 2) }]
        };
      }

      case 'infoblox_create_ea_definition': {
        const { name, type, comment = '', list_values } = args as any;
        
        // Check if EA already exists
        const checkResponse = await infobloxApi.get('extensibleattributedef', { 
          params: { name } 
        });
        
        if (checkResponse.data.length > 0) {
          return {
            content: [{ type: 'text', text: JSON.stringify({
              success: true,
              exists: true,
              ref: checkResponse.data[0]._ref,
              message: `EA definition '${name}' already exists`
            }, null, 2) }]
          };
        }
        
        const data: any = { name, type, comment, flags: 'V' };
        if (type === 'ENUM' && list_values) {
          data.list_values = list_values.map((v: string) => ({ value: v }));
        }
        
        const response = await infobloxApi.post('extensibleattributedef', data);
        
        return {
          content: [{ type: 'text', text: JSON.stringify({
            success: true,
            ref: response.data,
            message: `EA definition '${name}' created successfully`
          }, null, 2) }]
        };
      }
      case 'infoblox_get_ea_definition': {
        const { name } = args as any;
        const response = await infobloxApi.get('extensibleattributedef', { 
          params: { name } 
        });
        
        return {
          content: [{ type: 'text', text: JSON.stringify({
            success: true,
            definition: response.data.length > 0 ? response.data[0] : null,
            found: response.data.length > 0
          }, null, 2) }]
        };
      }

      case 'infoblox_list_ea_definitions': {
        const response = await infobloxApi.get('extensibleattributedef');
        
        return {
          content: [{ type: 'text', text: JSON.stringify({
            success: true,
            definitions: response.data,
            count: response.data.length
          }, null, 2) }]
        };
      }

      case 'infoblox_get_schema': {
        const { object_type } = args as any;
        const path = object_type ? `_schema/${object_type}` : '_schema';
        const response = await infobloxApi.get(path);
        
        return {
          content: [{ type: 'text', text: JSON.stringify({
            success: true,
            schema: response.data
          }, null, 2) }]
        };
      }

      case 'infoblox_test_connection': {
        const response = await infobloxApi.get('grid');
        
        return {
          content: [{ type: 'text', text: JSON.stringify({
            success: true,
            connected: true,
            grid_info: response.data[0] || {},
            message: 'Successfully connected to InfoBlox Grid Master'
          }, null, 2) }]
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error: any) {
    return {
      content: [{ type: 'text', text: JSON.stringify({
        success: false,
        error: error.message,
        details: error.response?.data || error.toString()
      }, null, 2) }]
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('InfoBlox MCP Server started');
}

main().catch(console.error);
