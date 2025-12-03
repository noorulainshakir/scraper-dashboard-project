# Wink to NocoDB Inventory Synchronization

Standalone script to synchronize product inventory data from Wink API to NocoDB.

## 🚀 Quick Start

### Run the sync (2 ways):

**Option 1: From this folder**
```bash
python run_sync.py
```

**Option 2: From project root**
```bash
python "Noco-Wink Inventory Sync/run_sync.py"
```

### First time setup:
1. Copy `env_example.txt` to `../.env` (project root)
2. Fill in your credentials in `.env`
3. Run the sync

---

## Overview

This script fetches real-time inventory data from the Wink PMS (Practice Management System) API and updates NocoDB records with:
- **Wink Stock Status**: `in_stock`, `low_stock`, `out_of_stock`, or `not_found`
- **Wink Location Inventory**: JSON object with stock counts per store location

## Features

- ✅ Automatic authentication with Wink API
- ✅ Batch processing with progress tracking
- ✅ Store location mapping (Niagara Falls, St. Catharines, Welland, etc.)
- ✅ Rate limiting protection
- ✅ Detailed sync statistics
- ✅ Error handling and retry logic

## Prerequisites

1. **Python 3.8+** installed
2. **Environment variables** configured (see Configuration section)
3. **NocoDB** with table containing:
   - `Wink Id` field (product identifier in Wink)
   - `Wink Stock Status` field (will be updated)
   - `Wink Location Inventory` field (will be updated)

## Installation

No additional installation required if you're already running the main Spectacle-Clinic-Scrapers project. This script uses the same dependencies.

## Configuration

### Required Environment Variables

Create a `.env` file in the project root (`Spectacle-Clinic-Scrapers/.env`) with:

```env
# NocoDB Configuration
NOCODB_API_TOKEN=your_nocodb_api_token
NOCODB_BASE_URL=https://your-nocodb-instance.com
NOCODB_PROJECT_NAME=your_project_name
NOCODB_TABLE_NAME=your_table_name

# Wink API Configuration
WINK_ACCOUNT_ID=your_account_id
WINK_USERNAME=your_username
WINK_PASSWORD=your_password
WINK_STORE_ID=1
```

### Store Location Mapping

The script uses hardcoded store mappings:
- Store ID `1` → Niagara Falls
- Store ID `8` → St. Catharines
- Store ID `10` → Niagara On The Lake
- Store ID `11` → Welland

## Usage

### Run the Sync

From the project root directory:

```bash
python "Noco-Wink Inventory Sync/run_sync.py"
```

Or navigate to the folder:

```bash
cd "Noco-Wink Inventory Sync"
python run_sync.py
```

### What It Does

1. **Authenticates** with Wink API using credentials from `.env`
2. **Fetches** all NocoDB records that have a `Wink Id`
3. **Queries** Wink API for each product's inventory data
4. **Updates** NocoDB with:
   - Stock status (in_stock/low_stock/out_of_stock/not_found)
   - Location inventory as JSON (e.g., `{"Niagara Falls": 2, "St. Catharines": 1}`)
5. **Displays** sync statistics

### Example Output

```
Wink to NocoDB Inventory Synchronization
════════════════════════════════════════

✓ Loaded environment variables
✓ Authenticated with Wink API
✓ Found 1,234 records with Wink Id

Syncing inventory... ████████████████████ 100%

Wink Inventory Sync Results
┌─────────────────┬────────┐
│ Metric          │  Value │
├─────────────────┼────────┤
│ Total Records   │  1,234 │
│ Processed       │  1,234 │
│ Updated         │  1,200 │
│ Not Found       │     34 │
│ Errors          │      0 │
│                 │        │
│ In Stock        │    856 │
│ Low Stock       │     89 │
│ Out of Stock    │    255 │
└─────────────────┴────────┘

✓ Wink inventory sync completed successfully!
```

## Stock Status Logic

The script determines stock status based on total inventory across all locations:

- **in_stock**: Total stock > 2 units
- **low_stock**: Total stock 1-2 units
- **out_of_stock**: Total stock = 0 units
- **not_found**: Product not found in Wink API (Wink Id invalid or product doesn't exist)

## Inventory Data Format

The `Wink Location Inventory` field is updated with JSON data:

```json
{
  "Niagara Falls": 2,
  "St. Catharines": 1,
  "Welland": 0,
  "Niagara On The Lake": 0
}
```

## Integration with Shopify Sync

This sync runs **before** the main Shopify sync in `shopify/main.py` to ensure:
1. NocoDB has latest inventory from Wink
2. Shopify gets accurate availability status
3. Inventory metafields are current

The Shopify sync (`product_transformer.py`) uses the Wink data to calculate:
- `inventory.is_in_stock` metafield (Boolean)
- `inventory.availability_status` metafield ("Available", "Backorder", "Last Pieces", "Out of Stock")
- `inventory.estimated_availability_date` metafield (Date)

## Troubleshooting

### "Missing NocoDB configuration!"
- Check that `.env` file exists in project root
- Verify all required environment variables are set

### "Login failed: 401"
- Check Wink API credentials in `.env`
- Verify `WINK_ACCOUNT_ID`, `WINK_USERNAME`, `WINK_PASSWORD`

### "Rate limit exceeded"
- Script will automatically wait and retry
- If persisting, increase delay in `wink_inventory_sync.py` (line 588)

### "No records with Wink Id found"
- Check that your NocoDB table has a `Wink Id` field
- Verify records have Wink Id values populated

## Technical Details

### API Endpoints

- **Wink Login**: `https://azurefd.downloadwink.com/Web/login/doctors`
- **Wink Product**: `https://azurefd.downloadwink.com/Web/Product/{wink_id}`

### Files

- `run_sync.py`: Main entry point (this folder)
- `../shopify/wink_inventory_sync.py`: Core sync logic (imports from here)
- `../common_modules/nocodb_manager.py`: NocoDB API wrapper

### Rate Limiting

- Default delay: 0.5 seconds between API calls
- Automatic retry on 429 (Rate Limit) errors
- Respects `Retry-After` header

## Exit Codes

- `0`: Success (no errors)
- `1`: Errors occurred during sync or interrupted by user

## Support

For issues or questions, check:
1. Main project README: `../README.md`
2. Wink API documentation
3. NocoDB API documentation

---

**Last Updated**: December 2, 2025

