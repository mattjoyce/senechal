"""ETL process for Garmin health data."""
import logging
from datetime import datetime, timedelta
import sqlite3
from typing import Dict, List, Tuple, Set

from app.config import (
    GARMIN_DB_PATH,
    GARMIN_MONITORING_DB_PATH,
    GARMIN_SUMMARY_DB_PATH,
    SENECHAL_DB_PATH,
)
from app.etl.base import HealthETL

# Mapping of summary table metrics to Senechal metrics
GARMIN_METRIC_MAP = {
    # Heart rate metrics
    "hr_avg": "hr",
    "hr_min": "hr_min",
    "hr_max": "hr_max",
    "rhr_avg": "rhr",
    "rhr_min": "rhr_min",
    "rhr_max": "rhr_max",
    "inactive_hr_avg": "inactive_hr",
    # Sleep metrics
    "sleep_avg": "sleep_total",
    "sleep_min": "sleep_min",
    "sleep_max": "sleep_max",
    "rem_sleep_avg": "sleep_rem",
    # Activity metrics
    "steps": "steps",
    "steps_goal": "steps_goal",
    "floors": "floors",
    "floors_goal": "floors_goal",
    "intensity_time": "intensity_total",
    "moderate_activity_time": "intensity_mod",
    "vigorous_activity_time": "intensity_vig",
    # Breathing metrics
    "spo2_avg": "spo2",
    "spo2_min": "spo2_min",
    "rr_waking_avg": "resp_rate",
    "rr_min": "resp_rate_min",
    "rr_max": "resp_rate_max",
    # Stress and other metrics
    "stress_avg": "stress",
    "calories_avg": "calories",
    "calories_bmr_avg": "calories_bmr",
    "calories_active_avg": "calories_active",
    "calories_goal": "calories_goal",
    "weight_avg": "weight",
    "weight_min": "weight_min",
    "weight_max": "weight_max",
}

# Time period mapping between Garmin summary tables and Senechal period types
PERIOD_TYPE_MAP = {
    "years_summary": "year",
    "months_summary": "month",
    "weeks_summary": "week",
    "days_summary": "day",
}


