#!/usr/bin/env python3
import logging
from datetime import datetime
import sqlite3
from typing import Dict, List, Tuple

from app.config import (
    GARMIN_DB_PATH,
    GARMIN_MONITORING_DB_PATH,
    GARMIN_SUMMARY_DB_PATH
)
from app.etl.base import HealthETL

class GarminETL(HealthETL):
    def __init__(self):
        super().__init__("garmin")

    def process_period(
        self,
        senechal_db: sqlite3.Connection,
        period_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> None:
        """Process Garmin data for a period"""
        # Process each data type
        metrics = {}
        
        # Get heart rate metrics
        metrics.update(self._get_heart_metrics(start_date, end_date))
        
        # Get sleep metrics
        metrics.update(self._get_sleep_metrics(start_date, end_date))
        
        # Get breathing metrics
        metrics.update(self._get_breathing_metrics(start_date, end_date))
        
        # Get activity metrics
        metrics.update(self._get_activity_metrics(start_date, end_date))
        
        # Save all metrics to senechal db
        self._save_metrics(senechal_db, period_type, start_date, end_date, metrics)

    def _get_heart_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get heart rate related metrics"""
        metrics = {}
        garmin_db = self.get_db(GARMIN_DB_PATH)
        monitoring_db = self.get_db(GARMIN_MONITORING_DB_PATH)
        
        # Get resting heart rate stats
        cursor = garmin_db.cursor()
        cursor.execute("""
            SELECT 
                AVG(resting_heart_rate) as avg_rhr,
                MIN(resting_heart_rate) as min_rhr,
                MAX(resting_heart_rate) as max_rhr,
                COUNT(*) as sample_count
            FROM resting_hr
            WHERE day >= ? AND day < ?
        """, (start_date, end_date))
        rhr_stats = cursor.fetchone()
        
        if rhr_stats and rhr_stats['avg_rhr']:
            metrics['rhr'] = {
                'avg': rhr_stats['avg_rhr'],
                'min': rhr_stats['min_rhr'],
                'max': rhr_stats['max_rhr'],
                'count': rhr_stats['sample_count']
            }
            
        # Get continuous heart rate stats
        cursor = monitoring_db.cursor()
        cursor.execute("""
            SELECT 
                AVG(heart_rate) as avg_hr,
                MIN(heart_rate) as min_hr,
                MAX(heart_rate) as max_hr,
                COUNT(*) as sample_count
            FROM monitoring_hr
            WHERE timestamp >= ? AND timestamp < ?
        """, (start_date, end_date))
        hr_stats = cursor.fetchone()
        
        if hr_stats and hr_stats['avg_hr']:
            metrics['hr'] = {
                'avg': hr_stats['avg_hr'],
                'min': hr_stats['min_hr'],
                'max': hr_stats['max_hr'],
                'count': hr_stats['sample_count']
            }
        
        garmin_db.close()
        monitoring_db.close()
        return metrics

    def _get_sleep_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get sleep related metrics"""
        metrics = {}
        garmin_db = self.get_db(GARMIN_DB_PATH)
        cursor = garmin_db.cursor()
        
        # Get sleep stats (convert TIME to minutes for consistent storage)
        cursor.execute("""
            SELECT 
                AVG(CAST(SUBSTR(total_sleep, 1, 2) AS INTEGER) * 60 + 
                    CAST(SUBSTR(total_sleep, 4, 2) AS INTEGER)) as avg_total_sleep,
                MIN(CAST(SUBSTR(total_sleep, 1, 2) AS INTEGER) * 60 + 
                    CAST(SUBSTR(total_sleep, 4, 2) AS INTEGER)) as min_total_sleep,
                MAX(CAST(SUBSTR(total_sleep, 1, 2) AS INTEGER) * 60 + 
                    CAST(SUBSTR(total_sleep, 4, 2) AS INTEGER)) as max_total_sleep,
                AVG(CAST(SUBSTR(deep_sleep, 1, 2) AS INTEGER) * 60 + 
                    CAST(SUBSTR(deep_sleep, 4, 2) AS INTEGER)) as avg_deep_sleep,
                AVG(CAST(SUBSTR(rem_sleep, 1, 2) AS INTEGER) * 60 + 
                    CAST(SUBSTR(rem_sleep, 4, 2) AS INTEGER)) as avg_rem_sleep,
                AVG(CAST(SUBSTR(light_sleep, 1, 2) AS INTEGER) * 60 + 
                    CAST(SUBSTR(light_sleep, 4, 2) AS INTEGER)) as avg_light_sleep,
                AVG(score) as avg_score,
                COUNT(*) as sample_count
            FROM sleep
            WHERE day >= ? AND day < ?
        """, (start_date, end_date))
        sleep_stats = cursor.fetchone()
        
        if sleep_stats and sleep_stats['avg_total_sleep']:
            metrics['sleep_total'] = {
                'avg': sleep_stats['avg_total_sleep'],
                'min': sleep_stats['min_total_sleep'],
                'max': sleep_stats['max_total_sleep'],
                'count': sleep_stats['sample_count']
            }
            metrics['sleep_deep'] = {
                'avg': sleep_stats['avg_deep_sleep'],
                'count': sleep_stats['sample_count']
            }
            metrics['sleep_rem'] = {
                'avg': sleep_stats['avg_rem_sleep'],
                'count': sleep_stats['sample_count']
            }
            metrics['sleep_light'] = {
                'avg': sleep_stats['avg_light_sleep'],
                'count': sleep_stats['sample_count']
            }
            if sleep_stats['avg_score']:
                metrics['sleep_score'] = {
                    'avg': sleep_stats['avg_score'],
                    'count': sleep_stats['sample_count']
                }
        
        garmin_db.close()
        return metrics

    def _get_breathing_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get breathing related metrics"""
        metrics = {}
        monitoring_db = self.get_db(GARMIN_MONITORING_DB_PATH)
        cursor = monitoring_db.cursor()
        
        # Get SPO2 stats
        cursor.execute("""
            SELECT 
                AVG(pulse_ox) as avg_spo2,
                MIN(pulse_ox) as min_spo2,
                MAX(pulse_ox) as max_spo2,
                COUNT(*) as sample_count
            FROM monitoring_pulse_ox
            WHERE timestamp >= ? AND timestamp < ?
        """, (start_date, end_date))
        spo2_stats = cursor.fetchone()
        
        if spo2_stats and spo2_stats['avg_spo2']:
            metrics['spo2'] = {
                'avg': spo2_stats['avg_spo2'],
                'min': spo2_stats['min_spo2'],
                'max': spo2_stats['max_spo2'],
                'count': spo2_stats['sample_count']
            }
            
        # Get respiratory rate stats
        cursor.execute("""
            SELECT 
                AVG(rr) as avg_rr,
                MIN(rr) as min_rr,
                MAX(rr) as max_rr,
                COUNT(*) as sample_count
            FROM monitoring_rr
            WHERE timestamp >= ? AND timestamp < ?
        """, (start_date, end_date))
        rr_stats = cursor.fetchone()
        
        if rr_stats and rr_stats['avg_rr']:
            metrics['resp_rate'] = {
                'avg': rr_stats['avg_rr'],
                'min': rr_stats['min_rr'],
                'max': rr_stats['max_rr'],
                'count': rr_stats['sample_count']
            }
        
        monitoring_db.close()
        return metrics

    def _get_activity_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get activity related metrics"""
        metrics = {}
        monitoring_db = self.get_db(GARMIN_MONITORING_DB_PATH)
        cursor = monitoring_db.cursor()
        
        # Get activity intensity stats (convert TIME to minutes)
        cursor.execute("""
            SELECT 
                AVG(CAST(SUBSTR(moderate_activity_time, 1, 2) AS INTEGER) * 60 + 
                    CAST(SUBSTR(moderate_activity_time, 4, 2) AS INTEGER)) as avg_moderate,
                AVG(CAST(SUBSTR(vigorous_activity_time, 1, 2) AS INTEGER) * 60 + 
                    CAST(SUBSTR(vigorous_activity_time, 4, 2) AS INTEGER)) as avg_vigorous,
                COUNT(*) as sample_count
            FROM monitoring_intensity
            WHERE timestamp >= ? AND timestamp < ?
        """, (start_date, end_date))
        intensity_stats = cursor.fetchone()
        
        if intensity_stats and intensity_stats['avg_moderate']:
            metrics['intensity_mod'] = {
                'avg': intensity_stats['avg_moderate'],
                'count': intensity_stats['sample_count']
            }
            metrics['intensity_vig'] = {
                'avg': intensity_stats['avg_vigorous'],
                'count': intensity_stats['sample_count']
            }
        
        monitoring_db.close()
        return metrics

    def _save_metrics(
        self,
        senechal_db: sqlite3.Connection,
        period_type: str,
        start_date: datetime,
        end_date: datetime,
        metrics: Dict
    ) -> None:
        """Save processed metrics to Senechal DB"""
        cursor = senechal_db.cursor()
        
        for metric_id, values in metrics.items():
            cursor.execute("""
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
                values.get('avg'),
                values.get('min'),
                values.get('max'),
                values.get('count', 0)
            ))
        
        senechal_db.commit()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    etl = GarminETL()
    etl.process_pending_updates()