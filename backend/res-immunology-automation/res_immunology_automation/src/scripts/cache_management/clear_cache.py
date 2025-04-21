"""
Module for clearing cache for individual diseases.
"""

import os
import asyncio
import json
import sys
from sqlalchemy import select, update
from datetime import datetime, timedelta
from .utils import (
    setup_logging,
    log_error_to_json,
    find_latest_backup_for_disease,
    DISEASE_CACHE_DIR,
    BASE_DIR
)
import tzlocal

# Import database models
sys.path.append(BASE_DIR)
from build_dossier import SessionLocal
from db.models import DiseasesDossierStatus
from graphrag_service import get_redis

# Import backup function from backup module
from .backup import backup_single_disease

async def update_disease_status(disease_id, status):
    """Update the status of a specific disease with current timestamp."""
    logger = setup_logging("update_status")
    
    try:
        async with SessionLocal() as db:
            current_time = datetime.now(tzlocal.get_localzone())
            
            # Always update submission_time when changing status to "regeneration"
            # For other statuses, only update the status field
            if status == "regeneration":
                update_stmt = (
                    update(DiseasesDossierStatus)
                    .where(DiseasesDossierStatus.id == disease_id)
                    .values(status=status, submission_time=current_time)
                )
            else:
                update_stmt = (
                    update(DiseasesDossierStatus)
                    .where(DiseasesDossierStatus.id == disease_id)
                    .values(status=status)
                )
                
            await db.execute(update_stmt)
            await db.commit()
            
            if status == "regeneration":
                logger.info(f"Successfully updated disease {disease_id} status to '{status}' with new submission_time {current_time}")
            else:
                logger.info(f"Successfully updated disease {disease_id} status to '{status}'")
                
            return True
    except Exception as e:
        error_msg = f"Error updating disease {disease_id} status to '{status}': {str(e)}"
        logger.error(error_msg)
        log_error_to_json(disease_id, "clear_file_error", error_msg, module="clear_cache")
        return False


async def clear_disease_file(disease_id):
    """Clear a specific disease JSON file and create an empty one."""
    logger = setup_logging("clear_disease")
    logger.info(f"Clearing cache file for disease: {disease_id}")
    
    # Ensure cache directory exists
    os.makedirs(DISEASE_CACHE_DIR, exist_ok=True)
    
    file_path = os.path.join(DISEASE_CACHE_DIR, f"{disease_id}.json")
    
    try:
        # Remove file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Removed existing file: {file_path}")
        
        # Create empty JSON file
        with open(file_path, 'w') as f:
            json.dump({}, f)
        logger.info(f"Created empty file: {file_path}")
        
        return True
        
    except Exception as e:
        error_msg = f"Error clearing disease file for {disease_id}: {str(e)}"
        logger.error(error_msg)
        log_error_to_json(disease_id, "clear_file_error", error_msg, module="clear_cache")
        return False


async def clear_redis_cache_for_disease(disease_id):
    """Clear Redis cache entries for a specific disease."""
    logger = setup_logging("clear_redis")
    
    try:
        # Get Redis connection
        redis = get_redis()
        logger.info("Connected to Redis successfully")
        
        # Get keys related to this disease
        pattern = f"*{disease_id}*"
        keys = redis.keys(pattern)
        
        if keys:
            # Delete matching keys
            redis.delete(*keys)
            logger.info(f"Deleted {len(keys)} Redis keys for disease {disease_id}")
        else:
            logger.info(f"No Redis keys found for disease {disease_id}")
        
        return True
        
    except Exception as e:
        error_msg = f"Error clearing Redis cache for disease {disease_id}: {str(e)}"
        logger.error(error_msg)
        log_error_to_json(disease_id, "clear_file_error", error_msg, module="clear_cache")
        return False