class GarminETL(HealthETL):
    """ETL process for Garmin health data."""
    def __init__(self):
        super().__init__("garmin")

    def identify_affected_periods(self, dates: List[datetime]) -> Set[Tuple]:
        """
        Identify all periods (day, week, month, year) affected by the given dates
        Returns a set of tuples: (period_type, period_start, period_end)
        """
        affected_periods = set()

        for date in dates:
            # Add day period
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)
            affected_periods.add(("day", day_start, day_end))

            # Add week period
            week_start = (date - timedelta(days=date.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            week_end = week_start + timedelta(days=7) - timedelta(microseconds=1)
            affected_periods.add(("week", week_start, week_end))

            # Add month period
            month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if month_start.month == 12:
                month_end = date.replace(year=date.year + 1, month=1, day=1)
            else:
                month_end = date.replace(month=month_start.month + 1, day=1)
            month_end = month_end - timedelta(microseconds=1)
            affected_periods.add(("month", month_start, month_end))

            # Add year period
            year_start = date.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            year_end = date.replace(year=date.year + 1, month=1, day=1) - timedelta(
                microseconds=1
            )
            affected_periods.add(("year", year_start, year_end))

        return affected_periods

    def identify_summary_periods(self) -> Set[Tuple]:
        """
        Identify all periods available in the Garmin summary database
        Returns a set of tuples: (period_type, period_start, period_end)
        """
        affected_periods = set()

        # Connect to Garmin summary database
        summary_db = self.get_db(GARMIN_SUMMARY_DB_PATH)
        cursor = summary_db.cursor()

        # Get all periods from each summary table
        for table_name, period_type in PERIOD_TYPE_MAP.items():
            # Check if the table exists
            cursor.execute(
                f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{table_name}'
            """
            )
            if not cursor.fetchone():
                logging.warning(
                    f"Table {table_name} not found in Garmin summary database"
                )
                continue

            # Get the date field based on table type
            date_field = "day" if table_name == "days_summary" else "first_day"

            # Get all dates in this table
            cursor.execute(
                f"""
                SELECT {date_field} FROM {table_name}
                ORDER BY {date_field}
            """
            )

            for row in cursor.fetchall():
                date_str = row[0]
                try:
                    # Parse the date string into a datetime object
                    date = datetime.fromisoformat(date_str)

                    # Create period start/end based on period type
                    if period_type == "day":
                        period_start = date.replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )
                        period_end = (
                            period_start + timedelta(days=1) - timedelta(microseconds=1)
                        )
                    elif period_type == "week":
                        period_start = date.replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )
                        period_end = (
                            period_start + timedelta(days=7) - timedelta(microseconds=1)
                        )
                    elif period_type == "month":
                        period_start = date.replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )
                        if period_start.month == 12:
                            period_end = date.replace(
                                year=date.year + 1, month=1, day=1
                            )
                        else:
                            period_end = date.replace(
                                month=period_start.month + 1, day=1
                            )
                        period_end = period_end - timedelta(microseconds=1)
                    elif period_type == "year":
                        period_start = date.replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )
                        period_end = date.replace(
                            year=date.year + 1, month=1, day=1
                        ) - timedelta(microseconds=1)

                    affected_periods.add((period_type, period_start, period_end))

                except Exception as exception:
                    logging.error(
                        f"Error parsing date {date_str} from {table_name}: {exception}"
                    )

        summary_db.close()
        return affected_periods

    def mark_periods_for_update(
        self, affected_periods: Set[Tuple], dry_run: bool = False
    ) -> None:
        """Mark the affected periods for update in the database"""
        if dry_run:
            logging.info(
                f"[DRY RUN] Would mark {len(affected_periods)} periods for update:"
            )
            for period_type, start, end in affected_periods:
                logging.info(
                    f"  {period_type}: {start.isoformat()} to {end.isoformat()}"
                )
            return

        conn = sqlite3.connect(SENECHAL_DB_PATH)
        cursor = conn.cursor()

        for period_type, start, end in affected_periods:
            cursor.execute(
                """
                INSERT INTO source_updates 
                    (source, period_type, period_start, period_end, 
                     raw_data_updated, needs_update)
                VALUES ('garmin', ?, ?, ?, CURRENT_TIMESTAMP, 1)
                ON CONFLICT (source, period_type, period_start) DO UPDATE SET
                    raw_data_updated = CURRENT_TIMESTAMP,
                    needs_update = 1
            """,
                (period_type, start, end),
            )

        conn.commit()
        conn.close()
        logging.info(f"Marked {len(affected_periods)} periods for update")

    def process_period(
        self,
        senechal_db: sqlite3.Connection,
        period_type: str,
        start_date: datetime,
        end_date: datetime,
    ) -> None:
        """Process Garmin data for a period"""
        metrics = {}

        # Try to get data from Garmin summary database first
        summary_metrics = self._get_summary_metrics(period_type, start_date, end_date)
        if summary_metrics:
            metrics.update(summary_metrics)
            logging.info(
                f"Retrieved {len(summary_metrics)} metrics from Garmin summary database"
            )
        else:
            logging.info(
                f"No summary data found for {period_type} from {start_date} to {end_date}, using raw data"
            )

            # Fall back to raw data if summary not available
            metrics.update(self._get_heart_metrics(start_date, end_date))
            metrics.update(self._get_sleep_metrics(start_date, end_date))
            metrics.update(self._get_breathing_metrics(start_date, end_date))
            metrics.update(self._get_activity_metrics(start_date, end_date))

        # Save all metrics to senechal db
        self._save_metrics(senechal_db, period_type, start_date, end_date, metrics)

    def _get_summary_metrics(
        self, period_type: str, start_date: datetime, end_date: datetime
    ) -> Dict:
        """Get metrics from Garmin summary database"""
        metrics = {}

        # Connect to Garmin summary database
        try:
            summary_db = self.get_db(GARMIN_SUMMARY_DB_PATH)
            cursor = summary_db.cursor()

            # Find the corresponding summary table
            summary_table = None
            for table, senechal_period in PERIOD_TYPE_MAP.items():
                if senechal_period == period_type:
                    summary_table = table
                    break

            if not summary_table:
                logging.warning(
                    f"No matching summary table for period type {period_type}"
                )
                summary_db.close()
                return metrics

            # Check if the table exists
            cursor.execute(
                f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{summary_table}'
            """
            )
            if not cursor.fetchone():
                logging.warning(
                    f"Table {summary_table} not found in Garmin summary database"
                )
                summary_db.close()
                return metrics

            # Get the date field based on table type
            date_field = "day" if summary_table == "days_summary" else "first_day"

            # Get summary data for the period
            query = f"SELECT * FROM {summary_table} WHERE {date_field} = ?"
            cursor.execute(query, (start_date.date().isoformat(),))

            row = cursor.fetchone()
            if not row:
                logging.warning(
                    f"No summary data found for {period_type} starting {start_date.date()}"
                )
                summary_db.close()
                return metrics

            # Process each column in the summary row
            column_names = [description[0] for description in cursor.description]
            for i, column in enumerate(column_names):
                if column == date_field:
                    continue  # Skip the date field

                # Map Garmin metric to Senechal metric
                senechal_metric = GARMIN_METRIC_MAP.get(column)
                if not senechal_metric:
                    continue  # Skip unmapped metrics

                value = row[i]
                if value is None:
                    continue  # Skip NULL values

                # Handle TIME values by converting to minutes
                if isinstance(value, str) and ":" in value:
                    try:
                        hours, minutes = value.split(":")[:2]
                        value = int(hours) * 60 + int(minutes)
                    except Exception as exception:
                        logging.error(
                            f"Error converting time value {value}: {exception}"
                        )
                        continue

                # Add to metrics dict
                metrics[senechal_metric] = {"avg": value, "count": 1}

                # Check if we have min/max variants to store
                if column.endswith("_avg"):
                    base = column[:-4]
                    min_col = f"{base}_min"
                    max_col = f"{base}_max"

                    # Check if min/max columns exist and are in our mapping
                    if min_col in column_names and base + "_min" in GARMIN_METRIC_MAP:
                        min_idx = column_names.index(min_col)
                        min_value = row[min_idx]
                        if min_value is not None:
                            metrics[senechal_metric]["min"] = min_value

                    if max_col in column_names and base + "_max" in GARMIN_METRIC_MAP:
                        max_idx = column_names.index(max_col)
                        max_value = row[max_idx]
                        if max_value is not None:
                            metrics[senechal_metric]["max"] = max_value

            summary_db.close()

        except Exception as exception:
            logging.error(f"Error getting summary metrics: {exception}")
            return {}

        return metrics

    def _get_heart_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get heart rate related metrics from raw data"""
        metrics = {}
        try:
            garmin_db = self.get_db(GARMIN_DB_PATH)
            monitoring_db = self.get_db(GARMIN_MONITORING_DB_PATH)

            # Get resting heart rate stats
            cursor = garmin_db.cursor()
            cursor.execute(
                """
                SELECT 
                    AVG(resting_heart_rate) as avg_rhr,
                    MIN(resting_heart_rate) as min_rhr,
                    MAX(resting_heart_rate) as max_rhr,
                    COUNT(*) as sample_count
                FROM resting_hr
                WHERE day >= ? AND day < ?
            """,
                (start_date, end_date),
            )
            rhr_stats = cursor.fetchone()

            if rhr_stats and rhr_stats["avg_rhr"]:
                metrics["rhr"] = {
                    "avg": rhr_stats["avg_rhr"],
                    "min": rhr_stats["min_rhr"],
                    "max": rhr_stats["max_rhr"],
                    "count": rhr_stats["sample_count"],
                }

            # Get continuous heart rate stats
            cursor = monitoring_db.cursor()
            cursor.execute(
                """
                SELECT 
                    AVG(heart_rate) as avg_hr,
                    MIN(heart_rate) as min_hr,
                    MAX(heart_rate) as max_hr,
                    COUNT(*) as sample_count
                FROM monitoring_hr
                WHERE timestamp >= ? AND timestamp < ?
            """,
                (start_date, end_date),
            )
            hr_stats = cursor.fetchone()

            if hr_stats and hr_stats["avg_hr"]:
                metrics["hr"] = {
                    "avg": hr_stats["avg_hr"],
                    "min": hr_stats["min_hr"],
                    "max": hr_stats["max_hr"],
                    "count": hr_stats["sample_count"],
                }

            garmin_db.close()
            monitoring_db.close()

        except Exception as error:
            logging.error(f"Error getting heart metrics: {error}")

        return metrics

    def _get_sleep_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get sleep related metrics from raw data"""
        metrics = {}
        try:
            garmin_db = self.get_db(GARMIN_DB_PATH)
            cursor = garmin_db.cursor()

            # Get sleep stats (convert TIME to minutes for consistent storage)
            cursor.execute(
                """
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
            """,
                (start_date, end_date),
            )
            sleep_stats = cursor.fetchone()

            if sleep_stats and sleep_stats["avg_total_sleep"]:
                metrics["sleep_total"] = {
                    "avg": sleep_stats["avg_total_sleep"],
                    "min": sleep_stats["min_total_sleep"],
                    "max": sleep_stats["max_total_sleep"],
                    "count": sleep_stats["sample_count"],
                }
                metrics["sleep_deep"] = {
                    "avg": sleep_stats["avg_deep_sleep"],
                    "count": sleep_stats["sample_count"],
                }
                metrics["sleep_rem"] = {
                    "avg": sleep_stats["avg_rem_sleep"],
                    "count": sleep_stats["sample_count"],
                }
                metrics["sleep_light"] = {
                    "avg": sleep_stats["avg_light_sleep"],
                    "count": sleep_stats["sample_count"],
                }
                if sleep_stats["avg_score"]:
                    metrics["sleep_score"] = {
                        "avg": sleep_stats["avg_score"],
                        "count": sleep_stats["sample_count"],
                    }

            garmin_db.close()

        except Exception as error:
            logging.error(f"Error getting sleep metrics: {error}")

        return metrics

    def _get_breathing_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get breathing related metrics from raw data"""
        metrics = {}
        try:
            monitoring_db = self.get_db(GARMIN_MONITORING_DB_PATH)
            cursor = monitoring_db.cursor()

            # Get SPO2 stats
            cursor.execute(
                """
                SELECT 
                    AVG(pulse_ox) as avg_spo2,
                    MIN(pulse_ox) as min_spo2,
                    MAX(pulse_ox) as max_spo2,
                    COUNT(*) as sample_count
                FROM monitoring_pulse_ox
                WHERE timestamp >= ? AND timestamp < ?
            """,
                (start_date, end_date),
            )
            spo2_stats = cursor.fetchone()

            if spo2_stats and spo2_stats["avg_spo2"]:
                metrics["spo2"] = {
                    "avg": spo2_stats["avg_spo2"],
                    "min": spo2_stats["min_spo2"],
                    "max": spo2_stats["max_spo2"],
                    "count": spo2_stats["sample_count"],
                }

            # Get respiratory rate stats
            cursor.execute(
                """
                SELECT 
                    AVG(rr) as avg_rr,
                    MIN(rr) as min_rr,
                    MAX(rr) as max_rr,
                    COUNT(*) as sample_count
                FROM monitoring_rr
                WHERE timestamp >= ? AND timestamp < ?
            """,
                (start_date, end_date),
            )
            rr_stats = cursor.fetchone()

            if rr_stats and rr_stats["avg_rr"]:
                metrics["resp_rate"] = {
                    "avg": rr_stats["avg_rr"],
                    "min": rr_stats["min_rr"],
                    "max": rr_stats["max_rr"],
                    "count": rr_stats["sample_count"],
                }

            monitoring_db.close()

        except Exception as error:
            logging.error(f"Error getting breathing metrics: {error}")

        return metrics

    def _get_activity_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get activity related metrics from raw data"""
        metrics = {}
        try:
            monitoring_db = self.get_db(GARMIN_MONITORING_DB_PATH)
            cursor = monitoring_db.cursor()

            # Get activity intensity stats (convert TIME to minutes)
            cursor.execute(
                """
                SELECT 
                    AVG(CAST(SUBSTR(moderate_activity_time, 1, 2) AS INTEGER) * 60 + 
                        CAST(SUBSTR(moderate_activity_time, 4, 2) AS INTEGER)) as avg_moderate,
                    AVG(CAST(SUBSTR(vigorous_activity_time, 1, 2) AS INTEGER) * 60 + 
                        CAST(SUBSTR(vigorous_activity_time, 4, 2) AS INTEGER)) as avg_vigorous,
                    COUNT(*) as sample_count
                FROM monitoring_intensity
                WHERE timestamp >= ? AND timestamp < ?
            """,
                (start_date, end_date),
            )
            intensity_stats = cursor.fetchone()

            if intensity_stats and intensity_stats["avg_moderate"]:
                metrics["intensity_mod"] = {
                    "avg": intensity_stats["avg_moderate"],
                    "count": intensity_stats["sample_count"],
                }
                metrics["intensity_vig"] = {
                    "avg": intensity_stats["avg_vigorous"],
                    "count": intensity_stats["sample_count"],
                }

            monitoring_db.close()

        except Exception as error:
            logging.error(f"Error getting activity metrics: {error}")

        return metrics

    def _save_metrics(
        self,
        senechal_db: sqlite3.Connection,
        period_type: str,
        start_date: datetime,
        end_date: datetime,
        metrics: Dict,
    ) -> None:
        """Save processed metrics to Senechal DB"""
        cursor = senechal_db.cursor()

        for metric_id, values in metrics.items():
            cursor.execute(
                """
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
            """,
                (
                    period_type,
                    start_date,
                    end_date,
                    metric_id,
                    values.get("avg"),
                    values.get("min"),
                    values.get("max"),
                    values.get("count", 0),
                ),
            )

        senechal_db.commit()
        logging.info(
            f"Saved {len(metrics)} metrics for {period_type} period: {start_date} to {end_date}"
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    etl = GarminETL()
    etl.process_pending_updates()
