# app/health/routes.py
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
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


## v1 models end


## V2 Models start
# Existing models remain...

class MetricValue(BaseModel):
    avg: Optional[float]
    min: Optional[float]
    max: Optional[float]
    unit: str
    sample_count: int

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

@router.get("/health/summary/{period}", response_model=HealthSummaryResponse)
async def get_health_summary(
    period: Literal["day", "week", "month", "year"],
    metrics: str = Query(
        default="all",
        description="Comma-separated metrics/groups or 'all'"
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
        # Connect to DB
        db = get_db(SENECHAL_DB_PATH)
        cursor = db.cursor()
        
        # Build metric filter
        if metrics.lower() == "all":
            metric_filter = ""
        else:
            # Handle both metric IDs and group IDs
            metric_parts = metrics.split(',')
            # Check if each part is a metric ID or group ID
            metric_ids = []
            for part in metric_parts:
                cursor.execute("""
                    SELECT metric_id FROM metrics WHERE metric_id = ?
                    UNION
                    SELECT metric_id FROM metrics WHERE group_id = ?
                """, (part, part))
                metric_ids.extend(row[0] for row in cursor.fetchall())
            
            if not metric_ids:
                raise HTTPException(status_code=400, detail="No valid metrics specified")
            metric_filter = f"AND metric_id IN ({','.join('?' for _ in metric_ids)})"
        
        # Calculate date range
        query = f"""
            SELECT 
                period_start,
                period_end,
                metric_id,
                avg_value,
                min_value,
                max_value,
                sample_count,
                m.unit
            FROM summaries s
            JOIN metrics m ON s.metric_id = m.metric_id
            WHERE period_type = ?
            AND period_start >= date('now', '-' || ? || ' ' || ? || 's')
            {metric_filter}
            ORDER BY period_start DESC, metric_id
        """
        
        params = [period, span + offset, period]
        if metric_filter:
            params.extend(metric_ids)
            
        cursor.execute(query, params)
        
        # Process results
        summaries = {}
        for row in cursor:
            period_start = datetime.fromisoformat(row[0])
            if period_start not in summaries:
                summaries[period_start] = {
                    "period_start": period_start,
                    "period_end": datetime.fromisoformat(row[1]),
                    "metrics": {}
                }
            
            summaries[period_start]["metrics"][row[2]] = {
                "avg": row[3],
                "min": row[4],
                "max": row[5],
                "sample_count": row[6],
                "unit": row[7]
            }
        
        db.close()
        
        return HealthSummaryResponse(
            period_type=period,
            summaries=list(summaries.values())
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile", dependencies=[Depends(check_access("/health/profile"))])
async def get_health_profile():
    """Get health profile from configured file location"""
    return read_json_file(HEALTH_PROFILE_PATH)


@router.get(
    "/current",
    response_model=HealthResponse,
    dependencies=[Depends(check_access("/health/current"))],
)
async def get_current_measurements(
    types: Optional[List[int]] = Query(None, description="Filter by measurement types")
):
    """Get latest measurements for all health metrics"""
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
)
async def get_health_trends(
    days: int = Query(30, description="Number of days to analyze"),
    types: Optional[List[int]] = Query(None, description="Filter by measurement types"),
    interval: str = Query("day", description="Grouping interval: day, week, month"),
):
    """Get trend data for specified period and metrics"""
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
)
async def get_health_stats(
    days: Optional[int] = Query(30, description="Analysis period in days"),
    types: Optional[List[int]] = Query(
        default=None, description="Filter by measurement types"
    ),
):
    """Get statistical analysis of health metrics"""
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
