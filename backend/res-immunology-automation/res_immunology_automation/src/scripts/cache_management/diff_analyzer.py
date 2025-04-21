import os
import json
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import select
from .utils import (
    setup_logging,
    find_latest_backup_for_disease,
    log_error_to_json,
    BASE_DIR,
    DISEASE_CACHE_DIR,
    BACKUP_DIR
)

# Import database models
sys.path.append(BASE_DIR)
from build_dossier import SessionLocal
from db.models import DiseaseDiffReport

def count_items(obj):
    """Count items in a dictionary, list, or nested structure."""
    if isinstance(obj, dict):
        count = len(obj)
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                count += count_items(v)
        return count
    elif isinstance(obj, list):
        count = len(obj)
        for item in obj:
            if isinstance(item, (dict, list)):
                count += count_items(item)
        return count
    else:
        return 0

def compare_section(backup_section, current_section, path=""):
    """Compare a section between backup and current file."""
    diff = {
        "path": path,
        "added": 0,
        "removed": 0,
        "changed": 0
    }
    
    if backup_section is None and current_section is not None:
        diff["added"] = count_items(current_section)
        return diff
    elif backup_section is not None and current_section is None:
        diff["removed"] = count_items(backup_section)
        return diff
    
    if type(backup_section) != type(current_section):
        diff["changed"] = 1
        return diff
        
    if isinstance(backup_section, dict):
        backup_keys = set(backup_section.keys())
        current_keys = set(current_section.keys())
        
        added_keys = current_keys - backup_keys
        removed_keys = backup_keys - current_keys
        common_keys = backup_keys.intersection(current_keys)
        
        diff["added"] += len(added_keys)
        diff["removed"] += len(removed_keys)
        
        for key in common_keys:
            sub_path = f"{path}.{key}" if path else key
            sub_diff = compare_section(backup_section[key], current_section[key], sub_path)
            
            diff["added"] += sub_diff["added"]
            diff["removed"] += sub_diff["removed"]
            diff["changed"] += sub_diff["changed"]
            
    elif isinstance(backup_section, list):
        len_diff = len(current_section) - len(backup_section)
        if len_diff > 0:
            diff["added"] += len_diff
        elif len_diff < 0:
            diff["removed"] += abs(len_diff)
        
        if backup_section and current_section and all(isinstance(x, dict) for x in backup_section + current_section):
            id_fields = ["id", "ID", "Id", "identifier", "name", "Name", "title", "Title"]
            
            common_id = None
            for field in id_fields:
                if any(field in item for item in backup_section) and any(field in item for item in current_section):
                    common_id = field
                    break
            
            if common_id:
                backup_map = {}
                current_map = {}
                
                for item in backup_section:
                    if common_id in item:
                        item_id = item.get(common_id)
                        if isinstance(item_id, (str, int, float, bool, tuple)):
                            backup_map[item_id] = item
                
                for item in current_section:
                    if common_id in item:
                        item_id = item.get(common_id)
                        if isinstance(item_id, (str, int, float, bool, tuple)):
                            current_map[item_id] = item
                
                backup_ids = set(backup_map.keys())
                current_ids = set(current_map.keys())
                
                added_ids = current_ids - backup_ids
                removed_ids = backup_ids - current_ids
                common_ids = backup_ids.intersection(current_ids)
                
                diff["added"] += len(added_ids)
                diff["removed"] += len(removed_ids)
                
                for item_id in common_ids:
                    if backup_map[item_id] != current_map[item_id]:
                        diff["changed"] += 1
                        
            else:
                for i, (backup_item, current_item) in enumerate(zip(backup_section, current_section)):
                    if backup_item != current_item:
                        diff["changed"] += 1
                        
    else:
        if backup_section != current_section:
            diff["changed"] += 1
    
    return diff

