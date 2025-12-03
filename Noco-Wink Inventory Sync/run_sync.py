#!/usr/bin/env python3
"""
Wink to NocoDB Inventory Synchronization Script
Standalone script to sync inventory data from Wink API to NocoDB
"""

import os
import sys
import logging
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

# Add current directory to path for local imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import from local modules (copied to this folder for standalone operation)
from nocodb_manager import NocoDBManager
from wink_inventory_sync import WinkInventorySync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()


def main():
    """Main entry point for Wink inventory sync"""
    
    # Load environment variables from project root (parent directory)
    project_root = os.path.dirname(script_dir)
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        console.print(f"[green]✓[/green] Loaded environment variables from {env_path}")
    else:
        console.print(f"[yellow]⚠[/yellow] No .env file found at {env_path}")
    
    console.print(Panel(
        "[bold blue]Wink to NocoDB Inventory Synchronization[/bold blue]\n"
        "This script syncs product inventory from Wink API to NocoDB\n\n"
        "Configuration:\n"
        "- Wink API: https://azurefd.downloadwink.com\n"
        "- Updates: Wink Stock Status, Wink Location Inventory",
        title="Inventory Sync",
        border_style="blue"
    ))
    
    try:
        # Initialize NocoDB manager
        nocodb_config = {
            'api_token': os.getenv('NOCODB_API_TOKEN', ''),
            'base_url': os.getenv('NOCODB_BASE_URL', ''),
            'project_name': os.getenv('NOCODB_PROJECT_NAME', ''),
            'table_name': os.getenv('NOCODB_TABLE_NAME', '')
        }
        
        if not all(nocodb_config.values()):
            console.print("[red]✗ Missing NocoDB configuration![/red]")
            console.print("\nRequired environment variables:")
            console.print("  - NOCODB_API_TOKEN")
            console.print("  - NOCODB_BASE_URL")
            console.print("  - NOCODB_PROJECT_NAME")
            console.print("  - NOCODB_TABLE_NAME")
            return 1
        
        console.print(f"\n[cyan]Connecting to NocoDB...[/cyan]")
        console.print(f"  Project: {nocodb_config['project_name']}")
        console.print(f"  Table: {nocodb_config['table_name']}")
        
        nocodb_manager = NocoDBManager(
            api_token=nocodb_config['api_token'],
            base_url=nocodb_config['base_url'],
            project_name=nocodb_config['project_name'],
            table_name=nocodb_config['table_name']
        )
        
        # Initialize Wink sync
        console.print(f"\n[cyan]Initializing Wink API connection...[/cyan]")
        wink_sync = WinkInventorySync(nocodb_manager)
        
        # Run sync
        console.print("\n" + "="*80)
        wink_stats = wink_sync.sync_inventory()
        console.print("="*80)
        
        # Display results
        wink_sync.display_sync_results(wink_stats)
        console.print("\n[green]✓[/green] Wink inventory sync completed successfully!")
        
        # Return exit code based on errors
        return 0 if wink_stats['errors'] == 0 else 1
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Interrupted by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[red]✗ Fatal error: {e}[/red]")
        logger.exception("Fatal error occurred")
        return 1


if __name__ == "__main__":
    sys.exit(main())

