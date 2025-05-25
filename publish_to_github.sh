#!/bin/bash

# GitHub Publishing Script for InfoBlox Network Import
# This script helps publish your project to GitHub

set -e  # Exit on error

echo "🚀 GitHub Publishing Assistant"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "app/cli.py" ]; then
    echo -e "${RED}❌ Error: Not in the InfoBlox project directory${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Error: Git not initialized${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found InfoBlox project${NC}"
echo ""

# Get GitHub username
echo "Please enter your GitHub username:"
read -p "Username: " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo -e "${RED}❌ Username cannot be empty${NC}"
    exit 1
fi

# Repository name
REPO_NAME="infoblox-network-import"
echo ""
echo "Repository name: $REPO_NAME"

# Check if GitHub CLI is installed
if command -v gh &> /dev/null; then
    echo -e "${GREEN}✓ GitHub CLI detected${NC}"
    echo ""
    echo "Would you like to create the repository using GitHub CLI? (y/n)"
    read -p "Choice: " USE_GH_CLI
    
    if [[ $USE_GH_CLI =~ ^[Yy]$ ]]; then
        echo ""
        echo "Creating repository on GitHub..."
        
        # Check if logged in
        if ! gh auth status &> /dev/null; then
            echo -e "${YELLOW}⚠️  You need to login to GitHub first${NC}"
            echo "Running: gh auth login"
            gh auth login
        fi
        
        # Create repo
        echo "Creating repository..."
        gh repo create $REPO_NAME \
            --public \
            --description "Import networks from AWS, Azure, GCP into InfoBlox IPAM" \
            --source=. \
            --push \
            --remote=origin
        
        echo -e "${GREEN}✅ Repository created and pushed successfully!${NC}"
        echo ""
        echo "🎉 Your project is now live at:"
        echo "   https://github.com/$GITHUB_USERNAME/$REPO_NAME"
        exit 0
    fi
fi

# Manual method
echo ""
echo -e "${YELLOW}📋 Manual Setup Required:${NC}"
echo ""
echo "1. Open your browser and go to:"
echo "   ${GREEN}https://github.com/new${NC}"
echo ""
echo "2. Create a new repository with these settings:"
echo "   - Repository name: ${GREEN}$REPO_NAME${NC}"
echo "   - Description: Import networks from AWS, Azure, GCP into InfoBlox IPAM"
echo "   - Visibility: Public or Private (your choice)"
echo "   - ${RED}DO NOT${NC} initialize with README, .gitignore, or license"
echo ""
echo "3. Click 'Create repository'"
echo ""
echo -e "${YELLOW}Press ENTER when you've created the repository...${NC}"
read

# Add remote and push
echo ""
echo "Adding GitHub remote..."

# Check if origin already exists
if git remote | grep -q "^origin$"; then
    echo "Remote 'origin' already exists. Updating URL..."
    git remote set-url origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
else
    git remote add origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
fi

echo -e "${GREEN}✓ Remote added${NC}"

# Show current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Push to GitHub
echo ""
echo "Pushing to GitHub..."
echo ""

# Try to push
if git push -u origin $CURRENT_BRANCH; then
    echo ""
    echo -e "${GREEN}✅ Successfully pushed to GitHub!${NC}"
    echo ""
    echo "🎉 Your project is now live at:"
    echo "   https://github.com/$GITHUB_USERNAME/$REPO_NAME"
    echo ""
    echo "Next steps:"
    echo "- Add topics: infoblox, ipam, network-automation, python, fastapi"
    echo "- Star your own repository ⭐"
    echo "- Share with your team!"
else
    echo ""
    echo -e "${RED}❌ Push failed${NC}"
    echo ""
    echo "Common issues:"
    echo "1. Authentication failed - Check your GitHub credentials"
    echo "2. Repository doesn't exist - Make sure you created it"
    echo "3. Wrong repository name - Check the URL"
    echo ""
    echo "To try again manually:"
    echo "git push -u origin $CURRENT_BRANCH"
fi

echo ""
echo "📊 Repository Summary:"
echo "- URL: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo "- Branch: $CURRENT_BRANCH"
echo "- Commits: $(git rev-list --count HEAD)"
echo "- Files: $(git ls-files | wc -l)"
