# InfoBlox Network Import Tool

Created: May 24, 2025
Version: 1.0.0

## Quick Start

```bash
# 1. Setup environment
./setup.sh

# 2. Configure InfoBlox credentials
cp .env.example .env
# Edit .env with your credentials

# 3. Test connection
source venv/bin/activate
python app/cli.py test-connection

# 4. Import networks
python app/cli.py import-networks -f example_aws_networks.csv -s aws --dry-run
```

## Project Structure

- `app/` - Main Python application
  - `cli.py` - Command-line interface
  - `core/` - Business logic (InfoBlox API, parsers, models)
- `mcp-server/` - Claude Desktop integration
- `example_*.csv/json` - Sample files
- `requirements.txt` - Python dependencies
- `setup.sh` - Quick setup script

## MCP Server (Claude Desktop)

```bash
cd mcp-server
npm install
npm run build
```

Then add configuration from `claude_desktop_config.json` to Claude Desktop.

## Features

✅ Multi-cloud support (AWS, Azure, GCP, Alibaba)
✅ Extended Attributes mapping
✅ Overlap detection
✅ Change preview with dry-run
✅ No deletion policy
✅ Claude Desktop integration
