# InfoBlox Network Import - Quick Reference

## 🚀 Quick Commands

### Test Connection
```bash
python app/cli.py test-connection
```

### View Current Networks
```bash
python list_infoblox_networks.py
```

### List Network Views
```bash
python app/cli.py list-network-views
# or
python list_network_views.py
```

### Import Networks (Dry Run)
```bash
# AWS format
python app/cli.py import-networks -f example_aws_networks.csv -s aws --dry-run

# Properties format
python app/cli.py import-networks -f example_properties_networks.csv -s properties --dry-run

# Specific network view
python app/cli.py import-networks -f file.csv -s aws --network-view Production --dry-run
```

### Import Networks (For Real)
```bash
# Remove --dry-run to actually import
python app/cli.py import-networks -f your_file.csv -s properties
```

### Web Interface
```bash
./run_web.sh
# Open http://localhost:8000
```

## 📁 File Formats

### AWS Format
- Columns: AccountId, Region, VpcId, Name, CidrBlock, IsDefault, State, Tags
- Tags: JSON format

### Properties Format  
- Columns: Property_Name, Network, Description, Environment, Owner, etc.
- All extra columns → Extended Attributes

### Custom Format
- Auto-detects network/CIDR columns
- All columns → Extended Attributes

## 🔧 Configuration

Edit `.env` file:
```
INFOBLOX_GRID_MASTER=192.168.1.222
INFOBLOX_USERNAME=admin
INFOBLOX_PASSWORD=infoblox
INFOBLOX_NETWORK_VIEW=default
```

## ✅ Status

- AWS Parser: **WORKING** ✅
- Properties Parser: **WORKING** ✅
- Overlap Detection: **WORKING** ✅
- Extended Attributes: **WORKING** ✅
- Web Interface: **WORKING** ✅
