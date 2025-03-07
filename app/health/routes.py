# app/health/routes.py
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from ..auth import check_access, get_api_key
from ..config import HEALTH_PROFILE_PATH, SENECHAL_DB_PATH, WITHINGS_DB_PATH



# v1 models
class Measurement(BaseModel):
    id: int
    date: datetime  # When the measurement was taken (UTC)
    type: int
    value: float
    measure_name: str
    display_unit: str

    class Config:
        schema_extra = {
            "description": "Health measurement data point. All timestamps are in UTC"
        }


class TrendMeasurement(BaseModel):
    period: datetime
    type: int
    measure_name: str
    avg_value: float
    min_value: float
    max_value: float
    display_unit: str
    reading_count: int


class StatMeasurement(BaseModel):
    type: int
    measure_name: str
    avg_value: float
    min_value: float
    max_value: float
    display_unit: str
    reading_count: int
    classification: Optional[str] = None


class HealthResponse(BaseModel):
    measurements: List[Measurement]
    timestamp: datetime = datetime.utcnow()
    timezone: str = "UTC"

    class Config:
        schema_extra = {"description": "All timestamps are in UTC"}


class TrendResponse(BaseModel):
    trends: List[TrendMeasurement]
    timestamp: datetime = datetime.utcnow()
    timezone: str = "UTC"

    class Config:
        schema_extra = {"description": "All timestamps are in UTC"}


class StatsResponse(BaseModel):
    stats: List[StatMeasurement]
    timestamp: datetime = datetime.utcnow()
    timezone: str = "UTC"

    class Config:
        schema_extra = {"description": "All timestamps are in UTC"}

class Metric(BaseModel):
    metric_id: str
    metric_name: str
    unit: str
    description: str
    group_name: str

class AvailableMetricsResponse(BaseModel):
    metrics: List[Metric]
    timestamp: datetime = datetime.utcnow()
    timezone: str = "UTC"

## v1 models end


## V2 Models start
# Existing models remain...

class MetricValue(BaseModel):
    avg: Optional[float]
    min: Optional[float]
    max: Optional[float]
    unit: str
    sample_count: int
    
    @classmethod
    def create_from_values(cls, avg, min_val, max_val, unit, sample_count):
        """Handle time string values by converting them to minutes"""
        if isinstance(avg, str) and ":" in avg:
            # Convert time format to minutes
            parts = avg.split(":")
            if len(parts) >= 2:
                hours = int(parts[0])
                minutes = int(parts[1])
                avg = hours * 60 + minutes
                
        if isinstance(min_val, str) and ":" in min_val:
            parts = min_val.split(":")
            if len(parts) >= 2:
                hours = int(parts[0])
                minutes = int(parts[1])
                min_val = hours * 60 + minutes
                
        if isinstance(max_val, str) and ":" in max_val:
            parts = max_val.split(":")
            if len(parts) >= 2:
                hours = int(parts[0])
                minutes = int(parts[1])
                max_val = hours * 60 + minutes
        
        # If we've converted time values, update the unit
        if isinstance(avg, str) and ":" in avg:
            unit = "minutes"
                
        return cls(
            avg=float(avg) if avg is not None else None,
            min=float(min_val) if min_val is not None else None,
            max=float(max_val) if max_val is not None else None,
            unit=unit,
            sample_count=sample_count
        )

class PeriodSummary(BaseModel):
    period_start: datetime
    period_end: datetime
    metrics: dict[str, MetricValue]  # metric_id -> values

class HealthSummaryResponse(BaseModel):
    period_type: str
    summaries: List[PeriodSummary]
    generated_at: datetime = datetime.utcnow()

## V2 Models end



router = APIRouter(prefix="/health", tags=["health"])

def read_markdown_file(filepath: str) -> str:
    """
    Read a Markdown file from the given filepath
    
    Args:
        filepath: Path to the Markdown file
        
    Returns:
        str: Content of the Markdown file
        
    Raises:
        HTTPException: If file not found
    """
    try:
        with open(filepath, "r") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Profile data not found. Check HEALTH_PROFILE_PATH configuration.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading profile data: {str(e)}"
        )



def read_json_file(filepath: str) -> dict:
    """
    Read and parse a JSON file from the given filepath

    Args:
        filepath: Path to the JSON file

    Returns:
        dict: Parsed JSON data

    Raises:
        HTTPException: If file not found or invalid JSON
    """
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Profile data not found. Check HEALTH_PROFILE_PATH configuration.",
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid JSON in profile data file")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading profile data: {str(e)}"
        )


def get_db(path:str):
    return sqlite3.connect(path)


@router.get("/availablemetrics", 
            response_model=List[Metric],
            dependencies=[Depends(check_access("/health/availablemetrics"))],
            )
async def get_available_metrics():
    try:
        db = get_db(SENECHAL_DB_PATH)
        cursor = db.cursor()
        cursor.execute("""
            SELECT m.metric_id, m.name, m.unit,m.description, g.name AS group_name FROM metrics AS m
            JOIN metric_groups AS g WHERE g.group_id = m.group_id
            ORDER by m.group_id, m.metric_id
        """)
        # Process and return the results as an array of metrics.
        metrics = []
        for row in cursor:
            metrics.append(Metric(
                metric_id=row[0],
                metric_name=row[1],
                unit=row[2],
                description=row[3],
                group_name=row[4]
            ))
        db.close()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


