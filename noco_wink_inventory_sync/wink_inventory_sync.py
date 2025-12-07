#!/usr/bin/env python3
"""
Wink Inventory Synchronizer
Synchronizes product inventory between Wink API and NocoDB using UPC codes
"""

import os
import sys
import json
import logging
import requests
import time
import base64
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table

# Import from local module (nocodb_manager.py in same directory)
from noco_wink_inventory_sync.nocodb_manager import NocoDBManager

# Note: WebSocket manager can be imported when needed for real-time updates
# from backend.websocket_manager import manager



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()


class WinkInventorySync:
    """Synchronizes product inventory between Wink API and NocoDB"""
    
    def __init__(self, nocodb_manager: NocoDBManager, 
                 wink_api_base_url: str = "https://azurefd.downloadwink.com",
                 account_id: int = None,
                 username: str = None,
                 password: str = None,
                 store_id: int = None):
        """
        Initialize Wink Inventory Sync
        
        Args:
            nocodb_manager: NocoDBManager instance for database operations
            wink_api_base_url: Base URL for Wink API
            account_id: Wink account ID (or from env WINK_ACCOUNT_ID)
            username: Wink username (or from env WINK_USERNAME)
            password: Wink password (or from env WINK_PASSWORD)
            store_id: Wink store ID (or from env WINK_STORE_ID, default: 1)
        """
        self.nocodb = nocodb_manager
        self.wink_api_base_url = wink_api_base_url
        self.wink_product_endpoint_template = f"{wink_api_base_url}/Web/Product"  # Will append /{wink_id}
        self.wink_login_endpoint = f"{wink_api_base_url}/Web/login/doctors"
        
        # Get credentials from parameters or environment variables
        self.account_id = account_id or int(os.getenv('WINK_ACCOUNT_ID', '0'))
        self.username = username or os.getenv('WINK_USERNAME', '')
        self.password = password or os.getenv('WINK_PASSWORD', '')
        self.store_id = store_id or int(os.getenv('WINK_STORE_ID', '1'))
        
        # Validate required credentials
        if not self.username or not self.password or not self.account_id:
            raise ValueError(
                "Missing Wink API credentials. Please set the following environment variables:\n"
                "  - WINK_ACCOUNT_ID\n"
                "  - WINK_USERNAME\n"
                "  - WINK_PASSWORD"
            )
        
        # Session for authenticated requests
        self.session = requests.Session()
        self.token = None
        self._authenticated = False
        
        # Store mapping: {store_id: store_name} - Hardcoded
        self.store_id_to_name = {
            '1': 'Niagara Falls',
            '10': 'Niagara On The Lake',
            '8': 'St. Catharines',
            '11': 'Welland'
        }
        
        logger.info(f"Initialized WinkInventorySync with API endpoint template: {self.wink_product_endpoint_template}/{{wink_id}}")
        logger.info(f"Using hardcoded store mapping: {self.store_id_to_name}")
    
    def login(self) -> bool:
        """
        Authenticate with Wink API and get token
        
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Create Basic Auth header
            auth_string = f"{self.username}:{self.password}"
            base64_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Basic {base64_auth}",
                "Accept-Language": "en"
            }
            
            login_data = {
                "accountsId": str(self.account_id),
                "storeId": str(self.store_id),
                "expiration": "24",
                "thirdParty": True
            }
            
            console.print("[cyan]Authenticating with Wink API...[/cyan]")
            login_response = self.session.post(self.wink_login_endpoint, headers=headers, json=login_data, timeout=30)
            
            if login_response.status_code == 200:
                self.token = login_response.headers.get('token')
                if self.token:
                    # Update session headers with token
                    self.session.headers.update({
                        "Token": self.token,
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    })
                    self._authenticated = True
                    logger.info("Successfully authenticated with Wink API")
                    console.print("[green]✓[/green] Authenticated with Wink API")
                    return True
                else:
                    logger.error("Login successful but no token received")
                    console.print("[red]✗[/red] Login failed: No token received")
                    return False
            else:
                logger.error(f"Login failed with status {login_response.status_code}: {login_response.text}")
                console.print(f"[red]✗[/red] Login failed: {login_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error during Wink API login: {e}")
            console.print(f"[red]✗[/red] Login error: {e}")
            return False
    
    
    def fetch_records_with_wink_id(self) -> List[Dict[str, Any]]:
        """
        Fetch all records from NocoDB where 'Wink Id' is not empty
        
        Returns:
            List of records with Wink Id
        """
        console.print("\n[cyan]Fetching records with Wink Id from NocoDB...[/cyan]")
        
        all_records = []
        page = 1
        limit = 1000  # NocoDB default limit
        
        try:
            while True:
                offset = (page - 1) * limit
                query_url = f"{self.nocodb.api_url}?limit={limit}&offset={offset}"
                
                response = requests.get(query_url, headers=self.nocodb.headers, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    records = result.get('list', [])
                    
                    if not records:
                        break
                    
                    # Filter records where 'Wink Id' is not empty
                    for record in records:
                        wink_id = record.get('Wink Id', '') or record.get('Wink ID', '') or record.get('wink_id', '') or record.get('WinkId', '')
                        if wink_id and str(wink_id).strip():
                            all_records.append(record)
                    
                    # Check if there are more pages
                    page_info = result.get('pageInfo', {})
                    if page_info.get('isLastPage', False):
                        break
                    
                    page += 1
                    time.sleep(0.1)  # Rate limiting
                else:
                    logger.error(f"Failed to fetch records: {response.status_code}")
                    break
            
            logger.info(f"Found {len(all_records)} records with Wink Id")
            console.print(f"[green]✓[/green] Found {len(all_records)} records with Wink Id")
            
        except Exception as e:
            logger.error(f"Error fetching records with Wink Id: {e}")
            console.print(f"[red]✗[/red] Error fetching records: {e}")
        
        return all_records
    
    def normalize_upc_for_wink(self, upc: str, is_safilo: bool = False) -> str:
        """
        Normalize UPC code for Wink API query
        For Safilo UPCs, remove leading zeros
        
        Args:
            upc: Original UPC code
            is_safilo: Whether this UPC is from Safilo
            
        Returns:
            Normalized UPC code
        """
        if not upc:
            return upc
        
        upc_str = str(upc).strip()
        
        # Remove leading zeros for Safilo UPCs
        if is_safilo:
            normalized = upc_str.lstrip('0')
            # Ensure we don't remove all zeros (keep at least one if original was all zeros)
            if not normalized:
                normalized = '0'
            logger.debug(f"Normalized Safilo UPC: '{upc_str}' -> '{normalized}'")
            return normalized
        
        return upc_str
    
    def get_wink_inventory(self, wink_id: str) -> Optional[Dict[str, Any]]:
        """
        Get product data from Wink API for a given Wink Id (includes inventory information)
        
        Args:
            wink_id: Wink Id from NocoDB record
            
        Returns:
            Dictionary with product/inventory data or None if not found/error
        """
        # Ensure we're authenticated
        if not self._authenticated:
            if not self.login():
                logger.error("Cannot get Wink inventory: Authentication failed")
                return None
        
        try:
            # Use Wink Id directly in the URL path
            url = f"{self.wink_product_endpoint_template}/{wink_id}"
            
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                # The response might be a single product object or a list
                product_data = None
                if isinstance(data, list) and len(data) > 0:
                    product_data = data[0]  # Return first product if it's a list
                elif isinstance(data, dict):
                    product_data = data
                else:
                    logger.debug(f"Wink Id {wink_id} returned empty response")
                    return None
                
                return product_data
            elif response.status_code == 404:
                logger.debug(f"Wink Id {wink_id} not found in Wink API (404)")
                return None
            elif response.status_code == 429:
                # Rate limit exceeded
                retry_after = response.headers.get('Retry-After', '60')
                try:
                    retry_seconds = int(retry_after)
                except ValueError:
                    retry_seconds = 60  # Default to 60 seconds if header is invalid
                
                logger.warning(f"Rate limit exceeded for Wink Id {wink_id}. Retry after {retry_seconds} seconds.")
                # Return a special marker to indicate rate limit (don't save empty {})
                return {'_rate_limited': True, '_retry_after': retry_seconds}
            else:
                logger.warning(f"Wink API returned status {response.status_code} for Wink Id {wink_id}")
                # If we get 401, try to re-authenticate once
                if response.status_code == 401:
                    logger.info("Token expired, attempting to re-authenticate...")
                    if self.login():
                        # Retry the request
                        response = self.session.get(url, timeout=30)
                        if response.status_code == 200:
                            data = response.json()
                            if isinstance(data, list) and len(data) > 0:
                                return data[0]
                            elif isinstance(data, dict):
                                return data
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Wink API for Wink Id {wink_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting Wink inventory for Wink Id {wink_id}: {e}")
            return None
    
    def parse_inventory_response(self, wink_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Wink API product response to extract location inventory and compute stock status
        
        Args:
            wink_data: Raw product response from Wink API (from /Web/Product/{wink_id})
            
        Returns:
            Dictionary with:
                - location_inventory: Dict mapping location names to quantities
                - total_stock: Total units across all locations
                - stock_status: "in_stock", "low_stock", or "out_of_stock"
        """
        location_inventory = {}
        total_stock = 0
        
        # Parse the response structure from Wink Product API
        if isinstance(wink_data, dict):
            # Check if product has inventory field (could be array or dict)
            inventory_data = wink_data.get('inventory')
            
            # Log the structure of inventory data for debugging
            if inventory_data:
                logger.debug(f"Inventory data type: {type(inventory_data)}, value: {inventory_data}")
            
            if inventory_data:
                # If inventory is a list of location objects
                if isinstance(inventory_data, list):
                    for item in inventory_data:
                        if isinstance(item, dict):
                            store_id = str(item.get('store') or '')
                            quantity = item.get('qty')
                            
                            if store_id:
                                try:
                                    quantity = int(quantity) if quantity else 0
                                    # Map store ID to store name
                                    store_name = self.store_id_to_name.get(store_id, store_id)
                                    location_inventory[store_name] = quantity
                                    total_stock += quantity
                                except (ValueError, TypeError):
                                    logger.warning(f"Invalid quantity for store {store_id}: {quantity}")
                
                # If inventory is a dict mapping store IDs to quantities
                elif isinstance(inventory_data, dict):
                    for store_id, quantity in inventory_data.items():
                        try:
                            quantity = int(quantity) if quantity else 0
                            if quantity >= 0:
                                # Map store ID to store name
                                store_name = self.store_id_to_name.get(str(store_id), str(store_id))
                                location_inventory[store_name] = quantity
                                total_stock += quantity
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid quantity for store {store_id}: {quantity}")
            
            # Check if product has locations array with inventory info
            locations = wink_data.get('locations') or wink_data.get('stores')
            if locations and isinstance(locations, list):
                for location in locations:
                    if isinstance(location, dict):
                        location_name = (location.get('name') or location.get('storeName') or 
                                       location.get('location') or location.get('store_name') or '')
                        quantity = (location.get('quantity') or location.get('qty') or 
                                  location.get('stock') or location.get('available') or 
                                  location.get('onHand') or 0)
                        
                        if location_name:
                            try:
                                quantity = int(quantity) if quantity else 0
                                location_inventory[str(location_name)] = quantity
                                total_stock += quantity
                            except (ValueError, TypeError):
                                logger.warning(f"Invalid quantity for location {location_name}: {quantity}")
            
            # Check for direct inventory fields (total stock)
            if not location_inventory:
                # Try to get total inventory if location-specific data not available
                total_inv = (wink_data.get('totalInventory') or wink_data.get('total_inventory') or 
                           wink_data.get('stock') or wink_data.get('quantity') or 0)
                try:
                    total_inv = int(total_inv) if total_inv else 0
                    if total_inv > 0:
                        # If we only have total, store it as "Total" location
                        location_inventory['Total'] = total_inv
                        total_stock = total_inv
                except (ValueError, TypeError):
                    pass
        
        # Log parsed data for debugging
        if location_inventory:
            logger.debug(f"Parsed inventory: {location_inventory} (total: {total_stock})")
        else:
            # Enhanced logging to help debug why inventory is empty
            if isinstance(wink_data, dict):
                available_keys = list(wink_data.keys())
                logger.warning(f"Could not parse inventory from Wink response. Available keys: {available_keys}")
                # Check for common inventory field names
                if 'inventory' in wink_data:
                    inv_value = wink_data.get('inventory')
                    logger.warning(f"  - 'inventory' field exists but is empty or invalid:")
                    logger.warning(f"    Type: {type(inv_value)}, Value: {inv_value}")
                    if isinstance(inv_value, list):
                        logger.warning(f"    List length: {len(inv_value)}, First item: {inv_value[0] if inv_value else 'N/A'}")
                    elif isinstance(inv_value, dict):
                        logger.warning(f"    Dict keys: {list(inv_value.keys())}, Sample: {dict(list(inv_value.items())[:3])}")
                if 'locations' in wink_data:
                    logger.warning(f"  - 'locations' field exists: {wink_data.get('locations')}")
                if 'stores' in wink_data:
                    logger.warning(f"  - 'stores' field exists: {wink_data.get('stores')}")
            else:
                logger.warning(f"Could not parse inventory: Wink response is not a dictionary (type: {type(wink_data)})")
        
        # Determine stock status
        if total_stock == 0:
            stock_status = "out_of_stock"
        elif total_stock <= 2:
            stock_status = "low_stock"
        else:
            stock_status = "in_stock"
        
        return {
            'location_inventory': location_inventory,
            'total_stock': total_stock,
            'stock_status': stock_status
        }
    
    def update_nocodb_record(self, record_id: str, stock_status: str, location_inventory: Dict[str, int]) -> bool:
        """
        Update NocoDB record with Wink inventory data
        
        Args:
            record_id: NocoDB record ID
            stock_status: Stock status string (in_stock, low_stock, out_of_stock, not_found)
            location_inventory: Dictionary mapping location names to quantities
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                'Wink Stock Status': stock_status,
                'Wink Location Inventory': json.dumps(location_inventory) if location_inventory else '{}'
            }
            
            result = self.nocodb._update_record(record_id, update_data)
            
            if result:
                logger.debug(f"Updated record {record_id} with stock status: {stock_status}")
                return True
            else:
                logger.warning(f"Failed to update record {record_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating NocoDB record {record_id}: {e}")
            return False
    
    def sync_inventory(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Main method to synchronize inventory from Wink to NocoDB
        
        Args:
            limit: Optional limit on number of records to process (for testing)
            
        Returns:
            Dictionary with sync statistics
        """
        console.print("\n[bold cyan]Starting Wink Inventory Synchronization[/bold cyan]")
        
        # Authenticate first
        if not self.login():
            console.print("[red]✗[/red] Failed to authenticate with Wink API. Cannot proceed with sync.")
            return {
                'total_records': 0,
                'processed': 0,
                'updated': 0,
                'not_found': 0,
                'errors': 1,
                'in_stock': 0,
                'low_stock': 0,
                'out_of_stock': 0
            }
        
        # Store names are hardcoded (no API call needed)
        console.print(f"\n[cyan]Using hardcoded store mapping: {len(self.store_id_to_name)} stores[/cyan]")
        logger.info(f"Store mapping: {self.store_id_to_name}")
        
        stats = {
            'total_records': 0,
            'processed': 0,
            'updated': 0,
            'not_found': 0,
            'errors': 0,
            'in_stock': 0,
            'low_stock': 0,
            'out_of_stock': 0
        }
        
        # Fetch records with Wink Id
        records = self.fetch_records_with_wink_id()
        
        if not records:
            console.print("[yellow]No records with Wink Id found[/yellow]")
            return stats
        
        stats['total_records'] = len(records)
        
        # Apply limit if specified
        if limit:
            records = records[:limit]
            console.print(f"[yellow]TEST MODE: Processing first {limit} records[/yellow]")
        
        # Process records with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Syncing inventory...", total=len(records))
            
            for record in records:
                record_id = record.get('Id') or record.get('id')
                wink_id = record.get('Wink Id', '') or record.get('Wink ID', '') or record.get('wink_id', '') or record.get('WinkId', '')
                
                if not record_id or not wink_id:
                    stats['errors'] += 1
                    progress.update(task, advance=1)
                    continue
                
                try:
                    # Get inventory from Wink API using Wink Id
                    wink_id_str = str(wink_id).strip()
                    wink_data = self.get_wink_inventory(wink_id_str)
                    
                    # Check for rate limiting
                    if wink_data and isinstance(wink_data, dict) and wink_data.get('_rate_limited'):
                        retry_after = wink_data.get('_retry_after', 60)
                        logger.warning(f"Rate limit hit. Waiting {retry_after} seconds before continuing...")
                        console.print(f"[yellow]⚠ Rate limit exceeded. Waiting {retry_after} seconds...[/yellow]")
                        time.sleep(retry_after)
                        # Retry this record
                        wink_data = self.get_wink_inventory(wink_id_str)
                    
                    if wink_data and not (isinstance(wink_data, dict) and wink_data.get('_rate_limited')):
                        # Parse inventory data
                        inventory_info = self.parse_inventory_response(wink_data)
                        
                        # Check if we got valid inventory data
                        location_inventory = inventory_info['location_inventory']
                        if not location_inventory:
                            logger.warning(f"Wink Id {wink_id_str}: Parsed inventory is empty. This may indicate the product has no stock or the API response structure is unexpected.")
                            # Still update with empty inventory to mark that we checked
                        
                        # Update NocoDB record
                        success = self.update_nocodb_record(
                            str(record_id),
                            inventory_info['stock_status'],
                            location_inventory
                        )
                        
                        if success:
                            stats['updated'] += 1
                            stats[inventory_info['stock_status']] += 1
                            if location_inventory:
                                logger.debug(f"Updated Wink Id {wink_id_str}: {inventory_info['stock_status']} (total: {inventory_info['total_stock']}, locations: {location_inventory})")
                            else:
                                logger.debug(f"Updated Wink Id {wink_id_str}: {inventory_info['stock_status']} (no inventory data)")
                        else:
                            stats['errors'] += 1
                    elif wink_data and isinstance(wink_data, dict) and wink_data.get('_rate_limited'):
                        # Still rate limited after retry - skip this record for now
                        logger.warning(f"Still rate limited for Wink Id {wink_id_str} after retry. Skipping this record.")
                        stats['errors'] += 1
                    else:
                        # Not found in Wink API
                        success = self.update_nocodb_record(
                            str(record_id),
                            "not_found",
                            {}
                        )
                        
                        if success:
                            stats['updated'] += 1
                            stats['not_found'] += 1
                        else:
                            stats['errors'] += 1
                    
                    stats['processed'] += 1
                    
                    # Rate limiting - be nice to the API
                    # Increased delay to reduce rate limit issues
                    time.sleep(0.5)  # Increased from 0.2 to 0.5 seconds
                    
                except Exception as e:
                    logger.error(f"Error processing record {record_id} (Wink Id: {wink_id}): {e}")
                    stats['errors'] += 1
                
                progress.update(task, advance=1)
        
        return stats
    
    def display_sync_results(self, stats: Dict[str, Any]):
        """
        Display synchronization results in a formatted table
        
        Args:
            stats: Statistics dictionary from sync_inventory()
        """
        console.print("\n")
        results_table = Table(title="Wink Inventory Sync Results", show_header=True, header_style="bold cyan")
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="green", justify="right")
        
        results_table.add_row("Total Records", str(stats['total_records']))
        results_table.add_row("Processed", str(stats['processed']))
        results_table.add_row("Updated", str(stats['updated']))
        results_table.add_row("Not Found", str(stats['not_found']))
        results_table.add_row("Errors", str(stats['errors']))
        results_table.add_row("", "")  # Separator
        results_table.add_row("In Stock", str(stats['in_stock']))
        results_table.add_row("Low Stock", str(stats['low_stock']))
        results_table.add_row("Out of Stock", str(stats['out_of_stock']))
        
        console.print(results_table)


