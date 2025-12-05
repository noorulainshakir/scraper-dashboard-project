#!/usr/bin/env python3
"""
Common NoCoDB Manager
Handles interactions with NoCoDB for both Luxottica and Safilo products
"""

import logging
import requests
from datetime import datetime
from typing import Dict, Optional, List, Any

logger = logging.getLogger(__name__)

class NocoDBManager:
    """Handles interactions with NoCoDB for both Luxottica and Safilo products"""

    def __init__(self, api_token: str, base_url: str, project_name: str, table_name: str):
        self.api_token = api_token
        self.base_url = base_url
        self.project_name = project_name
        self.table_name = table_name
        self.api_url = f"{self.base_url}/api/v1/db/data/noco/{self.project_name}/{self.table_name}"
        self.headers = {
            "xc-token": self.api_token,
            "Content-Type": "application/json"
        }

    def create_or_update_record(self, data: Dict) -> Optional[Dict]:
        """Create a new record or update existing record using UPC as unique identifier"""
        try:
            # Try to find existing record by UPC (unique identifier)
            upc = data.get('UPC / EAN', '')
            if upc:
                existing_record = self._find_record_by_upc(upc)
                if existing_record:
                    # Check if data has changed
                    if self._has_data_changed(existing_record, data):
                        # Update existing record
                        logger.info(f"Updating existing record for UPC: {upc}")
                        return self._update_record(existing_record['Id'], data)
                    else:
                        # No changes detected, skip update
                        logger.info(f"No changes detected for UPC: {upc}, skipping update")
                        return existing_record
            
            # Create new record if not found
            logger.info(f"Creating new record for UPC: {upc}")
            return self._create_record(data)
            
        except Exception as e:
            logger.error(f"An unexpected error occurred while creating/updating NoCoDB record: {e}")
            return None

    def _has_data_changed(self, existing_record: Dict, new_data: Dict) -> bool:
        """Compare existing record with new data to detect changes dynamically"""
        try:
            # Get all fields from both records (excluding system fields)
            system_fields = {'Id', 'id', 'created_at', 'updated_at', 'createdAt', 'updatedAt', 'Last Updated'}
            
            # Get all unique fields from both records
            all_fields = set(existing_record.keys()) | set(new_data.keys())
            
            # Remove system fields from comparison
            fields_to_compare = all_fields - system_fields
            
            for field in fields_to_compare:
                existing_value = existing_record.get(field)
                new_value = new_data.get(field)
                
                # Handle None vs empty string comparison
                if existing_value is None:
                    existing_value = ""
                if new_value is None:
                    new_value = ""
                
                # Convert to string for comparison
                existing_str = str(existing_value)
                new_str = str(new_value)
                
                if existing_str != new_str:
                    logger.debug(f"Field '{field}' changed: '{existing_str}' -> '{new_str}'")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error comparing data: {e}")
            # If comparison fails, assume data has changed to be safe
            return True

    def _create_record(self, data: Dict) -> Optional[Dict]:
        """Create a new record in the NoCoDB table"""
        try:
            logger.info(f"[DEBUG] NoCoDB: Attempting to create record for UPC: {data.get('UPC / EAN', 'Unknown')}")
            logger.info(f"[DEBUG] NoCoDB: API URL: {self.api_url}")
            logger.info(f"[DEBUG] NoCoDB: Headers: {self.headers}")
            
            # NoCoDB expects a flat structure, so we stringify complex fields
            payload = data
            
            logger.info(f"[DEBUG] NoCoDB: Payload keys: {list(payload.keys())}")
            
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            logger.info(f"[DEBUG] NoCoDB: Response status: {response.status_code}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"[DEBUG] NoCoDB: Success response: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create record in NoCoDB: {e}")
            if e.response is not None:
                logger.error(f"NoCoDB response status: {e.response.status_code}")
                logger.error(f"NoCoDB response text: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while creating NoCoDB record: {e}")
            return None

    def _update_record(self, record_id: str, data: Dict) -> Optional[Dict]:
        """Update an existing record in the NoCoDB table"""
        try:
            update_url = f"{self.api_url}/{record_id}"
            logger.info(f"[DEBUG] NoCoDB: Attempting to update record {record_id} for UPC: {data.get('UPC / EAN', 'Unknown')}")
            
            response = requests.patch(update_url, headers=self.headers, json=data, timeout=30)
            logger.info(f"[DEBUG] NoCoDB: Update response status: {response.status_code}")
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"[DEBUG] NoCoDB: Update success response: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update record in NoCoDB: {e}")
            if e.response is not None:
                logger.error(f"NoCoDB response status: {e.response.status_code}")
                logger.error(f"NoCoDB response text: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while updating NoCoDB record: {e}")
            return None

    def _find_record_by_upc(self, upc: str) -> Optional[Dict]:
        """Find a record by UPC / EAN field"""
        try:
            # Query NoCoDB to find record by UPC / EAN
            # URL encode the field name and value
            from urllib.parse import quote
            field_name = quote("UPC / EAN", safe='')
            encoded_upc = quote(str(upc), safe='')
            query_url = f"{self.api_url}?where=({field_name},eq,{encoded_upc})"
            response = requests.get(query_url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('list') and len(result['list']) > 0:
                    return result['list'][0]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find record by UPC: {e}")
            return None

    def create_record(self, data: Dict) -> Optional[Dict]:
        """Legacy method for backward compatibility - now calls create_or_update_record"""
        return self.create_or_update_record(data)

    def get_record_count(self) -> int:
        """Get the total count of records in the table"""
        try:
            response = requests.get(self.api_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            count = result.get('pageInfo', {}).get('totalRows', 0)
            logger.info(f"Total records in NoCoDB table: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to get record count: {e}")
            return 0

    def get_brands_table(self, brands_table_name: str = None) -> List[Dict]:
        """
        Read the brands table from NocoDB containing brand code, brand name, and scrape check.
        
        Args:
            brands_table_name: Optional override for the brands table name
            
        Returns:
            List of brand records with brand code, brand name, and scrape check
        """
        try:
            # Use provided table name or construct from current table
            if brands_table_name:
                brands_api_url = f"{self.base_url}/api/v1/db/data/noco/{self.project_name}/{brands_table_name}"
            else:
                # Try to construct brands table name from current table
                # Assuming if current table is 'products', brands table might be 'brands'
                current_table = self.table_name
                if 'product' in current_table.lower():
                    brands_table = current_table.replace('product', 'brand').replace('Product', 'Brand')
                else:
                    brands_table = 'brands'  # Default fallback
                brands_api_url = f"{self.base_url}/api/v1/db/data/noco/{self.project_name}/{brands_table}"
            
            logger.info(f"Fetching brands from: {brands_api_url}")
            
            # Get all records from brands table
            response = requests.get(brands_api_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            brands = data.get('list', [])
            
            logger.info(f"Successfully fetched {len(brands)} brand records")
            
            # Log the structure of the first record for debugging
            if brands:
                logger.info(f"Sample brand record structure: {list(brands[0].keys())}")
            
            return brands
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch brands table: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching brands table: {e}")
            return []

    def get_brands_lookup(self, brands_table_name: str = None) -> Dict[str, Dict]:
        """
        Get a lookup dictionary of brands by brand code.
        
        Args:
            brands_table_name: Optional override for the brands table name
            
        Returns:
            Dictionary with brand code as key and brand info as value
        """
        brands = self.get_brands_table(brands_table_name)
        lookup = {}
        
        for brand in brands:
            brand_code = brand.get('Brand Code') or brand.get('brand_code') or brand.get('BrandCode')
            if brand_code:
                lookup[brand_code] = {
                    'brand_name': brand.get('Brand Name') or brand.get('brand_name') or brand.get('BrandName'),
                    'scrape_check': brand.get('Scrape Check') or brand.get('scrape_check') or brand.get('ScrapeCheck'),
                    'enabled': brand.get('Enabled') or brand.get('enabled'),
                    'raw_data': brand
                }
        
        logger.info(f"Created brands lookup with {len(lookup)} brands")
        return lookup

    def get_enabled_brands(self, brands_table_name: str = None) -> List[str]:
        """
        Get list of brand codes that are enabled for scraping.
        
        Args:
            brands_table_name: Optional override for the brands table name
            
        Returns:
            List of enabled brand codes
        """
        brands_lookup = self.get_brands_lookup(brands_table_name)
        enabled_brands = []
        
        for brand_code, brand_info in brands_lookup.items():
            # Check if brand is enabled (scrape_check or enabled field)
            scrape_check = brand_info.get('scrape_check')
            enabled = brand_info.get('enabled')
            
            # Consider enabled if scrape_check is True or enabled is True
            if (scrape_check is True or enabled is True or 
                str(scrape_check).lower() == 'true' or 
                str(enabled).lower() == 'true'):
                enabled_brands.append(brand_code)
        
        logger.info(f"Found {len(enabled_brands)} enabled brands: {enabled_brands}")
        return enabled_brands

    def read_all_brands_rows(self, brands_table_name: str = None) -> List[Dict]:
        """
        Read all rows from the brands table in NocoDB.
        
        Args:
            brands_table_name: Optional override for the brands table name
            
        Returns:
            List of all brand records from the table
        """
        try:
            # Use provided table name or construct from current table
            if brands_table_name:
                brands_api_url = f"{self.base_url}/api/v1/db/data/noco/{self.project_name}/{brands_table_name}"
            else:
                # Try to construct brands table name from current table
                current_table = self.table_name
                if 'product' in current_table.lower():
                    brands_table = current_table.replace('product', 'brand').replace('Product', 'Brand')
                else:
                    brands_table = 'brands'  # Default fallback
                brands_api_url = f"{self.base_url}/api/v1/db/data/noco/{self.project_name}/{brands_table}"
            
            logger.info(f"Reading all rows from brands table: {brands_api_url}")
            
            # Get all records from brands table
            response = requests.get(brands_api_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            all_rows = data.get('list', [])
            
            logger.info(f"Successfully read {len(all_rows)} rows from brands table")
            
            return all_rows
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to read brands table: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error reading brands table: {e}")
            return []

