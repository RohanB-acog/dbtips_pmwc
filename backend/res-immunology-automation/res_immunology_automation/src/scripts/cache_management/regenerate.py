"""
Module for regenerating cache data for individual diseases with retry logic.
"""

import asyncio
import sys
import os
import json
from sqlalchemy import select, update
from datetime import datetime
from .utils import (
    setup_logging,
    log_error_to_json,
    check_environment_variables,
    retry_with_backoff,
    find_latest_backup_for_disease,
    BASE_DIR,
    DISEASE_CACHE_DIR
)
import tzlocal

# Import database models and functions
sys.path.append(BASE_DIR)
from build_dossier import SessionLocal, DiseasesDossierStatus, run_endpoints, get_db
from graphrag_service import get_redis


async def verify_redis_connection():
    """Verify Redis connection is working."""
    logger = setup_logging("verify_redis")
    
    try:
        redis = get_redis()
        # Perform a simple ping operation to verify connection
        ping_result = redis.ping()
        if ping_result:
            logger.info("Redis connection verified successfully")
            return True
        else:
            logger.error("Redis connection check failed")
            return False
    except Exception as e:
        logger.error(f"Error verifying Redis connection: {str(e)}")
        return False


async def update_disease_status(disease_id, status, processed_time=None):
    """Update disease status."""
    logger = setup_logging("update_status")
    
    try:
        async with SessionLocal() as db:
            logger.info(f"Updating status for disease {disease_id} to '{status}'")
            
            values = {"status": status}
            if processed_time:
                values["processed_time"] = processed_time
                
            update_stmt = (
                update(DiseasesDossierStatus)
                .where(DiseasesDossierStatus.id == disease_id)
                .values(**values)
            )
            await db.execute(update_stmt)
            await db.commit()
            logger.info(f"Successfully updated disease {disease_id} status to '{status}'")
            return True
    except Exception as e:
        error_msg = f"Error updating disease {disease_id} status to '{status}': {str(e)}"
        logger.error(error_msg)
        log_error_to_json(disease_id, "status_update_error", error_msg)
        return False


async def verify_json_file_content(disease_id):
    """Verify the JSON file is not empty after regeneration."""
    logger = setup_logging("verify_json")
    
    file_path = os.path.join(DISEASE_CACHE_DIR, f"{disease_id}.json")
    if not os.path.exists(file_path):
        error_msg = f"JSON file for disease {disease_id} does not exist after regeneration."
        logger.error(error_msg)
        log_error_to_json(disease_id, "verification_error", error_msg)
        return False
    
    if os.path.getsize(file_path) == 0:
        error_msg = f"JSON file for disease {disease_id} is empty after regeneration."
        logger.error(error_msg)
        log_error_to_json(disease_id, "verification_error", error_msg)
        return False
    
    # Check if the file contains valid JSON and is not just '{}'
    try:
        with open(file_path, 'r') as f:
            content = json.load(f)
            if not content:
                error_msg = f"JSON file for disease {disease_id} contains empty object."
                logger.error(error_msg)
                log_error_to_json(disease_id, "verification_error", error_msg)
                return False
    except json.JSONDecodeError:
        error_msg = f"JSON file for disease {disease_id} contains invalid JSON."
        logger.error(error_msg)
        log_error_to_json(disease_id, "verification_error", error_msg)
        return False
    except Exception as e:
        error_msg = f"Error checking JSON content for disease {disease_id}: {str(e)}"
        logger.error(error_msg)
        log_error_to_json(disease_id, "verification_error", error_msg)
        return False
    
    logger.info(f"Successfully verified JSON content for disease {disease_id}.")
    return True


async def run_regeneration_for_disease(disease_id):
    """Run regeneration for a single disease."""
    logger = setup_logging("run_regeneration")
    
    try:
        # Run endpoints for this single disease
        logger.info(f"Running regeneration for disease {disease_id}")
        single_disease_list = [disease_id]
        
        # Track which endpoint is being called
        current_endpoint = "run_endpoints"
        try:
            status = await run_endpoints(single_disease_list)
            
            if status and status != "error":
                logger.info(f"Regeneration completed for disease {disease_id}")
                return True
            else:
                error_msg = f"Regeneration returned error status for disease {disease_id}"
                logger.error(error_msg)
                log_error_to_json(disease_id, "regeneration_error", error_msg, 
                                 module="regenerate", endpoint=current_endpoint)
                return False
        except Exception as endpoint_error:
            error_msg = f"Exception in endpoint {current_endpoint}: {str(endpoint_error)}"
            logger.error(error_msg)
            log_error_to_json(disease_id, "endpoint_error", str(endpoint_error), 
                             module="regenerate", endpoint=current_endpoint)
            return False
            
    except Exception as e:
        error_msg = f"Exception during regeneration for disease {disease_id}: {str(e)}"
        logger.error(error_msg)
        log_error_to_json(disease_id, "regeneration_exception", error_msg, module="regenerate")
        return False

