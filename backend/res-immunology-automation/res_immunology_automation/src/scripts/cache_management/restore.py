"""
Module for restoring cache data from backup.
"""

import os
import sys
import asyncio
import shutil
import glob
from pathlib import Path
from sqlalchemy import update
from datetime import datetime
from .utils import (
    setup_logging,
    log_error_to_json,
    find_latest_backup_for_disease,
    BACKUP_DIR,
    DISEASE_CACHE_DIR,
    BASE_DIR
)
import tzlocal

# Import database models
sys.path.append(BASE_DIR)
from build_dossier import SessionLocal, DiseasesDossierStatus


async def restore_single_disease(disease_id):
    """Restore a single disease from its latest backup."""
    logger = setup_logging("restore_single")
    logger.info(f"Starting restore for disease: {disease_id}")
    
    try:
        # Find the latest backup file for this disease
        backup_file = find_latest_backup_for_disease(disease_id)
        
        if not backup_file:
            error_msg = f"No backup found for disease {disease_id}"
            logger.error(error_msg)
            log_error_to_json(disease_id, "restore_error", error_msg, module="restore")
            return False
        
        # Ensure cache directory exists
        os.makedirs(DISEASE_CACHE_DIR, exist_ok=True)
        
        # Copy the backup file to the cache directory
        destination = os.path.join(DISEASE_CACHE_DIR, f"{disease_id}.json")
        shutil.copy2(backup_file, destination)
        
        # Update disease status to "processed"
        try:
            async with SessionLocal() as db:
                current_time = datetime.now(tzlocal.get_localzone())
                update_stmt = (
                    update(DiseasesDossierStatus)
                    .where(DiseasesDossierStatus.id == disease_id)
                    .values(status="processed", processed_time=current_time)
                )
                await db.execute(update_stmt)
                await db.commit()
                logger.info(f"Updated disease {disease_id} status to 'processed'")
        except Exception as e:
            logger.error(f"Error updating status for disease {disease_id}: {str(e)}")
            
        logger.info(f"Successfully restored disease {disease_id} from backup: {os.path.basename(backup_file)}")
        return True
            
    except Exception as e:
        error_msg = f"Error restoring disease {disease_id}: {str(e)}"
        logger.error(error_msg)
        log_error_to_json(disease_id, "restore_error", error_msg, module="restore")
        return False


async def get_all_diseases_with_backups():
    """Get a list of all disease IDs that have backup files."""
    backup_dir = os.path.join(BACKUP_DIR, "disease")
    
    if not os.path.exists(backup_dir):
        return []
    
    backup_files = glob.glob(os.path.join(backup_dir, "*.json"))
    disease_ids = set()
    
    for file in backup_files:
        # Extract disease ID from filename (format: {disease_id}_{timestamp}.json)
        filename = os.path.basename(file)
        disease_id = filename.split('_')[0]  # Get the part before the first underscore
        disease_ids.add(disease_id)
    
    return list(disease_ids)


async def restore_from_backup(disease_id=None):
    """
    Restore cache data from backup.
    
    Args:
        disease_id: Optional disease ID to restore. If None, restores all diseases with backups.
    """
    logger = setup_logging("restore")
    
    if disease_id:
        # Restore specific disease
        logger.info(f"Restoring specific disease: {disease_id}")
        result = await restore_single_disease(disease_id)
        return result
    else:
        # Restore all diseases with backups
        logger.info("Restoring all diseases with backups")
        
        disease_ids = await get_all_diseases_with_backups()
        if not disease_ids:
            logger.warning("No disease backups found to restore")
            return False
        
        logger.info(f"Found {len(disease_ids)} disease backups to restore")
        
        success_count = 0
        for disease_id in disease_ids:
            result = await restore_single_disease(disease_id)
            if result:
                success_count += 1
            await asyncio.sleep(1)  # Small delay between operations
            
        logger.info(f"Restore completed: {success_count}/{len(disease_ids)} diseases restored successfully")
        return success_count > 0


async def main():
    """Main entry point for restore module."""
    import sys
    
    if len(sys.argv) > 1:
        # If disease ID is provided as argument, restore only that disease
        disease_id = sys.argv[1]
        result = await restore_from_backup(disease_id)
        if result:
            print(f"Restore of disease {disease_id} completed successfully.")
        else:
            print(f"Restore of disease {disease_id} failed. Check logs for details.")
    else:
        # Otherwise restore all diseases with backups
        result = await restore_from_backup()
        if result:
            print("Restore of all diseases completed successfully.")
        else:
            print("Restore operation failed. Check logs for details.")


if __name__ == "__main__":
    asyncio.run(main())