#!/usr/bin/env python3
"""
List networks currently in InfoBlox
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.infoblox import InfoBloxWAPI
from rich.console import Console
from rich.table import Table
import click

console = Console()

@click.command()
@click.option('--network-view', default='default', help='Network view to list')
@click.option('--max-results', default=100, help='Maximum results to display')
def list_networks(network_view, max_results):
    """List networks currently in InfoBlox"""
    
    try:
        console.print(f"[cyan]Connecting to InfoBlox...[/cyan]")
        api = InfoBloxWAPI()
        
        console.print(f"[green]✓[/green] Connected to InfoBlox Grid Master")
        console.print(f"Fetching networks from view: [cyan]{network_view}[/cyan]\n")
        
        # Get networks
        networks = api.search_networks(
            {"network_view": network_view},
            return_fields=['network', 'comment', 'extattrs'],
            max_results=max_results
        )
        
        if not networks:
            console.print("[yellow]No networks found[/yellow]")
            return
        
        # Display results
        table = Table(title=f"InfoBlox Networks in '{network_view}' view ({len(networks)} total)")
        table.add_column("Network", style="cyan")
        table.add_column("Comment", style="yellow")
        table.add_column("Extended Attributes", style="magenta")
        
        for net in networks:
            # Format extended attributes
            extattrs = net.get('extattrs', {})
            ea_list = []
            for ea_name, ea_value in extattrs.items():
                value = ea_value.get('value', '')
                ea_list.append(f"{ea_name}={value}")
            ea_str = ", ".join(ea_list[:3])
            if len(ea_list) > 3:
                ea_str += f" (+{len(ea_list)-3} more)"
            
            table.add_row(
                net.get('network', ''),
                net.get('comment', '')[:50] + "..." if len(net.get('comment', '')) > 50 else net.get('comment', ''),
                ea_str
            )
        
        console.print(table)
        
        if len(networks) == max_results:
            console.print(f"\n[yellow]Note: Results limited to {max_results}. Use --max-results to see more.[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    list_networks()
