import asyncio
import sys
import glob
from datetime import datetime
from sqlalchemy import select, func
from .utils import (
    setup_logging,
    log_error_to_json,
    BASE_DIR,
    LOGS_DIR
)
import tzlocal

# Import database models
sys.path.append(BASE_DIR)
from build_dossier import SessionLocal
from db.models import DiseasesDossierStatus, DiseaseOperationHistory

async def get_disease_info(disease_id):
    """Get disease information from database."""
    logger = setup_logging("history_tracker")
    
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                select(DiseasesDossierStatus).where(DiseasesDossierStatus.id == disease_id)
            )
            disease_record = result.scalar_one_or_none()
            
            if disease_record:
                return {
                    "id": disease_record.id,
                    "status": disease_record.status,
                    "submission_time": disease_record.submission_time,
                    "processed_time": disease_record.processed_time
                }
            else:
                logger.warning(f"No database record found for disease {disease_id}")
                return None
                
    except Exception as e:
        logger.error(f"Error fetching disease info for {disease_id}: {str(e)}")
        return None

async def record_regeneration(disease_id, operation_type="regenerate", status="success", notes=None):
    """Record a regeneration event for a disease."""
    logger = setup_logging("history_tracker")
    logger.info(f"Recording {operation_type} event for disease {disease_id}")
    
    try:
        async with SessionLocal() as db:
            # Get current timestamp
            current_time = datetime.now(tzlocal.get_localzone())
            
            # Get disease info from database
            disease_info = await get_disease_info(disease_id)
            
            # Create new history entry
            event = DiseaseOperationHistory(
                disease_id=disease_id,
                operation_type=operation_type,
                status=status,
                timestamp=current_time,
                notes=notes,
                database_status=disease_info.get("status") if disease_info else "unknown",
                processed_time=disease_info.get("processed_time") if disease_info else None
            )
            
            db.add(event)
            await db.commit()
            
            logger.info(f"Successfully recorded {operation_type} event for disease {disease_id}")
            return True
            
    except Exception as e:
        error_msg = f"Error recording event for disease {disease_id}: {str(e)}"
        logger.error(error_msg)
        log_error_to_json(disease_id, "history_error", error_msg, module="history_tracker")
        return False

async def get_regeneration_history(disease_id):
    """Get regeneration history for a disease."""
    logger = setup_logging("history_tracker")
    
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                select(DiseaseOperationHistory)
                .where(DiseaseOperationHistory.disease_id == disease_id)
                .order_by(DiseaseOperationHistory.timestamp.desc())
            )
            history_records = result.scalars().all()
            
            if not history_records:
                return None
                
            history = {
                "disease_id": disease_id,
                "disease_name": "Unknown",  # Name not stored in DiseasesDossierStatus
                "total_operations": len(history_records),
                "events": [
                    {
                        "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "operation": record.operation_type,
                        "status": record.status,
                        "database_status": record.database_status,
                        "processed_time": record.processed_time.strftime("%Y-%m-%d %H:%M:%S") if record.processed_time else None,
                        "notes": record.notes
                    } for record in history_records
                ]
            }
            return history
    except Exception as e:
        logger.error(f"Error reading history for disease {disease_id}: {str(e)}")
        return None

async def print_last_operation_summary(disease_id=None):
    """Print summary of last operations for a disease or all diseases."""
    logger = setup_logging("history_tracker")
    
    try:
        print("\n===== DISEASE OPERATION HISTORY =====")
        
        async with SessionLocal() as db:
            if disease_id:
                # Print history for specific disease
                history = await get_regeneration_history(disease_id)
                if history and history["events"]:
                    last_op = history["events"][0]  # Most recent operation
                    # Get second-to-last operation if available
                    previous_op = history["events"][1] if len(history["events"]) > 1 else None
                    
                    print(f"Disease ID: {disease_id}")
                    print(f"Total operations: {history['total_operations']}")
                    if previous_op:
                        print(f"Last operation: {previous_op['operation']} ({previous_op['status']})")
                        print(f"Last operation time: {previous_op['timestamp']}")
                    else:
                        print("Only one operation recorded")
                        
                    # Get current info from database
                    disease_info = await get_disease_info(disease_id)
                    if disease_info and disease_info.get("processed_time"):
                        print(f"Last processed time: {disease_info['processed_time'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(disease_info['processed_time'], datetime) else disease_info['processed_time']}")
                    print("=====================================")
                else:
                    print(f"No operation history found for disease {disease_id}")
            else:
                # Print history for all diseases with recorded history
                result = await db.execute(
                    select(DiseaseOperationHistory.disease_id)
                    .distinct()
                    .order_by(DiseaseOperationHistory.disease_id)
                )
                disease_ids = [row.disease_id for row in result]
                
                if not disease_ids:
                    print("No operation history found for any disease")
                    return
                
                print(f"Found history for {len(disease_ids)} diseases")
                
                for d_id in disease_ids[:5]:  # Limit to 5 to avoid flooding
                    history = await get_regeneration_history(d_id)
                    if history and history["events"]:
                        last_op = history["events"][0]
                        previous_op = history["events"][1] if len(history["events"]) > 1 else None
                        
                        print(f"\nDisease ID: {d_id}")
                        print(f"Total operations: {history['total_operations']}")
                        if previous_op:
                            print(f"Last operation: {previous_op['operation']} ({previous_op['status']})")
                            print(f"Last operation time: {previous_op['timestamp']}")
                        else:
                            print("Only one operation recorded")
                
                if len(disease_ids) > 5:
                    print(f"\n... and {len(disease_ids) - 5} more diseases with history")
                
                print("=====================================")
                
    except Exception as e:
        logger.error(f"Error printing operation summary: {str(e)}")
        print(f"Error reading operation history: {str(e)}")

