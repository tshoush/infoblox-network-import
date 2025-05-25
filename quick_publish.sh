#!/bin/bash

# Quick GitHub publish script

echo "🚀 Quick GitHub Publish Commands"
echo "================================"
echo ""
echo "Since GitHub CLI is installed, here's the fastest way:"
echo ""
echo "1. First, make sure you're logged in to GitHub CLI:"
echo "   gh auth login"
echo ""
echo "2. Then create and push in one command:"
echo "   gh repo create infoblox-network-import --public --source=. --push --description 'Import networks from AWS, Azure, GCP into InfoBlox IPAM'"
echo ""
echo "That's it! Your repo will be created and all code pushed automatically."
echo ""
echo "Alternative manual method:"
echo "1. Create repo at https://github.com/new"
echo "2. git remote add origin https://github.com/YOUR_USERNAME/infoblox-network-import.git"
echo "3. git push -u origin main"
