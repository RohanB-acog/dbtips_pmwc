#!/usr/bin/env python3
"""
Cache Management Script

This script manages cache operations for disease data, including:
- Backing up individual disease cache files
- Clearing cache for specific diseases
- Regenerating cache data for specific diseases
- Restoring from backup
- Tracking regeneration history
- Analyzing differences between backup and regenerated files

Usage:
    python cache_main.py [OPERATION] [OPTIONS]

Operations:
    backup [DISEASE_ID]      Backup specific disease or all processed diseases
    clear [DISEASE_ID]       Clear cache for specific disease or all processed diseases
    regenerate [DISEASE_ID]  Regenerate the cache data for specific disease or all marked for regeneration
    restore [DISEASE_ID]     Restore specific disease or all diseases from backup
    full [DISEASE_ID]        Perform full cycle (backup, clear, regenerate) for specific disease or all processed diseases
    history [DISEASE_ID]     Show operation history for a specific disease or recent operations
    diff [DISEASE_ID]        Analyze differences between backup and regenerated files
    report                   Show monthly statistics on disease operations
    help                     Display this help message

Examples:
    python cache_main.py --backup           # Backup all processed diseases
    python cache_main.py --clear            # Clear out all processed diseases 
    python cache_main.py --regenerate       # Regenerate all processed diseases 
    python cache_main.py --full             # Perform full operation cycle
    python cache_main.py --restore          # Restore all the backedup diseases to the main directory
    python cache_main.py --history          # Show operation history of all processed diseases
    python cache_main.py --diff             # Analyze differences for all processed diseases
    python cache_main.py --report           # Show monthly statistics
"""

import asyncio
import sys
import os
import traceback
from datetime import datetime
import glob

# Add the script directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Import cache management modules
from cache_management.backup import backup_single_disease, backup_processed_diseases
from cache_management.clear_cache import clear_single_disease, clear_and_create_empty_files
from cache_management.regenerate import regenerate_single_disease, regenerate_cache, update_disease_status
from cache_management.restore import restore_from_backup, restore_single_disease
from cache_management.history_tracker import record_regeneration, print_last_operation_summary, print_monthly_stats
from cache_management.diff_analyzer import analyze_disease_diff, print_diff_summary
from cache_management.utils import setup_logging, create_backup_directories, log_error_to_json, BASE_DIR
from cache_management.backup import get_processed_diseases_ordered_by_time
class CacheManagementError(Exception):
    """Custom exception for cache management operations."""
    pass

async def clear_previous_logs():
    """Clear all previous log files in the cached_data_json/logs directory."""
    logger = setup_logging("clear_logs")
    logs_dir = os.path.join(BASE_DIR, "cached_data_json", "logs")
    try:
        if os.path.exists(logs_dir):
            log_files = glob.glob(os.path.join(logs_dir, "*.log"))
            for log_file in log_files:
                os.remove(log_file)
            logger.info(f"Successfully cleared {len(log_files)} log files from {logs_dir}")
        else:
            logger.warning(f"Logs directory {logs_dir} does not exist")
    except Exception as e:
        logger.error(f"Error clearing log files: {str(e)}")

async def print_usage():
    """Display usage instructions."""
    print(__doc__)

