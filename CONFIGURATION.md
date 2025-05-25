# InfoBlox Configuration Guide

## Where to Configure InfoBlox Settings

### 1. Environment Variables (`.env` file)

**Primary method for both CLI and Web interfaces:**

```bash
# Copy the example file
cp .env.example .env

# Edit with your settings
INFOBLOX_GRID_MASTER=192.168.1.222
INFOBLOX_USERNAME=admin
INFOBLOX_PASSWORD=infoblox
INFOBLOX_NETWORK_VIEW=default
```

### 2. CLI Options

**Override environment variables per command:**

```bash
# Using CLI flags
python app/cli.py import-networks \
    -f networks.csv \
    -s aws \
    --network-view "Production"

# Test connection
python app/cli.py test-connection
```

### 3. Web Interface Settings

**Runtime configuration (doesn't persist):**

1. Open web interface: http://localhost:8000
2. Click "⚙️ InfoBlox Connection Settings" to expand
3. Modify any setting:
   - Grid Master IP
   - Network View
   - Username
   - Password
4. Click "Test Connection" to verify
5. Settings apply only to current session

### 4. Priority Order

Settings are applied in this order (highest priority first):
1. Web interface runtime settings
2. CLI command-line arguments
3. Environment variables (.env file)
4. Default values

### 5. Network Views

Network Views control which IP space you're working with:
- `default` - Standard network view
- `Production` - Production networks
- `Development` - Dev/test networks
- Custom views as configured in InfoBlox

### 6. Security Notes

- Never commit `.env` file to git (it's in .gitignore)
- Use strong passwords
- Consider using secrets management in production
- Enable SSL verification for production:
  ```
  INFOBLOX_VERIFY_SSL=true
  ```

### 7. Testing Configuration

Always test your configuration:

**CLI:**
```bash
python app/cli.py test-connection
```

**Web:**
- Use "Test Connection" button in settings panel
- Check http://localhost:8000/api/v1/test-connection

### 8. Troubleshooting

If connection fails:
1. Check Grid Master IP is reachable: `ping 192.168.1.222`
2. Verify credentials in InfoBlox admin panel
3. Ensure network view exists
4. Check firewall allows HTTPS (port 443)
5. Review logs in `logs/infoblox_import.log`
