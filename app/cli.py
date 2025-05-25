"""
Command-line interface for InfoBlox Network Import
"""
import click
import os
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
import json
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.infoblox import InfoBloxWAPI
from app.core.parsers import CloudNetworkParser
from app.core.models import NetworkImportModel, EAMappingConfig

console = Console()


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """InfoBlox Network Import Tool
    
    Import networks from various cloud providers into InfoBlox IPAM.
    """
    pass


@cli.command()
@click.option('--file', '-f', required=True, type=click.Path(exists=True),
              help='Network file to import (CSV or Excel)')
@click.option('--source', '-s', required=True,
              type=click.Choice(['aws', 'azure', 'gcp', 'alibaba', 'properties', 'custom']),
              help='Source cloud provider')
@click.option('--dry-run', is_flag=True,
              help='Preview changes without applying them')
@click.option('--no-confirm', is_flag=True,
              help='Skip confirmation prompt')
@click.option('--mapping-file', '-m', type=click.Path(exists=True),
              help='EA mapping configuration file (JSON)')
@click.option('--network-view', default='default',
              help='InfoBlox network view to use')
def import_networks(file, source, dry_run, no_confirm, mapping_file, network_view):
    """Import networks from a file into InfoBlox"""
    
    console.print(f"[cyan]InfoBlox Network Import[/cyan]")
    console.print(f"[dim]Source: {source} | File: {file}[/dim]\n")
    
    # Initialize InfoBlox API
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Connecting to InfoBlox...", total=None)
            api = InfoBloxWAPI()
            progress.update(task, completed=100)
        
        console.print("[green]✓[/green] Connected to InfoBlox Grid Master")
    except Exception as e:
        console.print(f"[red]✗ Failed to connect to InfoBlox: {e}[/red]")
        return
    
    # Parse file
    try:
        parser = CloudNetworkParser()
        networks = parser.parse_file(file, source)
        console.print(f"[green]✓[/green] Parsed {len(networks)} networks from file")
    except Exception as e:
        console.print(f"[red]✗ Error parsing file: {e}[/red]")
        return
    
    # Load EA mappings if provided
    ea_mappings = []
    if mapping_file:
        try:
            with open(mapping_file, 'r') as f:
                mapping_data = json.load(f)
                ea_mappings = [EAMappingConfig(**m) for m in mapping_data.get('mappings', [])]
            console.print(f"[green]✓[/green] Loaded {len(ea_mappings)} EA mappings")
        except Exception as e:
            console.print(f"[yellow]⚠ Warning: Failed to load mapping file: {e}[/yellow]")
    
    # Analyze changes
    console.print("\n[cyan]Analyzing changes...[/cyan]")
    analysis = analyze_network_changes(api, networks, network_view)
    
    # Display preview
    display_analysis(analysis)
    
    if dry_run:
        console.print("\n[yellow]Dry run mode - no changes will be applied[/yellow]")
        return
    
    # Confirm changes
    if not no_confirm and (analysis['new_networks'] or analysis['updated_networks']):
        if not Confirm.ask("\nProceed with import?"):
            console.print("[red]Import cancelled[/red]")
            return
    
    # Execute import
    if analysis['new_networks'] or analysis['updated_networks']:
        execute_import(api, analysis, ea_mappings, network_view)
    else:
        console.print("\n[yellow]No changes to apply[/yellow]")


def analyze_network_changes(api: InfoBloxWAPI, networks: list, network_view: str) -> dict:
    """Analyze what changes would be made"""
    analysis = {
        'new_networks': [],
        'updated_networks': [],
        'overlapping_networks': [],
        'errors': []
    }
    
    with Progress(console=console) as progress:
        task = progress.add_task("Analyzing networks...", total=len(networks))
        
        for network in networks:
            try:
                # Check if network exists
                existing = api.get_network(network.address, network_view,
                                         return_fields=['network', 'comment', 'extattrs'])
                
                if existing:
                    # Check for differences
                    if has_changes(existing, network):
                        analysis['updated_networks'].append({
                            'network': network,
                            'existing': existing
                        })
                else:
                    # Check for overlaps
                    overlaps = api.check_network_overlaps(network.address, network_view)
                    if overlaps:
                        analysis['overlapping_networks'].append({
                            'network': network,
                            'overlaps': overlaps
                        })
                    else:
                        analysis['new_networks'].append(network)
                        
            except Exception as e:
                analysis['errors'].append({
                    'network': network.address,
                    'error': str(e)
                })
            
            progress.update(task, advance=1)
    
    return analysis