async def perform_full_cycle_for_disease(disease_id):
    """Perform full cache management cycle for a single disease."""
    logger = setup_logging("full_cycle")
    logger.info(f"Starting full cache management cycle for disease {disease_id}...")
    
    try:
        # Step 1: Backup
        logger.info(f"Step 1: Backing up disease {disease_id}...")
        backup_result = await backup_single_disease(disease_id)
        if not backup_result:
            error_msg = f"Backup step failed for disease {disease_id}"
            logger.error(error_msg)
            log_error_to_json(disease_id, "backup_failure", error_msg)
            await record_regeneration(disease_id, operation_type="full", status="failed", notes="Backup step failed")
            return False
        
        # Step 2: Clear cache
        logger.info(f"Step 2: Clearing cache for disease {disease_id}...")
        clear_result = await clear_single_disease(disease_id)
        if not clear_result:
            error_msg = f"Clear step failed for disease {disease_id}"
            logger.error(error_msg)
            log_error_to_json(disease_id, "clear_failure", error_msg)
            await record_regeneration(disease_id, operation_type="full", status="failed", notes="Clear step failed")
            return False
        
        # Step 3: Regenerate
        logger.info(f"Step 3: Regenerating cache for disease {disease_id}...")
        regenerate_result = await regenerate_single_disease(disease_id)
        if not regenerate_result:
            error_msg = f"Regeneration step failed for disease {disease_id}"
            logger.error(error_msg)
            log_error_to_json(disease_id, "regenerate_failure", error_msg)
            await record_regeneration(disease_id, operation_type="full", status="failed", notes="Regenerate step failed")
            return False
        
        # Step 4: Analyze differences
        logger.info(f"Step 4: Analyzing differences for disease {disease_id}...")
        await analyze_disease_diff(disease_id)
        
        # Record successful full cycle operation
        await record_regeneration(disease_id, operation_type="full", status="success")
        
        logger.info(f"Full cache management cycle for disease {disease_id} completed successfully.")
        
        await print_last_operation_summary(disease_id)
        
        return True
        
    except Exception as e:
        error_msg = f"Unexpected error in full cycle for disease {disease_id}: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        log_error_to_json(disease_id, "full_cycle_error", error_msg)
        await record_regeneration(disease_id, operation_type="full", status="failed", notes=f"Error: {str(e)}")
        return False


async def perform_full_cycle():
    """Perform a full cache management cycle for all processed diseases in chronological order."""
    logger = setup_logging("full_cycle")
    logger.info("Starting full cache management cycle for all processed diseases in chronological order...")
    
    try:
        # Get all processed diseases ordered by processed_time
        
        disease_records = await get_processed_diseases_ordered_by_time()
        
        if not disease_records:
            logger.warning("No processed diseases found to perform full cycle.")
            return True
        
        # Extract just the disease IDs
        disease_ids = [record["id"] for record in disease_records]
        
        logger.info(f"Found {len(disease_ids)} processed diseases to cycle through, ordered by processing time")
        
        # Process each disease
        success_count = 0
        for disease_id in disease_ids:
            logger.info(f"Starting full cycle for disease {disease_id}")
            result = await perform_full_cycle_for_disease(disease_id)
            if result:
                success_count += 1
            await asyncio.sleep(2)
        
        logger.info(f"Full cycle completed: {success_count}/{len(disease_ids)} diseases processed successfully")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Unexpected error in full cycle: {str(e)}")
        logger.error(traceback.format_exc())
        return False

