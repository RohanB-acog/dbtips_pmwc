"""
Module for backing up individual disease cache data.
"""

import os
import asyncio
import tzlocal 
import shutil
import sys
from datetime import datetime
import json
from sqlalchemy import select
from pathlib import Path
from .utils import (
    setup_logging, 
    create_backup_directories,
    get_disease_timestamp,
    log_error_to_json,
    find_latest_backup_for_disease,
    DISEASE_CACHE_DIR, 
    BACKUP_DIR,
    LOGS_DIR,
    BASE_DIR
)

# Import database models
sys.path.append(BASE_DIR)
from build_dossier import SessionLocal
from db.models import DiseasesDossierStatus


async def backup_single_disease(disease_id):
    """Backup a single disease cache file with its timestamp."""
    logger = setup_logging("backup_single")
    logger.info(f"Starting backup for disease: {disease_id}")
    
    # Ensure backup directories exist
    backup_dir = await create_backup_directories()
    
    # Check if disease file exists
    source_file = os.path.join(DISEASE_CACHE_DIR, f"{disease_id}.json")
    if not os.path.exists(source_file):
        error_msg = f"Disease file {source_file} not found."
        logger.error(error_msg)
        log_error_to_json(disease_id, "backup_error", error_msg, module="backup")
        return False
    
    try:
        # Get timestamp for this disease
        timestamp = await get_disease_timestamp(disease_id)
        
        # Create backup filename with timestamp
        backup_filename = f"{disease_id}_{timestamp}.json"
        destination_file = os.path.join(backup_dir, backup_filename)
        
        # Check if there's an existing backup for this disease
        existing_backup = find_latest_backup_for_disease(disease_id)
        # Add this code to backup_single_disease function after finding the existing backup
        if existing_backup:
            logger.info(f"Found existing backup for {disease_id}: {os.path.basename(existing_backup)}")
            logger.info(f"Removing old backup and creating new one: {backup_filename}")
        # Remove the old backup
            try:
                os.remove(existing_backup)
            except Exception as e:
                logger.warning(f"Could not remove old backup file: {str(e)}")
        
        # Copy disease JSON file to backup with timestamp
        shutil.copy2(source_file, destination_file)
        logger.info(f"Successfully backed up {disease_id} to {destination_file}")
        
        return True
        
    except Exception as e:
        error_msg = f"Error backing up disease {disease_id}: {str(e)}"
        logger.error(error_msg)
        log_error_to_json(disease_id, "backup_error", error_msg, module="backup")
        return False


async def backup_processed_diseases():
    """Get all processed diseases from the database."""
    logger = setup_logging("backup_processed")
    
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                select(DiseasesDossierStatus).where(DiseasesDossierStatus.status == "processed")
            )
            disease_records = result.scalars().all()
            processed_disease_ids = [record.id for record in disease_records]
            
            if not processed_disease_ids:
                logger.error("No diseases with 'processed' status found in database.")
                return []
                
            logger.info(f"Found {len(processed_disease_ids)} diseases with 'processed' status: {processed_disease_ids}")
            return processed_disease_ids
            
    except Exception as e:
        logger.error(f"Error getting processed diseases: {str(e)}")
        return []


async def backup_and_populate_db():
    """Legacy function for backwards compatibility."""
    logger = setup_logging("backup_legacy")
    logger.warning("Legacy backup function called. This function is deprecated and will backup all diseases at once.")
    
    # Get all processed diseases
    disease_ids = await backup_processed_diseases()
    
    if not disease_ids:
        return False
    
    # Backup each disease one by one
    success_count = 0
    for disease_id in disease_ids:
        result = await backup_single_disease(disease_id)
        if result:
            success_count += 1
    
    logger.info(f"Successfully backed up {success_count}/{len(disease_ids)} diseases")
    return success_count > 0


async def main():
    """Main entry point for backup module."""
    if len(sys.argv) > 1:
        # If disease ID is provided as argument, backup only that disease
        disease_id = sys.argv[1]
        result = await backup_single_disease(disease_id)
        if result:
            print(f"Backup of disease {disease_id} completed successfully.")
        else:
            print(f"Backup of disease {disease_id} failed. Check logs for details.")
    else:
        # Otherwise backup all processed diseases
        disease_ids = await backup_processed_diseases()
        if not disease_ids:
            print("No processed diseases found to backup.")
            return
            
        print(f"Starting backup for {len(disease_ids)} diseases...")
        success_count = 0
        for disease_id in disease_ids:
            result = await backup_single_disease(disease_id)
            if result:
                success_count += 1
        
        print(f"Backup completed: {success_count}/{len(disease_ids)} successful.")


if __name__ == "__main__":
    asyncio.run(main())