def has_changes(existing: dict, new: NetworkImportModel) -> bool:
    """Check if network has changes"""
    # Check comment
    if existing.get('comment', '') != new.description:
        return True
    
    # Check extended attributes - simplified check
    existing_eas = existing.get('extattrs', {})
    for tag_key, tag_value in new.tags.items():
        if tag_key not in existing_eas or existing_eas[tag_key].get('value') != tag_value:
            return True
    
    return False


def display_analysis(analysis: dict):
    """Display analysis results in a table"""
    # Summary table
    table = Table(title="Import Analysis Summary")
    table.add_column("Category", style="cyan")
    table.add_column("Count", style="green")
    
    table.add_row("New Networks", str(len(analysis['new_networks'])))
    table.add_row("Updated Networks", str(len(analysis['updated_networks'])))
    table.add_row("Overlapping Networks", str(len(analysis['overlapping_networks'])))
    table.add_row("Errors", str(len(analysis['errors'])))
    
    console.print(table)
    
    # Details for each category
    if analysis['new_networks']:
        console.print("\n[bold cyan]New Networks to Create:[/bold cyan]")
        for net in analysis['new_networks'][:5]:  # Show first 5
            console.print(f"  • {net.address} - {net.name}")
        if len(analysis['new_networks']) > 5:
            console.print(f"  ... and {len(analysis['new_networks']) - 5} more")
    
    if analysis['overlapping_networks']:
        console.print("\n[bold yellow]Overlapping Networks (will be skipped):[/bold yellow]")
        for item in analysis['overlapping_networks'][:5]:
            net = item['network']
            overlaps = item['overlaps']
            console.print(f"  • {net.address} overlaps with {len(overlaps)} existing network(s)")
    
    if analysis['errors']:
        console.print("\n[bold red]Errors:[/bold red]")
        for error in analysis['errors'][:5]:
            console.print(f"  • {error['network']}: {error['error']}")


def execute_import(api: InfoBloxWAPI, analysis: dict, ea_mappings: list, network_view: str):
    """Execute the import operation"""
    console.print("\n[cyan]Executing import...[/cyan]")
    
    results = {
        'created': 0,
        'updated': 0,
        'failed': 0
    }
    
    with Progress(console=console) as progress:
        # Process new networks
        if analysis['new_networks']:
            task = progress.add_task("Creating networks...", total=len(analysis['new_networks']))
            
            for network in analysis['new_networks']:
                try:
                    # Map tags to EAs
                    extattrs = map_tags_to_eas(network, ea_mappings)
                    
                    # Create EA definitions if needed
                    for ea_name in extattrs:
                        try:
                            api.create_ea_definition(ea_name, "STRING")
                        except:
                            pass  # EA might already exist
                    
                    # Create network
                    api.create_network(
                        network.address,
                        network_view=network_view,
                        comment=network.description,
                        extattrs=extattrs
                    )
                    results['created'] += 1
                    
                except Exception as e:
                    console.print(f"[red]Failed to create {network.address}: {e}[/red]")
                    results['failed'] += 1
                
                progress.update(task, advance=1)
        
        # Process updated networks
        if analysis['updated_networks']:
            task = progress.add_task("Updating networks...", total=len(analysis['updated_networks']))
            
            for item in analysis['updated_networks']:
                network = item['network']
                existing = item['existing']
                
                try:
                    # Map tags to EAs
                    extattrs = map_tags_to_eas(network, ea_mappings)
                    
                    # Update network
                    updates = {
                        'comment': network.description,
                        'extattrs': extattrs
                    }
                    api.update_network(existing['_ref'], updates)
                    results['updated'] += 1
                    
                except Exception as e:
                    console.print(f"[red]Failed to update {network.address}: {e}[/red]")
                    results['failed'] += 1
                
                progress.update(task, advance=1)
    
    # Display results
    console.print("\n[bold green]Import Complete![/bold green]")
    console.print(f"Created: {results['created']} networks")
    console.print(f"Updated: {results['updated']} networks")
    if results['failed'] > 0:
        console.print(f"[red]Failed: {results['failed']} networks[/red]")


