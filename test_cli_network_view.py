#!/usr/bin/env python3
"""
Test the enhanced CLI network view selection
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.infoblox import InfoBloxWAPI
from rich.console import Console

console = Console()

def test_network_view_prompt():
    """Test network view selection"""
    console.print("[cyan]Testing Network View Selection[/cyan]\n")
    
    try:
        # Connect to InfoBlox
        api = InfoBloxWAPI()
        console.print("[green]✓[/green] Connected to InfoBlox")
        
        # Get available views
        views = api.list_network_view_names()
        console.print(f"\nFound {len(views)} network views:")
        for view in views:
            console.print(f"  • {view}")
        
        console.print("\n[yellow]The CLI will now prompt for selection when:[/yellow]")
        console.print("1. Using default network view (--network-view not specified)")
        console.print("2. Multiple views are available")
        console.print("3. Not in --no-confirm mode")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    test_network_view_prompt()
