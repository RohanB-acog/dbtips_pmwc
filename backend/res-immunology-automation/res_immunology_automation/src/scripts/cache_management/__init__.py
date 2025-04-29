"""
Cache management modules for handling disease data cache operations.

This package provides modules for:
- Backing up individual disease cache files
- Clearing cache for specific diseases
- Regenerating cache data for specific diseases with retry logic
- Restoring individual diseases from backup
- Tracking history of disease operations
- Analyzing differences between backup and regenerated files
- Utility functions for cache management operations

Each operation can be performed on a single disease or multiple diseases,
with proper error handling and logging.
"""

# Import main functions for API
from .backup import backup_single_disease, backup_processed_diseases, get_processed_diseases_ordered_by_time
from .clear_cache import clear_single_disease, clear_and_create_empty_files
from .regenerate import regenerate_single_disease, regenerate_cache, update_disease_status
from .restore import restore_single_disease, restore_from_backup
from .history_tracker import (
    record_regeneration,
    get_regeneration_history,
    print_last_operation_summary,
    get_monthly_stats,
    print_monthly_stats
)
from .diff_analyzer import (
    analyze_disease_diff,
    print_diff_summary,
    get_latest_diff_report
)
from .utils import (
    setup_logging, 
    create_backup_directories, 
    get_disease_timestamp,
    log_error_to_json,
    find_latest_backup_for_disease,
    retry_with_backoff
)

__all__ = [
    # Backup operations
    'backup_single_disease',
    'backup_processed_diseases',
    
    # Clear cache operations
    'clear_single_disease',
    'clear_and_create_empty_files',
    'ensure_backup_exists'
    # Regeneration operations
    'regenerate_single_disease',
    'regenerate_cache',
    'update_disease_status',
    
    # Restore operations
    'restore_single_disease',
    'restore_from_backup',
    
    # History tracking operations
    'record_regeneration',
    'get_regeneration_history',
    'print_last_operation_summary',
    'get_monthly_stats',
    'print_monthly_stats',
    
    # Diff analysis operations
    'analyze_disease_diff',
    'print_diff_summary',
    'get_latest_diff_report',
    
    # Utility functions
    'setup_logging',
    'create_backup_directories',
    'get_disease_timestamp',
    'log_error_to_json',
    'find_latest_backup_for_disease',
    'retry_with_backoff'
]