def main():
    """Main entry point for standalone execution"""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
    
    try:
        # Initialize NocoDB manager
        nocodb_config = {
            'api_token': os.getenv('NOCODB_API_TOKEN', ''),
            'base_url': os.getenv('NOCODB_BASE_URL', ''),
            'project_name': os.getenv('NOCODB_PROJECT_NAME', ''),
            'table_name': os.getenv('NOCODB_TABLE_NAME', '')
        }
        
        if not all(nocodb_config.values()):
            console.print("[red]Missing NocoDB configuration. Set NOCODB_API_TOKEN, NOCODB_BASE_URL, NOCODB_PROJECT_NAME, and NOCODB_TABLE_NAME environment variables.[/red]")
            return 1
        
        nocodb_manager = NocoDBManager(
            api_token=nocodb_config['api_token'],
            base_url=nocodb_config['base_url'],
            project_name=nocodb_config['project_name'],
            table_name=nocodb_config['table_name']
        )
        
        # Initialize Wink sync
        wink_sync = WinkInventorySync(nocodb_manager)
        
        # Run sync
        stats = wink_sync.sync_inventory()
        
        # Display results
        wink_sync.display_sync_results(stats)
        
        return 0 if stats['errors'] == 0 else 1
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        logger.exception("Fatal error occurred")
        return 1


if __name__ == "__main__":
    sys.exit(main())

