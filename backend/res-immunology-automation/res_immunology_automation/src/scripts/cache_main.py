#!/usr/bin/env python3
"""
Cache Management Script

This script manages cache operations for disease data, including:
- Backing up individual disease cache files
- Clearing cache for specific diseases
- Regenerating cache data for specific diseases
- Restoring from backup

Usage:
    python cache_main.py [OPERATION] [OPTIONS]

Operations:
    backup [DISEASE_ID]      Backup specific disease or all processed diseases
    clear [DISEASE_ID]       Clear cache for specific disease or all processed diseases
    regenerate [DISEASE_ID]  Regenerate the cache data for specific disease or all marked for regeneration
    restore [DISEASE_ID]     Restore specific disease or all diseases from backup
    full [DISEASE_ID]        Perform full cycle (backup, clear, regenerate) for specific disease or all processed diseases
    help                     Display this help message

Examples:
    python cache_main.py backup 12345     # Backup disease with ID 12345
    python cache_main.py backup           # Backup all processed diseases
    python cache_main.py full 12345       # Full cycle for disease with ID 12345
"""

import asyncio
import sys
import os
import traceback

# Add the script directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Import cache management modules
from cache_management.backup import backup_single_disease, backup_processed_diseases
from cache_management.clear_cache import clear_single_disease, clear_and_create_empty_files
from cache_management.regenerate import regenerate_single_disease, regenerate_cache, update_disease_status
from cache_management.restore import restore_from_backup, restore_single_disease
from cache_management.utils import setup_logging, create_backup_directories, log_error_to_json


# Import build_dossier modules directly to ensure they're available
try:
    from build_dossier import get_db, run_endpoints, SessionLocal, DiseasesDossierStatus
except ImportError:
    pass  # Will be handled in the modules that need these imports


class CacheManagementError(Exception):
    """Custom exception for cache management operations."""
    pass


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
            return False
        
        # Step 2: Clear cache
        logger.info(f"Step 2: Clearing cache for disease {disease_id}...")
        clear_result = await clear_single_disease(disease_id)
        if not clear_result:
            error_msg = f"Clear step failed for disease {disease_id}"
            logger.error(error_msg)
            log_error_to_json(disease_id, "clear_failure", error_msg)
            return False
        
        # Step 3: Regenerate
        logger.info(f"Step 3: Regenerating cache for disease {disease_id}...")
        regenerate_result = await regenerate_single_disease(disease_id)
        if not regenerate_result:
            error_msg = f"Regeneration step failed for disease {disease_id}"
            logger.error(error_msg)
            log_error_to_json(disease_id, "regenerate_failure", error_msg)
            return False
        
        logger.info(f"Full cache management cycle for disease {disease_id} completed successfully.")
        return True
        
    except Exception as e:
        error_msg = f"Unexpected error in full cycle for disease {disease_id}: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        log_error_to_json(disease_id, "full_cycle_error", error_msg)
        return False


async def perform_full_cycle():
    """Perform a full cache management cycle for all processed diseases."""
    logger = setup_logging("full_cycle")
    logger.info("Starting full cache management cycle for all processed diseases...")
    
    try:
        # Get all processed diseases
        disease_ids = await backup_processed_diseases()
        
        if not disease_ids:
            logger.warning("No processed diseases found to perform full cycle.")
            return True  # Return true since there's nothing to do
        
        logger.info(f"Found {len(disease_ids)} processed diseases to cycle through")
        
        # Process each disease one by one
        success_count = 0
        for disease_id in disease_ids:
            result = await perform_full_cycle_for_disease(disease_id)
            if result:
                success_count += 1
            await asyncio.sleep(2)  # Small delay between processing diseases
        
        logger.info(f"Full cycle completed: {success_count}/{len(disease_ids)} diseases processed successfully")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Unexpected error in full cycle: {str(e)}")
        logger.error(traceback.format_exc())
        return False


async def execute_operation(operation_name, operation_func, *args):
    """Execute a cache management operation with proper error handling."""
    logger = setup_logging("execute_operation")
    
    try:
        logger.info(f"Starting {operation_name}...")
        result = await operation_func(*args)
        
        if result:
            logger.info(f"{operation_name} completed successfully.")
            print(f"{operation_name} completed successfully.")
        else:
            logger.error(f"{operation_name} failed.")
            print(f"{operation_name} failed. Check logs for details.")
            
        return result
        
    except Exception as e:
        logger.error(f"Exception during {operation_name}: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"{operation_name} failed with exception: {str(e)}. Check logs for details.")
        return False


async def main():
    """Main entry point for the cache management script."""
    try:
        # Create necessary directories
        await create_backup_directories()
        
        # Check command line arguments
        if len(sys.argv) < 2:
            await print_usage()
            return
            
        operation = sys.argv[1].lower()
        
        # Check if a specific disease ID is provided
        disease_id = None
        if len(sys.argv) > 2 and operation != "help":
            disease_id = sys.argv[2]
        
        if operation == "help" or operation == "--help":
            await print_usage()
            
        elif operation == "backup":
            if disease_id:
                # Backup specific disease
                await execute_operation(f"Backup of disease {disease_id}", backup_single_disease, disease_id)
            else:
                # Backup all processed diseases
                disease_ids = await backup_processed_diseases()
                if not disease_ids:
                    print("No processed diseases found to backup.")
                    return
                
                print(f"Starting backup for {len(disease_ids)} diseases...")
                success_count = 0
                for d_id in disease_ids:
                    result = await backup_single_disease(d_id)
                    if result:
                        success_count += 1
                    await asyncio.sleep(1)  # Small delay
                    
                print(f"Backup completed: {success_count}/{len(disease_ids)} successful.")
                
        elif operation == "clear":
            if disease_id:
                # Clear specific disease
                await execute_operation(f"Cache clearing for disease {disease_id}", clear_single_disease, disease_id)
            else:
                # Clear all processed diseases
                await execute_operation("Cache clearing for all processed diseases", clear_and_create_empty_files)
                
        elif operation == "regenerate":
            if disease_id:
                # First update status to 'regeneration'
                await update_disease_status(disease_id, "regeneration")
                # Regenerate specific disease
                await execute_operation(f"Cache regeneration for disease {disease_id}", regenerate_single_disease, disease_id)
            else:
                # Regenerate all marked diseases
                await execute_operation("Cache regeneration for marked diseases", regenerate_cache)
                
        elif operation == "restore":
            if disease_id:
                # Restore specific disease
                await execute_operation(f"Restore of disease {disease_id}", restore_single_disease, disease_id)
            else:
                # Restore all diseases
                await execute_operation("Restore from backup", restore_from_backup)
                
        elif operation == "full":
            if disease_id:
                # Full cycle for specific disease
                await execute_operation(f"Full cycle for disease {disease_id}", perform_full_cycle_for_disease, disease_id)
            else:
                # Full cycle for all processed diseases
                await execute_operation("Full cycle for all processed diseases", perform_full_cycle)
                
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