async def get_monthly_stats(month=None, year=None):
    """Get monthly statistics for disease operations."""
    logger = setup_logging("history_tracker")
    
    try:
        # If month/year not specified, use current month/year
        if not month or not year:
            now = datetime.now()
            month = month or now.month
            year = year or now.year
            
        async with SessionLocal() as db:
            # Get counts grouped by disease_id
            result = await db.execute(
                select(
                    DiseaseOperationHistory.disease_id,
                    func.count().label('operation_count'),
                    DiseaseOperationHistory.operation_type
                )
                .where(
                    func.extract('year', DiseaseOperationHistory.timestamp) == year,
                    func.extract('month', DiseaseOperationHistory.timestamp) == month
                )
                .group_by(DiseaseOperationHistory.disease_id, DiseaseOperationHistory.operation_type)
            )
            
            monthly_stats = {
                "year": year,
                "month": month,
                "total_operations": 0,
                "operations_by_disease": {},
                "operations_by_type": {
                    "regenerate": 0,
                    "backup": 0,
                    "restore": 0,
                    "clear": 0,
                    "full": 0
                }
            }
            
            for row in result:
                disease_id = row.disease_id
                count = row.operation_count
                op_type = row.operation_type
                
                # Update disease-specific counts
                if disease_id not in monthly_stats["operations_by_disease"]:
                    monthly_stats["operations_by_disease"][disease_id] = 0
                monthly_stats["operations_by_disease"][disease_id] += count
                
                # Update operation type counts
                if op_type in monthly_stats["operations_by_type"]:
                    monthly_stats["operations_by_type"][op_type] += count
                else:
                    monthly_stats["operations_by_type"][op_type] = count
                
                monthly_stats["total_operations"] += count
                
            return monthly_stats
            
    except Exception as e:
        logger.error(f"Error getting monthly stats: {str(e)}")
        return None

async def print_monthly_stats(month=None, year=None):
    """Print monthly statistics to console."""
    stats = await get_monthly_stats(month, year)
    
    if not stats:
        print("Could not retrieve monthly statistics")
        return
        
    if stats["total_operations"] == 0:
        print(f"No operations found for {stats['month']}/{stats['year']}")
        return
        
    print(f"\n===== MONTHLY STATISTICS: {stats['month']}/{stats['year']} =====")
    print(f"Total operations: {stats['total_operations']}")
    
    print("\nOperations by type:")
    for op_type, count in stats["operations_by_type"].items():
        if count > 0:
            print(f"  {op_type}: {count}")
    
    print("\nTop 5 diseases by operation count:")
    sorted_diseases = sorted(stats["operations_by_disease"].items(), key=lambda x: x[1], reverse=True)
    for disease_id, count in sorted_diseases[:5]:
        print(f"  {disease_id}: {count} operations")
        
    print("=====================================")

async def main():
    """Main entry point for history tracker module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Track and report disease operation history")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Record command
    record_parser = subparsers.add_parser("record", help="Record a new operation")
    record_parser.add_argument("disease_id", help="Disease ID")
    record_parser.add_argument("--operation", "-o", default="regenerate", help="Operation type")
    record_parser.add_argument("--status", "-s", default="success", help="Operation status")
    record_parser.add_argument("--notes", "-n", help="Additional notes")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Report operation history")
    report_parser.add_argument("--disease-id", "-d", help="Specific disease ID to report on")
    
    # Monthly stats command
    stats_parser = subparsers.add_parser("stats", help="Show monthly statistics")
    stats_parser.add_argument("--month", "-m", type=int, help="Month (1-12)")
    stats_parser.add_argument("--year", "-y", type=int, help="Year")
    
    args = parser.parse_args()
    
    if args.command == "record":
        success = await record_regeneration(
            args.disease_id, 
            operation_type=args.operation, 
            status=args.status, 
            notes=args.notes
        )
        if success:
            print(f"Successfully recorded {args.operation} event for disease {args.disease_id}")
        else:
            print(f"Failed to record {args.operation} event for disease {args.disease_id}")
            
    elif args.command == "report":
        await print_last_operation_summary(args.disease_id)
        
    elif args.command == "stats":
        await print_monthly_stats(args.month, args.year)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())