import logging
# Get logger
logger = logging.getLogger('api')

@router.get("/summary/{period}", 
            response_model=HealthSummaryResponse,
            dependencies=[Depends(check_access("/health/summary"))],
            )
async def get_health_summary(
    period: Literal["day", "week", "month", "year"],
    metrics: str = Query(
        default="all",
        description="Comma-separated metrics/groups or 'all'. Use '@' prefix for metric groups."
    ),
    span: int = Query(
        default=1,
        ge=1,
        le=52,
        description="Number of periods to return"
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of periods to offset from now"
    )
):
    try:
        logger.info(f"get_health_summary called with period={period}, metrics={metrics}, span={span}, offset={offset}")
        # Connect to DB
        logger.debug(f"Connecting to DB: {SENECHAL_DB_PATH}")
        db = get_db(SENECHAL_DB_PATH)
        cursor = db.cursor()
        
        # Build metric filter
        if metrics.lower() == "all":
            logger.debug("Using all metrics")
            metric_filter = ""
            metric_params = []
        else:
            # Handle both metric IDs and group IDs
            metric_parts = metrics.split(',')
            logger.debug(f"Processing metric parts: {metric_parts}")
            
            # Process metric parts to handle groups (prefixed with @)
            metric_ids = []
            for part in metric_parts:
                part = part.strip()
                
                if part.startswith('@'):
                    # This is a group identifier
                    group_id = part[1:]  # Remove the @ prefix
                    logger.debug(f"Processing group: {group_id}")
                    cursor.execute("""
                        SELECT metric_id FROM metrics WHERE group_id = ?
                    """, (group_id,))
                    group_metrics = [row[0] for row in cursor.fetchall()]
                    logger.debug(f"Found {len(group_metrics)} metrics in group {group_id}: {group_metrics}")
                    metric_ids.extend(group_metrics)
                else:
                    # This is an individual metric
                    logger.debug(f"Processing individual metric: {part}")
                    cursor.execute("""
                        SELECT metric_id FROM metrics WHERE metric_id = ?
                    """, (part,))
                    result = cursor.fetchone()
                    if result:
                        logger.debug(f"Found metric: {result[0]}")
                        metric_ids.append(result[0])
                    else:
                        logger.warning(f"Metric not found: {part}")
            
            if not metric_ids:
                logger.warning("No valid metrics specified")
                raise HTTPException(status_code=400, detail="No valid metrics specified")
            
            # Build the SQL filter
            placeholders = ','.join('?' for _ in metric_ids)
            metric_filter = f"AND s.metric_id IN ({placeholders})"
            metric_params = metric_ids
            logger.debug(f"SQL filter: {metric_filter}")
            logger.debug(f"Metric params: {metric_params}")
        
        # Calculate date range
        query = f"""
            SELECT 
                s.period_start,
                s.period_end,
                s.metric_id,
                s.avg_value,
                s.min_value,
                s.max_value,
                s.sample_count,
                m.unit
            FROM summaries s
            JOIN metrics m ON s.metric_id = m.metric_id
            WHERE s.period_type = ?
            AND s.period_start >= date('now', '-' || ? || ' ' || ? || 's')
            {metric_filter}
            ORDER BY s.period_start DESC, s.metric_id
        """
        
        params = [period, span + offset, period]
        if metric_filter:
            params.extend(metric_params)
        
        logger.debug(f"Executing query: {query}")
        logger.debug(f"Query params: {params}")
        cursor.execute(query, params)
        
        # Process results
        summaries = {}
        row_count = 0
        for row in cursor:
            row_count += 1
            period_start = datetime.fromisoformat(row[0])
            if period_start not in summaries:
                summaries[period_start] = {
                    "period_start": period_start,
                    "period_end": datetime.fromisoformat(row[1]),
                    "metrics": {}
                }
            
            # Use our helper method to handle time string values
            summaries[period_start]["metrics"][row[2]] = MetricValue.create_from_values(
                avg=row[3],
                min_val=row[4],
                max_val=row[5],
                sample_count=row[6],
                unit=row[7]
            )
        
        logger.debug(f"Found {row_count} rows, {len(summaries)} periods")
        db.close()
        
        response = HealthSummaryResponse(
            period_type=period,
            summaries=list(summaries.values())
        )
        logger.info(f"Returning response with {len(response.summaries)} summaries")
        return response
        
    except Exception as e:
        logger.error(f"Error in get_health_summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile", 
            dependencies=[Depends(check_access("/health/profile"))],
            response_class=PlainTextResponse,
            )
async def get_health_profile():
    """Get health profile from configured file location"""
    return read_markdown_file(HEALTH_PROFILE_PATH)

