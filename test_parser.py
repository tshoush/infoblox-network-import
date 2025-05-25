#!/usr/bin/env python3
"""
Test script to verify parsers work without InfoBlox connection
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.parsers import CloudNetworkParser
from rich.console import Console
from rich.table import Table

console = Console()

def test_parser(file_path: str, source_type: str):
    """Test parser without InfoBlox connection"""
    console.print(f"\n[cyan]Testing {source_type} parser with {file_path}[/cyan]\n")
    
    try:
        parser = CloudNetworkParser()
        networks = parser.parse_file(file_path, source_type)
        
        if not networks:
            console.print("[red]No networks parsed![/red]")
            return
        
        # Display results
        table = Table(title=f"Parsed {len(networks)} Networks")
        table.add_column("Name", style="cyan")
        table.add_column("Network", style="green")
        table.add_column("Description", style="yellow")
        table.add_column("Tags", style="magenta")
        
        for net in networks[:5]:  # Show first 5
            tags_str = ", ".join([f"{k}={v}" for k, v in list(net.tags.items())[:3]])
            if len(net.tags) > 3:
                tags_str += f" ... +{len(net.tags)-3} more"
            
            table.add_row(
                net.name,
                net.address,
                net.description[:50] + "..." if len(net.description) > 50 else net.description,
                tags_str
            )
        
        console.print(table)
        
        if len(networks) > 5:
            console.print(f"\n... and {len(networks) - 5} more networks\n")
        
        console.print(f"[green]✓ Parser test successful![/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Parser test failed: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test AWS parser
    test_parser("example_aws_networks.csv", "aws")
    
    # Test Properties parser
    test_parser("example_properties_networks.csv", "properties")
