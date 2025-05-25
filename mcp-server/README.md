# InfoBlox MCP Server

Model Context Protocol (MCP) server for InfoBlox WAPI integration with Claude Desktop.

## Installation

1. Install dependencies:
```bash
cd /Users/Shared/infoblox-network-import/mcp-server
npm install
```

2. Build the server:
```bash
npm run build
```

3. Configure Claude Desktop:

Add the following to your Claude Desktop configuration file:
- On macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- On Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "infoblox": {
      "command": "node",
      "args": ["/Users/Shared/infoblox-network-import/mcp-server/dist/index.js"],
      "env": {
        "INFOBLOX_GRID_MASTER": "192.168.1.222",
        "INFOBLOX_USERNAME": "admin",
        "INFOBLOX_PASSWORD": "infoblox"
      }
    }
  }
}
```

4. Restart Claude Desktop

## Available Tools

- `infoblox_test_connection`: Test connection to InfoBlox Grid Master
- `infoblox_create_network`: Create a network with Extended Attributes
- `infoblox_get_network`: Get network information
- `infoblox_update_network`: Update an existing network
- `infoblox_search_networks`: Search for networks with filters
- `infoblox_check_overlaps`: Check if a network overlaps with existing networks
- `infoblox_create_ea_definition`: Create Extended Attribute definition
- `infoblox_get_ea_definition`: Get Extended Attribute definition
- `infoblox_list_ea_definitions`: List all EA definitions
- `infoblox_get_schema`: Get WAPI schema information

## Environment Variables

- `INFOBLOX_GRID_MASTER`: InfoBlox Grid Master IP (default: 192.168.1.222)
- `INFOBLOX_USERNAME`: API username (default: admin)
- `INFOBLOX_PASSWORD`: API password (default: infoblox)
- `INFOBLOX_WAPI_VERSION`: WAPI version (default: 2.13.1)