async def restore_disease_from_backup(disease_id):
    """Restore a disease file from its backup."""
    logger = setup_logging("restore_disease")
    logger.info(f"Attempting to restore disease {disease_id} from backup")
    
    try:
        # Find the latest backup for this disease
        backup_file = find_latest_backup_for_disease(disease_id)
        
        if not backup_file:
            error_msg = f"No backup found for disease {disease_id}"
            logger.error(error_msg)
            log_error_to_json(disease_id, "restore_error", error_msg)
            return False
        
        # Copy the backup to the cache directory
        import shutil
        destination_file = os.path.join(DISEASE_CACHE_DIR, f"{disease_id}.json")
        shutil.copy2(backup_file, destination_file)
        
        logger.info(f"Successfully restored disease {disease_id} from backup {os.path.basename(backup_file)}")
        return True
        
    except Exception as e:
        error_msg = f"Error restoring disease {disease_id} from backup: {str(e)}"
        logger.error(error_msg)
        log_error_to_json(disease_id, "restore_error", error_msg)
        return False


async def regenerate_single_disease(disease_id):
    """Regenerate cache data for a single disease with retry logic."""
    logger = setup_logging("regenerate_single")
    logger.info(f"Starting regeneration process for disease: {disease_id}")
    
    # Update status to "processing"
    await update_disease_status(disease_id, "processing")
    
    # Try regeneration with retry logic
    success, error_msg = await retry_with_backoff(run_regeneration_for_disease, 5, 5, disease_id)
    
    # Verify JSON content
    if success:
        json_valid = await verify_json_file_content(disease_id)
        if json_valid:
            # Update status to "processed"
            current_time = datetime.now(tzlocal.get_localzone())
            await update_disease_status(disease_id, "processed", current_time)
            logger.info(f"Disease {disease_id} regeneration completed successfully")
            return True
        else:
            success = False
            error_msg = "JSON verification failed"
    
    # If regeneration failed, restore from backup
    logger.error(f"Regeneration failed for disease {disease_id}: {error_msg}")
    log_error_to_json(disease_id, "regeneration_failed", error_msg)
    
    logger.info(f"Attempting to restore disease {disease_id} from backup")
    restore_success = await restore_disease_from_backup(disease_id)
    
    if restore_success:
        # Update status back to "processed" since we restored the backup
        current_time = datetime.now(tzlocal.get_localzone())
        await update_disease_status(disease_id, "processed", current_time)
        logger.info(f"Successfully restored {disease_id} from backup")
    else:
        # Set to error state if restore fails
        await update_disease_status(disease_id, "error")
        logger.error(f"Failed to restore {disease_id} from backup. Status set to 'error'")
    
    return False


async def get_diseases_for_regeneration():
    """Get all diseases with 'regeneration' status."""
    logger = setup_logging("get_regeneration")
    
    try:
        async with SessionLocal() as db:
            # Select diseases with 'regeneration' status
            result = await db.execute(
                select(DiseasesDossierStatus).where(DiseasesDossierStatus.status == "regeneration")
            )
            disease_records = result.scalars().all()
            disease_ids = [record.id for record in disease_records]
            
            if disease_ids:
                logger.info(f"Found {len(disease_ids)} diseases with 'regeneration' status: {disease_ids}")
            else:
                logger.info("No diseases with 'regeneration' status found")
                
            return disease_ids
            
    except Exception as e:
        logger.error(f"Error getting diseases for regeneration: {str(e)}")
        return []


async def regenerate_cache():
    """Process diseases with 'regeneration' status one by one."""
    logger = setup_logging("regenerate_cache")
    logger.info("Starting cache regeneration for marked diseases...")
    
    # Check environment variables
    missing_vars = check_environment_variables()
    if missing_vars:
        logger.error(f"Missing environment variables: {missing_vars}")
        return False
    
    # Verify Redis connection
    redis_check = await verify_redis_connection()
    if not redis_check:
        logger.error("Redis connection verification failed. Cannot proceed with regeneration.")
        return False
    
    try:
        # Get all diseases with 'regeneration' status
        disease_ids = await get_diseases_for_regeneration()
        
        if not disease_ids:
            logger.warning("No diseases with 'regeneration' status found to process.")
            return True  # Return true since there's nothing to do
        
        logger.info(f"Processing {len(disease_ids)} diseases sequentially...")
        
        # Process each disease one by one
        overall_success = True
        for disease_id in disease_ids:
            logger.info(f"Processing disease {disease_id}...")
            result = await regenerate_single_disease(disease_id)
            if not result:
                logger.warning(f"Failed to regenerate disease {disease_id} even after retries and restore")
                overall_success = False
            
            # Add a small delay between processing diseases to avoid overloading
            await asyncio.sleep(2)
        
        if overall_success:
            logger.info("All diseases processed successfully")
        else:
            logger.warning("Some diseases failed to regenerate properly")
            
        return overall_success
        
    except Exception as e:
        logger.error(f"Error during cache regeneration: {str(e)}")
        return False


async def main():
    """Main entry point for regenerate module."""
    if len(sys.argv) > 1:
        # If disease ID is provided as argument, regenerate only that disease
        disease_id = sys.argv[1]
        # First update status to 'regeneration'
        await update_disease_status(disease_id, "regeneration")
        result = await regenerate_single_disease(disease_id)
        if result:
            print(f"Regeneration of disease {disease_id} completed successfully.")
        else:
            print(f"Regeneration of disease {disease_id} failed. Check logs for details.")
    else:
        # Otherwise process all diseases marked for regeneration
        result = await regenerate_cache()
        if result:
            print("Cache regeneration completed successfully.")
        else:
            print("Cache regeneration encountered issues. Check logs for details.")


if __name__ == "__main__":
    asyncio.run(main())