async def analyze_disease_diff(disease_id):
    """Analyze differences between backup and current disease file."""
    logger = setup_logging("diff_analyzer")
    logger.info(f"Analyzing differences for disease {disease_id}")
    
    try:
        # Find latest backup file
        backup_file = find_latest_backup_for_disease(disease_id)
        
        if not backup_file:
            error_msg = f"No backup found for disease {disease_id}"
            logger.error(error_msg)
            return None
            
        # Get current file
        current_file = os.path.join(DISEASE_CACHE_DIR, f"{disease_id}.json")
        
        if not os.path.exists(current_file):
            error_msg = f"Current file not found for disease {disease_id}"
            logger.error(error_msg)
            return None
            
        # Load both files
        try:
            with open(backup_file, "r") as f:
                backup_data = json.load(f)
                
            with open(current_file, "r") as f:
                current_data = json.load(f)
        except json.JSONDecodeError as e:
            error_msg = f"Error parsing JSON for disease {disease_id}: {str(e)}"
            logger.error(error_msg)
            log_error_to_json(disease_id, "diff_analysis_error", error_msg, module="diff_analyzer")
            return None
            
        # Initialize diff report
        diff_report = {
            "disease_id": disease_id,
            "backup_file": os.path.basename(backup_file),
            "current_file": os.path.basename(current_file),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "changes_detected": False,
            "sections": {}
        }
        
        # Get all unique section keys from both files
        all_sections = set(backup_data.keys()).union(set(current_data.keys()))
        
        # Compare each section
        for section in all_sections:
            backup_section = backup_data.get(section)
            current_section = current_data.get(section)
            
            if backup_section is None and current_section is None:
                continue

            try:
                section_diff = compare_section(backup_section, current_section, section)
                
                if section_diff["added"] > 0 or section_diff["removed"] > 0 or section_diff["changed"] > 0:
                    diff_report["changes_detected"] = True
                    diff_report["sections"][section] = section_diff
            except Exception as e:
                logger.warning(f"Error comparing section '{section}' for disease {disease_id}: {str(e)}")
                diff_report["sections"][section] = {
                    "path": section,
                    "added": 0,
                    "removed": 0,
                    "changed": 0,
                    "error": str(e)
                }
                diff_report["changes_detected"] = True
                
        # Save diff report to database
        async with SessionLocal() as db:
            db_report = DiseaseDiffReport(
                disease_id=disease_id,
                backup_file=os.path.basename(backup_file),
                current_file=os.path.basename(current_file),
                changes_detected=diff_report["changes_detected"],
                sections=diff_report["sections"]
            )
            db.add(db_report)
            await db.commit()
            
        logger.info(f"Diff analysis completed for disease {disease_id}")
        return diff_report
        
    except Exception as e:
        error_msg = f"Error analyzing differences for disease {disease_id}: {str(e)}"
        logger.error(error_msg)
        log_error_to_json(disease_id, "diff_analysis_error", error_msg, module="diff_analyzer")
        return None

async def print_diff_summary(diff_report):
    """Print a summary of the differences to the console."""
    if not diff_report:
        print("No diff report available")
        return
        
    print(f"\n===== DIFF ANALYSIS: {diff_report['disease_id']} =====")
    print(f"Backup file: {diff_report['backup_file']}")
    print(f"Current file: {diff_report['current_file']}")
    print(f"Analysis time: {diff_report['timestamp']}")
    
    if not diff_report["changes_detected"]:
        print("No changes detected between backup and current files")
        print("=====================================")
        return
        
    print("\nChanges by section:")
    for section, diff in diff_report["sections"].items():
        if "error" in diff:
            print(f"  {section}: Error during comparison - {diff['error']}")
            continue
            
        changes = []
        if diff["added"] > 0:
            changes.append(f"{diff['added']} added")
        if diff["removed"] > 0:
            changes.append(f"{diff['removed']} removed")
        if diff["changed"] > 0:
            changes.append(f"{diff['changed']} changed")
            
        print(f"  {section}: {', '.join(changes)}")
        
    print("=====================================")

async def get_latest_diff_report(disease_id):
    """Get the latest diff report for a disease from the database."""
    logger = setup_logging("diff_analyzer")
    
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                select(DiseaseDiffReport)
                .where(DiseaseDiffReport.disease_id == disease_id)
                .order_by(DiseaseDiffReport.timestamp.desc())
                .limit(1)
            )
            report = result.scalar_one_or_none()
            
            if not report:
                return None
                
            return {
                "disease_id": report.disease_id,
                "backup_file": report.backup_file,
                "current_file": report.current_file,
                "timestamp": report.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "changes_detected": report.changes_detected,
                "sections": report.sections
            }
    except Exception as e:
        logger.error(f"Error getting latest diff report for disease {disease_id}: {str(e)}")
        return None

async def main():
    """Main entry point for diff analyzer module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze differences between backup and current disease files")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    analyze_parser = subparsers.add_parser("analyze", help="Analyze differences for a disease")
    analyze_parser.add_argument("disease_id", help="Disease ID")
    
    report_parser = subparsers.add_parser("report", help="Show latest diff report for a disease")
    report_parser.add_argument("disease_id", help="Disease ID")
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        diff_report = await analyze_disease_diff(args.disease_id)
        if diff_report:
            await print_diff_summary(diff_report)
        else:
            print(f"Failed to analyze differences for disease {args.disease_id}")
            
    elif args.command == "report":
        diff_report = await get_latest_diff_report(args.disease_id)
        if diff_report:
            await print_diff_summary(diff_report)
        else:
            print(f"No diff report found for disease {args.disease_id}")
            
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())