def map_tags_to_eas(network: NetworkImportModel, mappings: list) -> dict:
    """Map network tags to InfoBlox Extended Attributes"""
    eas = {}
    
    # Apply configured mappings
    for mapping in mappings:
        value = network.tags.get(mapping.source_tag, mapping.default_value)
        
        if value and mapping.transform:
            if mapping.transform == 'uppercase':
                value = value.upper()
            elif mapping.transform == 'lowercase':
                value = value.lower()
            elif mapping.transform.startswith('prefix:'):
                prefix = mapping.transform.split(':', 1)[1]
                value = f"{prefix}{value}"
        
        if value:
            eas[mapping.target_ea] = {"value": str(value)}
    
    # Add default attributes
    eas["Import Source"] = {"value": network.source}
    eas["Import Date"] = {"value": pd.Timestamp.now().isoformat()}
    
    # Add all tags if no specific mappings
    if not mappings:
        for key, value in network.tags.items():
            ea_name = key.replace(' ', '_').replace('-', '_')
            eas[ea_name] = {"value": str(value)}
    
    return eas


@cli.command()
@click.option('--source', '-s', type=click.Choice(['aws', 'azure', 'gcp', 'alibaba', 'properties']),
              help='Source cloud provider for template')
@click.option('--output', '-o', default='ea_mappings.json',
              help='Output file for mapping template')
def generate_mapping_template(source, output):
    """Generate EA mapping template file"""
    
    templates = {
        'aws': [
            {"source_tag": "Name", "target_ea": "Name", "ea_type": "STRING"},
            {"source_tag": "Environment", "target_ea": "Environment", "ea_type": "STRING"},
            {"source_tag": "AWS_AccountId", "target_ea": "AWS Account", "ea_type": "STRING"},
            {"source_tag": "AWS_Region", "target_ea": "AWS Region", "ea_type": "STRING"},
            {"source_tag": "AWS_VpcId", "target_ea": "AWS VPC ID", "ea_type": "STRING"},
        ],
        'azure': [
            {"source_tag": "Name", "target_ea": "Name", "ea_type": "STRING"},
            {"source_tag": "Environment", "target_ea": "Environment", "ea_type": "STRING"},
            {"source_tag": "ResourceGroup", "target_ea": "Azure RG", "ea_type": "STRING"},
        ],
        'properties': [
            {"source_tag": "Environment", "target_ea": "Environment", "ea_type": "STRING"},
            {"source_tag": "Owner", "target_ea": "Network_Owner", "ea_type": "STRING"},
            {"source_tag": "Department", "target_ea": "Department", "ea_type": "STRING"},
            {"source_tag": "Cost_Center", "target_ea": "Cost_Center", "ea_type": "STRING"},
            {"source_tag": "Site_Type", "target_ea": "Site_Type", "ea_type": "ENUM", 
             "list_values": ["Office", "Branch", "Datacenter", "Lab", "Cloud"]},
            {"source_tag": "Compliance", "target_ea": "Compliance", "ea_type": "ENUM",
             "list_values": ["GDPR", "HIPAA", "PCI-DSS", "SOC2", "None"]},
        ]
    }
    
    template = {
        "description": f"EA mapping configuration for {source or 'all'} networks",
        "mappings": templates.get(source, templates['aws'])
    }
    
    with open(output, 'w') as f:
        json.dump(template, f, indent=2)
    
    console.print(f"[green]✓[/green] Generated mapping template: {output}")


@cli.command()
@click.option('--output', '-o', default='network_report.html',
              help='Output file for report')
@click.option('--format', '-f', type=click.Choice(['html', 'json', 'csv']),
              default='html', help='Report format')
def report_missing(output, format):
    """Generate report of networks missing from latest import"""
    
    console.print("[yellow]This feature requires tracking of previous imports[/yellow]")
    console.print("Please use the web interface for comprehensive reporting")


@cli.command()
def test_connection():
    """Test connection to InfoBlox Grid Master"""
    
    try:
        api = InfoBloxWAPI()
        grid_info = api.get_grid_info()
        
        console.print("[green]✓ Successfully connected to InfoBlox[/green]")
        console.print(f"Grid Master: {api.grid_master}")
        console.print(f"WAPI Version: {api.wapi_version}")
        
        if grid_info:
            console.print(f"Grid Name: {grid_info.get('name', 'N/A')}")
        
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")
        sys.exit(1)


@cli.command()
def list_eas():
    """List all Extended Attribute definitions"""
    
    try:
        api = InfoBloxWAPI()
        eas = api.list_ea_definitions()
        
        if not eas:
            console.print("[yellow]No Extended Attributes defined[/yellow]")
            return
        
        table = Table(title="InfoBlox Extended Attributes")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Comment")
        
        for ea in eas:
            table.add_row(
                ea.get('name', ''),
                ea.get('type', ''),
                ea.get('comment', '')
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


if __name__ == '__main__':
    cli()
