# InfoBlox Network Import Tool

A comprehensive solution for importing networks from various cloud providers (AWS, Azure, GCP, Alibaba) into InfoBlox IPAM. The tool provides both CLI and web interfaces, with support for Extended Attributes mapping, overlap detection, and change preview.

## Features

- **Multi-Source Import**: Support for AWS, Azure, GCP, Alibaba, and custom CSV/Excel formats
- **Dual Interface**: Command-line tool and web application
- **Extended Attributes**: Automatic mapping of cloud tags to InfoBlox EAs
- **Overlap Detection**: Identifies subnet conflicts before import
- **Change Preview**: Review all changes before applying
- **No Deletion Policy**: Never removes networks from InfoBlox
- **Comprehensive Reporting**: Track missing networks and changes
- **MCP Server**: Integration with Claude Desktop via Model Context Protocol

## Project Structure

```
infoblox-network-import/
├── app/                    # Main application
│   ├── core/              # Business logic
│   │   ├── infoblox.py    # InfoBlox WAPI wrapper
│   │   ├── models.py      # Data models
│   │   └── parsers.py     # Cloud provider parsers
│   ├── cli.py             # CLI application
│   └── web.py             # Web application (FastAPI)
├── mcp-server/            # MCP server for Claude Desktop
├── templates/             # Report templates
├── requirements.txt       # Python dependencies
└── .env.example          # Environment variables template
```

## Installation

1. Clone the repository:
```bash
cd /Users/Shared/infoblox-network-import
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your InfoBlox credentials
```

## Usage

### CLI Application

1. Test connection:
```bash
python app/cli.py test-connection
```

2. Import networks:
```bash
# Basic import
python app/cli.py import-networks -f aws_networks.csv -s aws

# With dry run
python app/cli.py import-networks -f aws_networks.csv -s aws --dry-run

# With custom EA mapping
python app/cli.py import-networks -f aws_networks.csv -s aws -m ea_mappings.json
```

3. Generate EA mapping template:
```bash
python app/cli.py generate-mapping-template -s aws -o my_mappings.json
```

4. List Extended Attributes:
```bash
python app/cli.py list-eas
```

## AWS File Format

The tool expects AWS network data in CSV or Excel format with these columns:
- **AccountId**: AWS Account ID
- **Region**: AWS Region
- **VpcId**: VPC identifier
- **Name**: Network name
- **CidrBlock**: Network CIDR (e.g., 10.0.0.0/24)
- **IsDefault**: Boolean flag
- **State**: Network state
- **Tags**: JSON string or key=value pairs

Example Tags format:
```json
[{"Key": "Environment", "Value": "Production"}, {"Key": "Owner", "Value": "DevOps"}]
```

## Extended Attributes Mapping

Create a mapping file to control how cloud tags map to InfoBlox EAs:

```json
{
  "description": "EA mapping for AWS networks",
  "mappings": [
    {
      "source_tag": "Environment",
      "target_ea": "Environment",
      "transform": "uppercase",
      "ea_type": "STRING"
    },
    {
      "source_tag": "Owner",
      "target_ea": "Network_Owner",
      "default_value": "Unknown",
      "ea_type": "STRING"
    }
  ]
}
```

## MCP Server Setup

The MCP server allows Claude Desktop to interact with InfoBlox directly:

1. Build the MCP server:
```bash
cd mcp-server
npm install
npm run build
```

2. Add to Claude Desktop config:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

3. Restart Claude Desktop

Available tools in Claude:
- `infoblox_test_connection`
- `infoblox_create_network`
- `infoblox_search_networks`
- `infoblox_check_overlaps`
- And more...

## Environment Variables

Key configuration options:
- `INFOBLOX_GRID_MASTER`: Grid Master IP (default: 192.168.1.222)
- `INFOBLOX_USERNAME`: API username (default: admin)
- `INFOBLOX_PASSWORD`: API password (default: infoblox)
- `INFOBLOX_VERIFY_SSL`: SSL verification (default: false)

## Security Considerations

1. Use environment variables for credentials
2. Enable SSL verification in production
3. Implement proper authentication for web interface
4. Restrict file upload sizes and types
5. Use network views for access control

## License

This project is licensed under the MIT License.
