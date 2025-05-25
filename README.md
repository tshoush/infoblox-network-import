# InfoBlox Network Import Tool

A comprehensive Python solution for importing networks from various cloud providers (AWS, Azure, GCP, Alibaba) into InfoBlox IPAM.

## Features

- 🌐 **Multi-Source Import**: Support for AWS, Properties, and Custom CSV formats
- 🖥️ **Dual Interface**: Command-line tool and web application
- 🏷️ **Extended Attributes**: Automatic mapping of cloud tags to InfoBlox EAs
- 🔍 **Overlap Detection**: Identifies subnet conflicts before import
- 👁️ **Preview Mode**: Review all changes before applying
- 🚫 **No Deletion Policy**: Never removes networks from InfoBlox
- 📊 **Comprehensive Reporting**: Track changes and missing networks
- 🔌 **MCP Server**: Integration with Claude Desktop via Model Context Protocol

## Quick Start

### Prerequisites
- Python 3.8+
- Access to InfoBlox WAPI v2.13.1
- InfoBlox credentials with network creation permissions

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/infoblox-network-import.git
cd infoblox-network-import
```

2. Run setup:
```bash
./setup.sh
```

3. Configure InfoBlox credentials:
```bash
cp .env.example .env
# Edit .env with your InfoBlox details
```

### Usage

#### CLI Interface
```bash
# Test connection
python app/cli.py test-connection

# Import networks (dry run)
python app/cli.py import-networks -f example_aws_networks.csv -s aws --dry-run

# Import networks (actual)
python app/cli.py import-networks -f example_aws_networks.csv -s aws

# List network views
python app/cli.py list-network-views
```

#### Web Interface
```bash
./run_web.sh
# Open http://localhost:8000
```

## Supported File Formats

### AWS Format
```csv
AccountId,Region,VpcId,Name,CidrBlock,IsDefault,State,Tags
123456,us-east-1,vpc-123,Production,10.0.0.0/16,false,available,"[{""Key"":""Env"",""Value"":""Prod""}]"
```

### Properties Format
```csv
Property_Name,Network,Description,Environment,Owner,Department
Downtown Office,10.10.0.0/24,Main office,Production,IT Ops,IT
```

## Configuration

Configuration is managed through environment variables in `.env`:
- `INFOBLOX_GRID_MASTER`: Grid Master IP address
- `INFOBLOX_USERNAME`: API username  
- `INFOBLOX_PASSWORD`: API password
- `INFOBLOX_NETWORK_VIEW`: Default network view

## MCP Server (Claude Desktop Integration)

The project includes an MCP server for integration with Claude Desktop. See [mcp-server/README.md](mcp-server/README.md) for setup instructions.

## Documentation

- [Configuration Guide](CONFIGURATION.md)
- [Quick Reference](QUICK_REFERENCE.md)
- [API Documentation](docs/API.md)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with FastAPI, Click, and Pydantic
- Designed for InfoBlox WAPI v2.13.1
- Inspired by the need for automated network management
