#!/usr/bin/env python3
import logging
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime

from app.config import SENECHAL_DB_PATH


class HealthETL(ABC):
    def __init__(self, source_name: str):
        self.source_name = source_name
        logging.info(f"Initializing {source_name} ETL")

    def get_db(self, path: str) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn

    def process_pending_updates(self):
        """Process all pending updates for this source"""
        senechal_db = self.get_db(SENECHAL_DB_PATH)
        cursor = senechal_db.cursor()
        
        # Get pending updates for this source
        cursor.execute("""
            SELECT * FROM v_pending_updates
            WHERE source = ?
            ORDER BY period_start ASC
        """, (self.source_name,))
        
        pending = cursor.fetchall()
        logging.info(f"Found {len(pending)} periods needing updates for {self.source_name}")
        
        for period in pending:
            try:
                logging.info(
                    f"Processing {period['period_type']} starting {period['period_start']}"
                )
                
                # Calculate summaries
                self.process_period(
                    senechal_db,
                    period['period_type'],
                    datetime.fromisoformat(period['period_start']),
                    datetime.fromisoformat(period['period_end'])
                )
                
                # Mark as processed
                cursor.execute("""
                    UPDATE source_updates
                    SET needs_update = 0,
                        summary_updated = CURRENT_TIMESTAMP
                    WHERE source = ?
                    AND period_type = ?
                    AND period_start = ?
                """, (
                    self.source_name,
                    period['period_type'],
                    period['period_start']
                ))
                
                senechal_db.commit()
                logging.info("✅ Period processed successfully")
                
            except Exception as e:
                logging.error(f"❌ Error processing period: {e}")
                senechal_db.rollback()
                continue
        
        senechal_db.close()

    @abstractmethod
    def process_period(
        self,
        senechal_db: sqlite3.Connection,
        period_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> None:
        """Process data for a specific period"""
        pass