async def execute_operation(operation_name, operation_func, *args, record_operation=None):
    """Execute a cache management operation with error handling."""
    logger = setup_logging("execute_operation")
    
    try:
        logger.info(f"Starting {operation_name}...")
        result = await operation_func(*args)
        
        if record_operation and 'disease_id' in record_operation and 'operation_type' in record_operation:
            disease_id = record_operation['disease_id']
            operation_type = record_operation['operation_type']
            status = "success" if result else "failed"
            await record_regeneration(disease_id, operation_type=operation_type, status=status)
        
        if result:
            logger.info(f"{operation_name} completed successfully.")
            print(f"{operation_name} completed successfully.")
            
            if record_operation and 'disease_id' in record_operation:
                await print_last_operation_summary(record_operation['disease_id'])
        else:
            logger.error(f"{operation_name} failed.")
            print(f"{operation_name} failed. Check logs for details.")
            
        return result
        
    except Exception as e:
        logger.error(f"Exception during {operation_name}: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"{operation_name} failed with exception: {str(e)}. Check logs for details.")
        
        if record_operation and 'disease_id' in record_operation and 'operation_type' in record_operation:
            await record_regeneration(
                record_operation['disease_id'], 
                operation_type=record_operation['operation_type'], 
                status="failed", 
                notes=f"Error: {str(e)}"
            )
        
        return False

async def main():
    """Main entry point for the cache management script."""
    try:
        # Clear previous log files
        await clear_previous_logs()
        
        # Create necessary directories
        await create_backup_directories()
        
        # Check command line arguments
        if len(sys.argv) < 2:
            await print_usage()
            return
            
        operation = sys.argv[1].lower()
        
        # Check if a specific disease ID is provided
        disease_id = None
        if len(sys.argv) > 2 and operation != "help" and operation != "report":
            disease_id = sys.argv[2]
        
        # Process the operation
        if operation == "help" or operation == "--help":
            await print_usage()
            
        elif operation == "--backup":
            if disease_id:
                await execute_operation(
                    f"Backup of disease {disease_id}", 
                    backup_single_disease, 
                    disease_id,
                    record_operation={'disease_id': disease_id, 'operation_type': 'backup'}
                )
            else:
                disease_ids = await backup_processed_diseases()
                if not disease_ids:
                    print("No processed diseases found to backup.")
                    return
                
                print(f"Starting backup for {len(disease_ids)} diseases...")
                success_count = 0
                for d_id in disease_ids:
                    result = await backup_single_disease(d_id)
                    if result:
                        await record_regeneration(d_id, operation_type="backup", status="success")
                        success_count += 1
                    else:
                        await record_regeneration(d_id, operation_type="backup", status="failed")
                    await asyncio.sleep(1)
                    
                print(f"Backup completed: {success_count}/{len(disease_ids)} successful.")
                
        elif operation == "--clear":
            if disease_id:
                await execute_operation(
                    f"Cache clearing for disease {disease_id}", 
                    clear_single_disease, 
                    disease_id,
                    record_operation={'disease_id': disease_id, 'operation_type': 'clear'}
                )
            else:
                await execute_operation("Cache clearing for all processed diseases", clear_and_create_empty_files)
                
        elif operation == "--regenerate":
            if disease_id:
                await update_disease_status(disease_id, "regeneration")
                await execute_operation(
                    f"Cache regeneration for disease {disease_id}", 
                    regenerate_single_disease, 
                    disease_id,
                    record_operation={'disease_id': disease_id, 'operation_type': 'regenerate'}
                )
                await analyze_disease_diff(disease_id)
            else:
                await execute_operation("Cache regeneration for marked diseases", regenerate_cache)
                
        elif operation == "--restore":
            if disease_id:
                await execute_operation(
                    f"Restore of disease {disease_id}", 
                    restore_single_disease, 
                    disease_id,
                    record_operation={'disease_id': disease_id, 'operation_type': 'restore'}
                )
            else:
                await execute_operation("Restore from backup", restore_from_backup)
                
        elif operation == "--full":
            if disease_id:
                await execute_operation(
                    f"Full cycle for disease {disease_id}", 
                    perform_full_cycle_for_disease, 
                    disease_id
                )
            else:
                await execute_operation("Full cycle for all processed diseases", perform_full_cycle)
                
        elif operation == "--history":
            if disease_id:
                await print_last_operation_summary(disease_id)
            else:
                await print_last_operation_summary()
                
        elif operation == "--diff":
            if not disease_id:
                print("Error: Disease ID is required for diff analysis.")
                return
                
            diff_report = await analyze_disease_diff(disease_id)
            if diff_report:
                await print_diff_summary(diff_report)
            else:
                print(f"Failed to analyze differences for disease {disease_id}")
                
        elif operation == "--report":
            month = datetime.now().month
            year = datetime.now().year
            await print_monthly_stats(month, year)
                
        else:
            print(f"Error: Invalid operation '{operation}'.")
            await print_usage()
                
    except Exception as e:
        logger = setup_logging("main_exception")
        logger.error(f"Unhandled exception in main: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
