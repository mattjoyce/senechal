#!/usr/bin/env python3
import logging
from datetime import datetime
import sqlite3

from app.config import WITHINGS_DB_PATH
from app.etl.base import HealthETL

# Withings measurement type mapping
WITHINGS_METRIC_MAP = {
    1: 'weight',
    4: 'height',
    5: 'fat_free_mass',
    6: 'fat_ratio',
    8: 'fat_mass',
    76: 'muscle_mass',
    77: 'hydration',
    88: 'bone_mass',
    170: 'visceral_fat',
    9: 'bp_diastolic',
    10: 'bp_systolic',
    11: 'hr'
}

class WithingsETL(HealthETL):
    def __init__(self):
        super().__init__("withings")

    def process_period(
        self,
        senechal_db: sqlite3.Connection,
        period_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> None:
        """Process Withings data for a period"""
        withings_db = self.get_db(WITHINGS_DB_PATH)
        cursor = withings_db.cursor()
        
        # Query raw measurements for period
        cursor.execute("""
            SELECT 
                type,
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value,
                COUNT(*) as sample_count
            FROM measurements
            WHERE date >= ? AND date < ?
            GROUP BY type
        """, (start_date, end_date))
        
        results = cursor.fetchall()
        withings_db.close()
        
        # Map Withings types to Senechal metrics
        for row in results:
            metric_id = WITHINGS_METRIC_MAP.get(row['type'])
            if not metric_id:
                continue
                
            # Insert/update summary
            senechal_db.execute("""
                INSERT INTO summaries (
                    period_type, period_start, period_end,
                    metric_id, avg_value, min_value, max_value,
                    sample_count, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT (period_type, period_start, metric_id) DO UPDATE SET
                    avg_value = excluded.avg_value,
                    min_value = excluded.min_value,
                    max_value = excluded.max_value,
                    sample_count = excluded.sample_count,
                    last_updated = CURRENT_TIMESTAMP
            """, (
                period_type,
                start_date,
                end_date,
                metric_id,
                row['avg_value'],
                row['min_value'],
                row['max_value'],
                row['sample_count']
            ))
        
        senechal_db.commit()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    etl = WithingsETL()
    etl.process_pending_updates()