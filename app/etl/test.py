#!/usr/bin/env python3
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List

from app.config import (
    WITHINGS_DB_PATH,
    GARMIN_DB_PATH,
    GARMIN_MONITORING_DB_PATH,
    SENECHAL_DB_PATH
)
from app.etl.run import mark_for_update, run_etl

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def check_withings_data():
    """Check latest data in Withings DB"""
    conn = sqlite3.connect(WITHINGS_DB_PATH)
    cursor = conn.cursor()
    
    print("\n=== Latest Withings Data ===")
    cursor.execute("""
        SELECT date, type, value,
            CASE type
                WHEN 1 THEN 'Weight'
                WHEN 4 THEN 'Height'
                WHEN 5 THEN 'Fat Free Mass'
                WHEN 6 THEN 'Fat Ratio'
                WHEN 8 THEN 'Fat Mass Weight'
                WHEN 9 THEN 'Diastolic BP'
                WHEN 10 THEN 'Systolic BP'
                WHEN 11 THEN 'Heart Rate'
                WHEN 76 THEN 'Muscle Mass'
                WHEN 77 THEN 'Hydration'
                WHEN 88 THEN 'Bone Mass'
                WHEN 170 THEN 'Visceral Fat'
            END as measure_name
        FROM measurements
        WHERE date >= date('now', '-1 day')
        ORDER BY date DESC
    """)
    
    for row in cursor.fetchall():
        print(f"{row[0]} - {row[3]}: {row[2]}")
    
    conn.close()

def check_garmin_data():
    """Check latest data in Garmin DBs"""
    # Check heart rate data
    conn = sqlite3.connect(GARMIN_MONITORING_DB_PATH)
    cursor = conn.cursor()
    
    print("\n=== Latest Garmin Heart Rate Data ===")
    cursor.execute("""
        SELECT timestamp, heart_rate
        FROM monitoring_hr
        WHERE timestamp >= datetime('now', '-1 day')
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"{row[0]} - HR: {row[1]}")
    
    # Check sleep data
    conn = sqlite3.connect(GARMIN_DB_PATH)
    cursor = conn.cursor()
    
    print("\n=== Latest Garmin Sleep Data ===")
    cursor.execute("""
        SELECT day, total_sleep, deep_sleep, rem_sleep
        FROM sleep
        WHERE day >= date('now', '-7 days')
        ORDER BY day DESC
        LIMIT 3
    """)
    
    for row in cursor.fetchall():
        print(f"{row[0]} - Total: {row[1]}, Deep: {row[2]}, REM: {row[3]}")
    
    conn.close()

def process_single_day():
    """Process a single day of data"""
    # Mark yesterday for processing
    test_date = datetime.now() - timedelta(days=1)
    print(f"\nProcessing data for {test_date.date()}")
    
    mark_for_update('withings', test_date)
    mark_for_update('garmin', test_date)
    
    # Run ETL
    run_etl()

def check_summaries():
    """Check processed summaries"""
    conn = sqlite3.connect(SENECHAL_DB_PATH)
    cursor = conn.cursor()
    
    print("\n=== Processed Summaries ===")
    cursor.execute("""
        SELECT 
            m.group_id,
            m.name,
            s.period_start,
            s.avg_value,
            s.min_value,
            s.max_value,
            s.sample_count,
            m.unit
        FROM summaries s
        JOIN metrics m ON s.metric_id = m.metric_id
        WHERE s.period_type = 'day'
        AND s.period_start >= date('now', '-1 day')
        ORDER BY m.group_id, m.name
    """)
    
    current_group = None
    for row in cursor.fetchall():
        if row[0] != current_group:
            current_group = row[0]
            print(f"\n{current_group.upper()}:")
        
        print(f"{row[1]} ({row[7]})")
        print(f"  Period: {row[2]}")
        
        avg_val = "N/A" if row[3] is None else f"{row[3]:.2f}"
        min_val = "N/A" if row[4] is None else f"{row[4]:.2f}"
        max_val = "N/A" if row[5] is None else f"{row[5]:.2f}"
        
        print(f"  Avg: {avg_val}, Min: {min_val}, Max: {max_val}")
        print(f"  Samples: {row[6]}")
    
    conn.close()

def main():
    """Run ETL test"""
    setup_logging()
    logging.info("Starting ETL test")
    
    # First check source data
    check_withings_data()
    check_garmin_data()
    
    # Process single day
    process_single_day()
    
    # Check results
    check_summaries()
    
    logging.info("ETL test complete")

if __name__ == "__main__":
    main()