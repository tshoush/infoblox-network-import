# CLI Network View Selection - Enhanced

## 🎯 Current Behavior (UPDATED)

The CLI now **automatically fetches and prompts** for network view selection!

### When Prompting Occurs:

1. ✅ **Default view + Multiple views available + Interactive mode**
   ```bash
   python app/cli.py import-networks -f file.csv -s aws
   
   # Output:
   Available Network Views:
   1. default      ← current default
   2. Tarig_view
   3. Tarig2
   4. Test_view
   5. Tarig5
   6. Tarig6
   
   Select network view: [press Enter for default or type number]
   ```

2. ❌ **Specific view provided** (no prompt)
   ```bash
   python app/cli.py import-networks -f file.csv -s aws --network-view Tarig_view
   # Uses Tarig_view directly, no prompt
   ```

3. ❌ **No-confirm mode** (no prompt) 
   ```bash
   python app/cli.py import-networks -f file.csv -s aws --no-confirm
   # Uses default, no prompt
   ```

### Interactive Selection Features:

- **Shows all available views** with numbers
- **Indicates current default** with arrow
- **Press Enter** to use default
- **Type number** to select different view
- **Invalid input** falls back to default

### Example Session:

```
$ python app/cli.py import-networks -f example_aws_networks.csv -s aws --dry-run

InfoBlox Network Import
Source: aws | File: example_aws_networks.csv

✓ Connected to InfoBlox Grid Master

Available Network Views:
1. default      ← current default  
2. Tarig_view
3. Tarig2
4. Test_view
5. Tarig5
6. Tarig6

Press Enter for 'default' or enter number:
Select network view: 2
✓ Selected: Tarig_view

✓ Parsed 4 networks from file
...
```

## 📋 Summary

- **Web Interface**: Dropdown selection (always visible)
- **CLI Interface**: Smart prompting when appropriate
- **Both**: Dynamically fetch available views from InfoBlox

The CLI is now as user-friendly as the web interface! 🎉
