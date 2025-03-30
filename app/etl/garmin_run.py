#!/usr/bin/env python3
import argparse
import logging
import sys
from datetime import datetime, timedelta

from app.etl.garmin import GarminETL

def main():
    """Main entry point for the Garmin ETL process"""
    parser = argparse.ArgumentParser(description="Run Garmin ETL process")
    parser.add_argument("--dry-run", action="store_true", 
                        help="Show what would be done without making changes")
    parser.add_argument("--debug", action="store_true", 
                        help="Enable debug logging")
    parser.add_argument("--since", type=str, 
                        help="Process data since a specific date (DD/MM/YYYY)")
    parser.add_argument("--days", type=int, 
                        help="Process data for the last N days")
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if args.dry_run:
        logging.info("Running in DRY RUN mode - no changes will be made")
    
    etl = GarminETL()
    affected_periods = set()
    
    try:
        if args.since:
            # Process since a specific date
            try:
                target_date = datetime.strptime(args.since, "%d/%m/%Y")
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                current_date = target_date
                
                logging.info(f"Processing data since: {target_date.date()}")
                
                # Generate periods for each day from since date to today
                while current_date <= today:
                    affected_periods.update(etl.identify_affected_periods([current_date]))
                    current_date += timedelta(days=1)
                
                logging.info(f"Identified {len(affected_periods)} periods to process")
                
            except ValueError:
                logging.error(f"Invalid date format: {args.since}. Use DD/MM/YYYY.")
                return 1
                
        elif args.days:
            # Process for last N days
            if args.days < 1:
                logging.error("Days must be greater than 0")
                return 1
                
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = today - timedelta(days=args.days)
            current_date = start_date
            
            logging.info(f"Processing data for the last {args.days} days (since {start_date.date()})")
            
            # Generate periods for each day in the range
            while current_date <= today:
                affected_periods.update(etl.identify_affected_periods([current_date]))
                current_date += timedelta(days=1)
                
            logging.info(f"Identified {len(affected_periods)} periods to process")
            
        else:
            # Process data from garmin summary database
            logging.info("Processing all available Garmin summary data")
            affected_periods = etl.identify_summary_periods()
        
        # Mark periods for update
        etl.mark_periods_for_update(affected_periods, args.dry_run)
        
        # Process the updates if not in dry-run mode
        if not args.dry_run:
            etl.process_pending_updates()
            logging.info("Completed processing Garmin data")
        else:
            logging.info(f"[DRY RUN] Would process {len(affected_periods)} periods")
    
    except Exception as error:
        logging.error(f"Error in Garmin ETL: {error}", exc_info=args.debug)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())