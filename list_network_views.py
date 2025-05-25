#!/usr/bin/env python3
"""
List available network views in InfoBlox
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.infoblox import InfoBloxWAPI
from rich.console import Console
from rich.table import Table

console = Console()

def main():
    """List available network views"""
    
    try:
        console.print("[cyan]Connecting to InfoBlox...[/cyan]")
        api = InfoBloxWAPI()
        
        console.print("[green]✓[/green] Connected to InfoBlox Grid Master")
        console.print("Fetching network views...\n")
        
        # Get network views
        views = api.get_network_views()
        
        if not views:
            console.print("[yellow]No network views found[/yellow]")
            return
        
        # Display results
        table = Table(title=f"Available Network Views ({len(views)} total)")
        table.add_column("Name", style="cyan")
        table.add_column("Comment", style="yellow")
        table.add_column("Is Default", style="green")
        
        for view in views:
            table.add_row(
                view.get('name', ''),
                view.get('comment', '')[:50] + "..." if len(view.get('comment', '')) > 50 else view.get('comment', ''),
                "Yes" if view.get('is_default', False) else "No"
            )
        
        console.print(table)
        
        # Show current default from environment
        console.print(f"\n[dim]Current default from .env: {api.network_view}[/dim]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
