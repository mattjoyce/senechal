#!/usr/bin/env python3
import logging
from datetime import datetime, timedelta  
import sqlite3
from typing import Optional

from app.config import SENECHAL_DB_PATH
from app.etl.withings  import WithingsETL
from app.etl.garmin import GarminETL  

def mark_for_update(
    source: str,
    date: datetime,
    raw_updated: Optional[datetime] = None
) -> None:
    """Mark a date's periods for update"""
    conn = sqlite3.connect(SENECHAL_DB_PATH)
    cursor = conn.cursor()

    # For each period type
    for period_type in ['day', 'week', 'month', 'year']:
        # Calculate period boundaries based on type
        if period_type == 'day':
            start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(hour=23, minute=59, second=59)
        elif period_type == 'week':
            start = (date - timedelta(days=date.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        elif period_type == 'month':
            start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if date.month == 12:
                end = date.replace(year=date.year + 1, month=1, day=1)
            else:
                end = date.replace(month=date.month + 1, day=1)
            end = end - timedelta(seconds=1)
        else:  # year
            start = date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = date.replace(month=12, day=31, hour=23, minute=59, second=59)

        # Insert or update period record
        cursor.execute("""
            INSERT INTO source_updates 
                (source, period_type, period_start, period_end, 
                 raw_data_updated, needs_update)
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT (source, period_type, period_start) DO UPDATE SET
                raw_data_updated = COALESCE(?, raw_data_updated),
                needs_update = 1
        """, (source, period_type, start, end, raw_updated, raw_updated))

    conn.commit()
    conn.close()

def run_etl(sources: Optional[list[str]] = None):
    """Run ETL for specified sources or all sources"""
    if sources is None:
        sources = ['withings', 'garmin']
    
    for source in sources:
        try:
            if source == 'withings':
                etl = WithingsETL()
            elif source == 'garmin':
                etl = GarminETL()
            else:
                logging.warning(f"Unknown source: {source}")
                continue
                
            etl.process_pending_updates()
            
        except Exception as error:
            logging.error(f"Error processing {source}: {error}")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logging.info("Starting health data ETL process")
    run_etl()
    logging.info("ETL process complete")