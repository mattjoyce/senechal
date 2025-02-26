#!/usr/bin/env python3
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Tuple

from app.config import WITHINGS_DB_PATH, SENECHAL_DB_PATH
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
    
    def get_last_processed_uid(self) -> int:
        """Get the last processed Withings measurement UID"""
        conn = sqlite3.connect(SENECHAL_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT value FROM sync_metadata 
            WHERE source = 'withings' AND key = 'last_uid'
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        return int(result[0]) if result else 0
    
    def set_last_processed_uid(self, uid: int, dry_run: bool = False) -> None:
        """Update the last processed Withings measurement UID"""
        if dry_run:
            logging.info(f"[DRY RUN] Would update last_uid to {uid}")
            return
            
        conn = sqlite3.connect(SENECHAL_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO sync_metadata (source, key, value, updated_at)
            VALUES ('withings', 'last_uid', ?, CURRENT_TIMESTAMP)
        """, (str(uid),))
        
        conn.commit()
        conn.close()
    
    def get_new_measurements(self, last_uid: int) -> List[Dict]:
        """Get new measurements from Withings DB with UID > last_uid"""
        conn = sqlite3.connect(WITHINGS_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM measurements
            WHERE withings_id > ?
            ORDER BY withings_id
        """, (last_uid,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def identify_affected_periods(self, measurement_dates: List[datetime]) -> Set[Tuple]:
        """
        Identify all periods (day, week, month, year) affected by the given dates
        Returns a set of tuples: (period_type, period_start, period_end)
        """
        affected_periods = set()
        
        for date in measurement_dates:
            # Add day period
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)
            affected_periods.add(('day', day_start, day_end))
            
            # Add week period
            week_start = (date - timedelta(days=date.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            week_end = week_start + timedelta(days=7) - timedelta(microseconds=1)
            affected_periods.add(('week', week_start, week_end))
            
            # Add month period
            month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if month_start.month == 12:
                month_end = date.replace(year=date.year+1, month=1, day=1)
            else:
                month_end = date.replace(month=month_start.month+1, day=1)
            month_end = month_end - timedelta(microseconds=1)
            affected_periods.add(('month', month_start, month_end))
            
            # Add year period
            year_start = date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            year_end = date.replace(year=date.year+1, month=1, day=1) - timedelta(microseconds=1)
            affected_periods.add(('year', year_start, year_end))
        
        return affected_periods
    
    def mark_periods_for_update(self, affected_periods: Set[Tuple], dry_run: bool = False) -> None:
        """Mark the affected periods for update in the database"""
        if dry_run:
            logging.info(f"[DRY RUN] Would mark {len(affected_periods)} periods for update:")
            for period_type, start, end in affected_periods:
                logging.info(f"  {period_type}: {start.isoformat()} to {end.isoformat()}")
            return
        
        conn = sqlite3.connect(SENECHAL_DB_PATH)
        cursor = conn.cursor()
        
        for period_type, start, end in affected_periods:
            cursor.execute("""
                INSERT INTO source_updates 
                    (source, period_type, period_start, period_end, 
                     raw_data_updated, needs_update)
                VALUES ('withings', ?, ?, ?, CURRENT_TIMESTAMP, 1)
                ON CONFLICT (source, period_type, period_start) DO UPDATE SET
                    raw_data_updated = CURRENT_TIMESTAMP,
                    needs_update = 1
            """, (period_type, start, end))
        
        conn.commit()
        conn.close()
        logging.info(f"Marked {len(affected_periods)} periods for update")
    
    def process_new_measurements(self, dry_run: bool = False) -> None:
        """Process new Withings measurements"""
        # Get the last processed UID
        last_uid = self.get_last_processed_uid()
        logging.info(f"Last processed UID: {last_uid}")
        
        # Get new measurements
        new_measurements = self.get_new_measurements(last_uid)
        if not new_measurements:
            logging.info("No new measurements found")
            return
        
        logging.info(f"Found {len(new_measurements)} new measurements")
        
        # Find the highest UID for updating later
        highest_uid = max(m['withings_id'] for m in new_measurements)
        
        # Extract measurement dates
        measurement_dates = []
        for m in new_measurements:
            try:
                date_str = m['date']
                if isinstance(date_str, str):
                    measurement_dates.append(datetime.fromisoformat(date_str))
                else:
                    # If date is already a datetime object
                    measurement_dates.append(date_str)
            except Exception as e:
                logging.error(f"Error parsing date for measurement {m['withings_id']}: {e}")
        
        # Identify affected periods
        affected_periods = self.identify_affected_periods(measurement_dates)
        logging.info(f"Identified {len(affected_periods)} affected periods")
        
        # Mark periods for update
        self.mark_periods_for_update(affected_periods, dry_run)
        
        # Run the ETL process if not dry run
        if not dry_run:
            self.process_pending_updates()
            logging.info("ETL process completed")
        else:
            logging.info("[DRY RUN] Would process updates for affected periods")
        
        # Update the last processed UID
        self.set_last_processed_uid(highest_uid, dry_run)

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
        logging.info(f"Updated summaries for {period_type} period: {start_date} to {end_date}")


if __name__ == "__main__":
    # This allows the module to be run directly for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    etl = WithingsETL()
    etl.process_pending_updates()