async def ensure_backup_exists(disease_id):
    """Ensure that a backup exists for a specific disease, create one if not."""
    logger = setup_logging("ensure_backup")
    
    # Check if backup exists for the disease
    existing_backup = find_latest_backup_for_disease(disease_id)
    
    if existing_backup:
        logger.info(f"Found existing backup for disease {disease_id}: {os.path.basename(existing_backup)}")
        return True
    else:
        logger.info(f"No backup found for disease {disease_id}, creating one...")
        # Create backup using function from backup module
        backup_result = await backup_single_disease(disease_id)
        
        if backup_result:
            logger.info(f"Successfully created backup for disease {disease_id}")
            return True
        else:
            logger.error(f"Failed to create backup for disease {disease_id}")
            return False


async def clear_single_disease(disease_id):
    """Clear cache for a single disease and update its status."""
    logger = setup_logging("clear_single")
    logger.info(f"Starting cache clearing for disease: {disease_id}")
    
    # First ensure a backup exists, create one if not
    backup_check = await ensure_backup_exists(disease_id)
    if not backup_check:
        logger.error(f"Cannot proceed with clearing cache for disease {disease_id} without a backup")
        return False
    
    # Update status to 'regeneration'
    status_update = await update_disease_status(disease_id, "regeneration")
    if not status_update:
        logger.warning(f"Failed to update status for disease {disease_id}, but continuing with clearing")
    
    # Clear Redis cache for this disease
    redis_result = await clear_redis_cache_for_disease(disease_id)
    if not redis_result:
        logger.warning(f"Failed to clear Redis cache for disease {disease_id}, but continuing")
    
    # Clear and create empty file
    file_result = await clear_disease_file(disease_id)
    if not file_result:
        logger.error(f"Failed to clear and create empty file for disease {disease_id}")
        return False
    
    logger.info(f"Successfully cleared cache for disease {disease_id}")
    return True


async def clear_and_create_empty_files():
    """Clear all processed diseases after ensuring backups exist."""
    logger = setup_logging("clear_cache_all")
    logger.info("Starting cache clearing for all processed diseases")
    
    # For compatibility with the old approach, we'll get all processed diseases
    try:
        async with SessionLocal() as db:
            # Select diseases with 'processed' status
            result = await db.execute(
                select(DiseasesDossierStatus).where(
                    DiseasesDossierStatus.status == "processed"
                )
            )
            disease_records = result.scalars().all()
            disease_ids = [record.id for record in disease_records]
    except Exception as e:
        logger.error(f"Error getting processed diseases: {str(e)}")
        return False
    
    if not disease_ids:
        logger.warning("No processed diseases found to clear.")
        return False
        
    # Ensure backups exist for all diseases first
    logger.info(f"Ensuring backups exist for {len(disease_ids)} diseases...")
    diseases_with_backups = []
    for disease_id in disease_ids:
        backup_exists = await ensure_backup_exists(disease_id)
        if backup_exists:
            diseases_with_backups.append(disease_id)
        else:
            logger.warning(f"Skipping disease {disease_id} as backup creation failed")
    
    if not diseases_with_backups:
        logger.error("Could not ensure backups for any diseases, aborting clear operation")
        return False
    
    # Clear each disease that has a backup
    success_count = 0
    for disease_id in diseases_with_backups:
        result = await clear_single_disease(disease_id)
        if result:
            success_count += 1
            
        # Small delay between operations
        await asyncio.sleep(1)
    
    logger.info(f"Successfully cleared {success_count}/{len(diseases_with_backups)} diseases")
    return success_count > 0


async def main():
    """Main entry point for clear_cache module."""
    if len(sys.argv) > 1:
        # If disease ID is provided as argument, clear only that disease
        disease_id = sys.argv[1]
        result = await clear_single_disease(disease_id)
        if result:
            print(f"Cache clearing for disease {disease_id} completed successfully.")
        else:
            print(f"Cache clearing for disease {disease_id} failed. Check logs for details.")
    else:
        # Clear all processed diseases
        result = await clear_and_create_empty_files()
        if result:
            print("Cache clearing for all processed diseases completed successfully.")
        else:
            print("Cache clearing failed. Check logs for details.")


if __name__ == "__main__":
    asyncio.run(main())