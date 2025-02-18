# app/health/routes.py
from fastapi import APIRouter, Query, Depends
from typing import List, Optional
import sqlite3
from datetime import datetime, timedelta
from ..auth import check_access, get_api_key
from ..config import WITHINGS_DB_PATH
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["health"])

def get_db():
    return sqlite3.connect(WITHINGS_DB_PATH)

# Response Models
class Measurement(BaseModel):
    date: datetime
    type: int
    measure_name: str
    value: float
    unit: str

class HealthResponse(BaseModel):
    measurements: List[Measurement]
    timestamp: datetime = datetime.now()

@router.get("/current", response_model=HealthResponse, dependencies=[Depends(check_access("/health/current"))])
async def get_current_measurements(
    types: Optional[List[int]] = Query(None, description="Filter by measurement types")
):
    """Get latest measurements for all or specified health metrics"""
    db = get_db()
    cursor = db.cursor()
    
    query = """
        SELECT * FROM v_latest_measurements
        WHERE 1=1
    """
    params = []
    
    if types:
        query += " AND type IN (" + ",".join("?" * len(types)) + ")"
        params.extend(types)
    
    cursor.execute(query, params)
    columns = [col[0] for col in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    db.close()
    
    return HealthResponse(measurements=results)

@router.get("/trends", response_model=HealthResponse, dependencies=[Depends(check_access("/health/trends"))])
async def get_health_trends(
    days: int = Query(30, description="Number of days to analyze"),
    types: Optional[List[int]] = Query(None, description="Filter by measurement types"),
    interval: str = Query("day", description="Grouping interval: day, week, month")
):
    """Get trend data for specified period and metrics"""
    db = get_db()
    cursor = db.cursor()
    
    interval_sql = {
        "day": "date(date)",
        "week": "date(date, 'weekday 0')",
        "month": "date(date, 'start of month')"
    }.get(interval, "date(date)")
    
    query = f"""
        SELECT 
            {interval_sql} as period,
            type,
            measure_name,
            AVG(value) as value,
            unit
        FROM v_measurements
        WHERE date >= date('now', ?)
    """
    params = [f'-{days} days']
    
    if types:
        query += " AND type IN (" + ",".join("?" * len(types)) + ")"
        params.extend(types)
    
    query += f" GROUP BY {interval_sql}, type ORDER BY period DESC, type"
    
    cursor.execute(query, params)
    columns = [col[0] for col in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    db.close()
    
    return HealthResponse(measurements=results)

@router.get("/stats", response_model=HealthResponse, dependencies=[Depends(check_access("/health/stats"))])
async def get_health_stats(
    days: int = Query(30, description="Analysis period in days"),
    types: Optional[List[int]] = Query(None, description="Filter by measurement types")
):
    """Get statistical analysis of health metrics"""
    db = get_db()
    cursor = db.cursor()
    
    query = """
        SELECT 
            type,
            measure_name,
            AVG(value) as avg_value,
            MIN(value) as min_value,
            MAX(value) as max_value,
            COUNT(*) as reading_count,
            unit
        FROM v_measurements
        WHERE date >= date('now', ?)
    """
    params = [f'-{days} days']
    
    if types:
        query += " AND type IN (" + ",".join("?" * len(types)) + ")"
        params.extend(types)
    
    query += " GROUP BY type"
    
    cursor.execute(query, params)
    columns = [col[0] for col in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Add classifications for certain metrics (like BP)
    for result in results:
        if result["type"] in [9, 10]:  # BP measurements
            result["classification"] = classify_bp(result["avg_value"], result["type"])
    
    db.close()
    
    return HealthResponse(measurements=results)

def classify_bp(value: float, type_: int) -> str:
    """Classify blood pressure values"""
    if type_ == 10:  # Systolic
        if value < 120: return "Normal"
        if value < 130: return "Elevated"
        if value < 140: return "Stage 1 Hypertension"
        return "Stage 2 Hypertension"
    elif type_ == 9:  # Diastolic
        if value < 80: return "Normal"
        if value < 90: return "Stage 1 Hypertension"
        return "Stage 2 Hypertension"
    return "Unknown"