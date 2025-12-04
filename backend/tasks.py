from celery_app import celery
from wink_inventory_sync import WinkInventorySync
from nocodb_manager import NocoDBManager
import os

@celery.task(bind=True)
def run_wink_sync(self, limit=None):
    """Celery task to run Wink Inventory Sync"""
    # Initialize NocoDB manager
    nocodb_manager = NocoDBManager(
        api_token=os.getenv("NOCODB_API_TOKEN"),
        base_url=os.getenv("NOCODB_BASE_URL"),
        project_name=os.getenv("NOCODB_PROJECT_NAME"),
        table_name=os.getenv("NOCODB_TABLE_NAME")
    )
    
    # Initialize WinkInventorySync
    wink_sync = WinkInventorySync(nocodb_manager)
    
    # Run sync
    stats = wink_sync.sync_inventory(limit=limit)
    return stats