@router.get(
    "/current",
    response_model=HealthResponse,
    dependencies=[Depends(check_access("/health/current"))],
    deprecated=True,
)
async def get_current_measurements(
    types: Optional[List[int]] = Query(None, description="Filter by measurement types")
):
    """
    DEPRECATED: This endpoint will be removed in a future version. 
    Use '/health/summary/day' with span=1 instead.
    
    Get latest measurements for all health metrics
    """
    db = get_db(WITHINGS_DB_PATH)
    cursor = db.cursor()

    query = """
        SELECT 
            id, withings_id, date, type, value, measure_name, display_unit, created_at
        FROM v_latest_measurements
        WHERE 1=1
    """
    params = []

    if types:
        query += " AND type IN (" + ",".join("?" * len(types)) + ")"
        params.extend(types)

    cursor.execute(query, params)
    columns = [column[0] for column in cursor.description]
    results = []

    for row in cursor.fetchall():
        measurement_dict = dict(zip(columns, row))
        measurement_dict["date"] = datetime.fromisoformat(measurement_dict["date"])
        measurement_dict["created_at"] = datetime.fromisoformat(
            measurement_dict["created_at"]
        )
        results.append(Measurement(**measurement_dict))

    db.close()
    return HealthResponse(measurements=results)


@router.get(
    "/trends",
    response_model=TrendResponse,
    dependencies=[Depends(check_access("/health/trends"))],
    deprecated=True,
)
async def get_health_trends(
    days: int = Query(30, description="Number of days to analyze"),
    types: Optional[List[int]] = Query(None, description="Filter by measurement types"),
    interval: str = Query("day", description="Grouping interval: day, week, month"),
):
    """
    DEPRECATED: This endpoint will be removed in a future version.
    Use '/health/summary/{period}' with appropriate period and span parameters instead.
    
    Get trend data for specified period and metrics
    """
    db = get_db(WITHINGS_DB_PATH)
    cursor = db.cursor()

    interval_sql = {
        "day": "date(date)",
        "week": "date(date, 'weekday 0')",
        "month": "date(date, 'start of month')",
    }.get(interval, "date(date)")

    query = f"""
        SELECT 
            {interval_sql} as period,
            type,
            measure_name,
            AVG(value) as avg_value,
            MIN(value) as min_value,
            MAX(value) as max_value,
            display_unit,
            COUNT(*) as reading_count
        FROM v_measurements
        WHERE date >= date('now', ?)
    """
    params = [f"-{days} days"]

    if types:
        query += " AND type IN (" + ",".join("?" * len(types)) + ")"
        params.extend(types)

    query += f" GROUP BY {interval_sql}, type ORDER BY period DESC, type"

    cursor.execute(query, params)
    columns = [column[0] for column in cursor.description]
    results = []

    for row in cursor.fetchall():
        trend_dict = dict(zip(columns, row))
        trend_dict["period"] = datetime.fromisoformat(trend_dict["period"])
        results.append(TrendMeasurement(**trend_dict))

    db.close()
    return TrendResponse(trends=results)


@router.get(
    "/stats",
    response_model=StatsResponse,
    dependencies=[Depends(check_access("/health/stats"))],
    deprecated=True,
)
async def get_health_stats(
    days: Optional[int] = Query(30, description="Analysis period in days"),
    types: Optional[List[int]] = Query(
        default=None, description="Filter by measurement types"
    ),
):
    """
    DEPRECATED: This endpoint will be removed in a future version.
    Use '/health/summary/{period}' with appropriate metrics parameters instead.
    
    Get statistical analysis of health metrics
    """
    db = get_db(WITHINGS_DB_PATH)
    cursor = db.cursor()

    query = """
        SELECT 
            type,
            measure_name,
            AVG(value) as avg_value,
            MIN(value) as min_value,
            MAX(value) as max_value,
            display_unit,
            COUNT(*) as reading_count
        FROM v_measurements
        WHERE date >= date('now', ?)
    """
    params = [f"-{days} days"]

    if types:
        query += " AND type IN (" + ",".join("?" * len(types)) + ")"
        params.extend(types)

    query += " GROUP BY type"

    cursor.execute(query, params)
    columns = [column[0] for column in cursor.description]
    results = []

    for row in cursor.fetchall():
        stat_dict = dict(zip(columns, row))

        # Add classifications for certain metrics
        if stat_dict["type"] in [9, 10]:  # BP measurements
            stat_dict["classification"] = classify_bp(
                stat_dict["avg_value"], stat_dict["type"]
            )
        elif stat_dict["type"] == 1:  # Weight
            # You could add BMI classification here if height is available
            pass

        results.append(StatMeasurement(**stat_dict))

    db.close()
    return StatsResponse(stats=results)


def classify_bp(value: float, type_: int) -> str:
    """Classify blood pressure values"""
    if type_ == 10:  # Systolic
        if value < 120:
            return "Normal"
        if value < 130:
            return "Elevated"
        if value < 140:
            return "Stage 1 Hypertension"
        return "Stage 2 Hypertension"
    elif type_ == 9:  # Diastolic
        if value < 80:
            return "Normal"
        if value < 90:
            return "Stage 1 Hypertension"
        return "Stage 2 Hypertension"
    return "Unknown"
