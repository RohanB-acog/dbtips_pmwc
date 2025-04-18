"""
Utility functions for cache management operations.
"""

import os
import logging
import sys
import json
from datetime import datetime
import glob
from pathlib import Path
import asyncio
import tzlocal
import time
from sqlalchemy import select

# Base directories
BASE_DIR = "/app/res-immunology-automation/res_immunology_automation/src/scripts"
CACHE_DIR = os.path.join(BASE_DIR, "cached_data_json")
DISEASE_CACHE_DIR = os.path.join(CACHE_DIR, "disease")
BACKUP_DIR = os.path.join(BASE_DIR, "backedup_cache_data")
LOGS_DIR = os.path.join(CACHE_DIR, "logs")
ERROR_LOGS_DIR = os.path.join(CACHE_DIR, "error_logs")  # New directory for error logs


def setup_logging(log_name):
    """Set up logging configuration for modules."""
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.INFO)
    
    # Create logs directory if it doesn't exist
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # File handler
    log_file = os.path.join(LOGS_DIR, f"{log_name}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


async def get_disease_timestamp(disease_id):
    """Get timestamp from database for a specific disease."""
    logger = setup_logging("disease_timestamp")
    
    try:
        # Import here to avoid circular imports
        sys.path.append(BASE_DIR)
        from build_dossier import SessionLocal
        from db.models import DiseasesDossierStatus
        
        async with SessionLocal() as db:
            # Get the submission time for the specific disease
            result = await db.execute(
                select(DiseasesDossierStatus.submission_time)
                .where(
                    DiseasesDossierStatus.id == disease_id,
                    DiseasesDossierStatus.status == "processed"
                )
            )
            
            submission_time = result.scalar_one_or_none()
            
            if submission_time:
                timestamp = submission_time.strftime("%Y%m%d_%H%M%S")
                logger.info(f"Using database timestamp for disease {disease_id} backup: {timestamp}")
                return timestamp
            else:
                # Fallback to current time if no submission time found
                timestamp = datetime.now(tzlocal.get_localzone()).strftime("%Y%m%d_%H%M%S")
                logger.warning(f"No submission time found for disease {disease_id} in database, using current time: {timestamp}")
                return timestamp

    except Exception as e:
        logger.error(f"Error getting database timestamp for disease {disease_id}: {str(e)}")
        # Fallback to current time
        timestamp = datetime.now(tzlocal.get_localzone()).strftime("%Y%m%d_%H%M%S")
        logger.warning(f"Using current time as fallback: {timestamp}")
        return timestamp


async def create_backup_directories():
    """Create necessary directories for cache management."""
    # Create main backup directory
    os.makedirs(os.path.join(BACKUP_DIR, "disease"), exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(ERROR_LOGS_DIR, exist_ok=True)  # Create error logs directory
    return os.path.join(BACKUP_DIR, "disease")


def log_error_to_json(disease_id, error_type, error_message, module="general", endpoint=None, attempt=None):
    """Log errors to a JSON file in the error_logs directory with module categorization."""
    os.makedirs(ERROR_LOGS_DIR, exist_ok=True)
    
    error_file = os.path.join(ERROR_LOGS_DIR, f"{disease_id}_errors.json")
    
    # Create or update the error log
    try:
        if os.path.exists(error_file):
            with open(error_file, 'r') as f:
                error_log = json.load(f)
        else:
            error_log = {
                "disease_id": disease_id,
                "errors": []
            }
        
        # Add new error with module info
        timestamp = datetime.now(tzlocal.get_localzone()).strftime("%Y-%m-%d %H:%M:%S")
        error_entry = {
            "timestamp": timestamp,
            "module": module,
            "error_type": error_type,
            "message": str(error_message)
        }
        
        if endpoint:
            error_entry["endpoint"] = endpoint
            
        if attempt is not None:
            error_entry["attempt"] = attempt
            
        error_log["errors"].append(error_entry)
        
        # Write back to file
        with open(error_file, 'w') as f:
            json.dump(error_log, f, indent=2)
            
    except Exception as e:
        logger = setup_logging("error_logger")
        logger.error(f"Failed to log error to JSON for disease {disease_id}: {str(e)}")    
    os.makedirs(ERROR_LOGS_DIR, exist_ok=True)
    
    error_file = os.path.join(ERROR_LOGS_DIR, f"{disease_id}_errors.json")
    
    # Create or update the error log
    try:
        if os.path.exists(error_file):
            with open(error_file, 'r') as f:
                error_log = json.load(f)
        else:
            error_log = {
                "disease_id": disease_id,
                "errors": []
            }
        
        # Add new error
        timestamp = datetime.now(tzlocal.get_localzone()).strftime("%Y-%m-%d %H:%M:%S")
        error_entry = {
            "timestamp": timestamp,
            "error_type": error_type,
            "message": str(error_message)
        }
        
        if attempt is not None:
            error_entry["attempt"] = attempt
            
        error_log["errors"].append(error_entry)
        
        # Write back to file
        with open(error_file, 'w') as f:
            json.dump(error_log, f, indent=2)
            
    except Exception as e:
        logger = setup_logging("error_logger")
        logger.error(f"Failed to log error to JSON for disease {disease_id}: {str(e)}")


def find_latest_backup_for_disease(disease_id):
    """Find the latest backup file for a specific disease."""
    backup_dir = os.path.join(BACKUP_DIR, "disease")
    backup_pattern = f"{disease_id}_*.json"
    
    backup_files = glob.glob(os.path.join(backup_dir, backup_pattern))
    if not backup_files:
        return None
    
    # Sort files by modification time (newest first)
    backup_files.sort(key=os.path.getmtime, reverse=True)
    return backup_files[0]


def get_all_disease_ids():
    """Get all disease IDs from JSON files in cache directory."""
    if not os.path.exists(DISEASE_CACHE_DIR):
        return []
    
    json_files = glob.glob(os.path.join(DISEASE_CACHE_DIR, "*.json"))
    return [Path(file).stem for file in json_files]


def check_environment_variables():
    """Check if required environment variables are set."""
    required_vars = ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_HOST"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    return missing_vars


async def retry_with_backoff(func, max_retries=5, initial_backoff=5, *args, **kwargs):
    """Execute a function with exponential backoff retry logic."""
    logger = setup_logging("retry")
    
    retries = 0
    current_backoff = initial_backoff
    
    while retries < max_retries:
        try:
            if retries > 0:
                logger.info(f"Retry attempt {retries}/{max_retries} after {current_backoff}s backoff")
            
            result = await func(*args, **kwargs)
            
            if result:
                return True, None
            else:
                error_msg = f"Function {func.__name__} returned False"
                logger.warning(error_msg)
                retries += 1
                
        except Exception as e:
            error_msg = f"Exception in {func.__name__}: {str(e)}"
            logger.error(error_msg)
            retries += 1
        
        if retries < max_retries:
            logger.info(f"Waiting {current_backoff} seconds before retry...")
            await asyncio.sleep(current_backoff)
            # Exponential backoff with a cap
            current_backoff = min(current_backoff * 2, 60)
    
    return False, f"Failed after {max_retries} retries"

async def create_directories():
    """Create all necessary directories for cache management."""
    # Create main cache directories
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(DISEASE_CACHE_DIR, exist_ok=True)
    
    # Create backup directories
    backup_dir = await create_backup_directories()
    
    # Create log directories
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(ERROR_LOGS_DIR, exist_ok=True)
    
    return backup_dir


if __name__ == "__main__":
    logger = setup_logging("utils")
    logger.info("Testing utilities module")
    
    try:
        backup_dir = asyncio.run(create_backup_directories())
        logger.info(f"Created directories: {backup_dir}")
        
        disease_ids = get_all_disease_ids()
        logger.info(f"Found disease IDs: {disease_ids}")
        
        missing_vars = check_environment_variables()
        if missing_vars:
            logger.warning(f"Missing environment variables: {missing_vars}")
        else:
            logger.info("All required environment variables are set")
            
    except Exception as e:
        logger.error(f"Error in utils: {str(e)}")