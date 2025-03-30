#!/usr/bin/env python3
import argparse
import logging
import sys
from datetime import datetime

from app.etl.withings import WithingsETL

def main():
    """Main entry point for the Withings ETL process"""
    parser = argparse.ArgumentParser(description="Run Withings ETL process")
    parser.add_argument("--dry-run", action="store_true", 
                        help="Show what would be done without making changes")
    parser.add_argument("--debug", action="store_true", 
                        help="Enable debug logging")
    parser.add_argument("--force-date", type=str, 
                        help="Force processing for a specific date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if args.dry_run:
        logging.info("Running in DRY RUN mode - no changes will be made")
    
    etl = WithingsETL()
    
    try:
        if args.force_date:
            # Process a specific date if requested
            try:
                target_date = datetime.fromisoformat(args.force_date)
                logging.info(f"Forcing process for date: {target_date.date()}")
                
                # Create a set with just this date's periods
                affected_periods = etl.identify_affected_periods([target_date])
                
                # Mark these periods for update
                etl.mark_periods_for_update(affected_periods, args.dry_run)
                
                # Process the updates if not in dry-run mode
                if not args.dry_run:
                    etl.process_pending_updates()
                    logging.info(f"Completed processing for date: {target_date.date()}")
                else:
                    logging.info(f"[DRY RUN] Would process updates for date: {target_date.date()}")
            
            except ValueError:
                logging.error(f"Invalid date format: {args.force_date}. Use YYYY-MM-DD.")
                return 1
        else:
            # Process all new measurements
            etl.process_new_measurements(args.dry_run)
    
    except Exception as e:
        logging.error(f"Error in Withings ETL: {e}", exc_info=args.debug)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())