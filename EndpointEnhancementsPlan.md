# Health Endpoints Enhancement Plan

## Overview
This plan outlines the refactoring of health-related endpoints in the Senechal API to improve maintainability and consistency. The current implementation includes redundant endpoints that directly access device-specific databases, while a more standardized approach would be to use the Senechal database exclusively.

## Goals
1. Enhance `/health/summary` to support comprehensive metric filtering, including metric groups
2. Remove redundant endpoints that duplicate functionality
3. Standardize API to use only Senechal DB, eliminating direct dependencies on device-specific databases

## Implementation Details

### 1. Enhance `/health/summary` endpoint
The `/health/summary` endpoint will be enhanced to support:
- Individual metric requests
- Multiple metric requests
- Metric group requests (using '@' prefix)
- Any combination of the above

**Implementation:**
```python
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
        # Connect to DB
        db = get_db(SENECHAL_DB_PATH)
        cursor = db.cursor()
        
        # Build metric filter
        if metrics.lower() == "all":
            metric_filter = ""
            metric_params = []
        else:
            # Handle both metric IDs and group IDs
            metric_parts = metrics.split(',')
            
            # Process metric parts to handle groups (prefixed with @)
            metric_ids = []
            for part in metric_parts:
                part = part.strip()
                
                if part.startswith('@'):
                    # This is a group identifier
                    group_id = part[1:]  # Remove the @ prefix
                    cursor.execute("""
                        SELECT metric_id FROM metrics WHERE group_id = ?
                    """, (group_id,))
                    metric_ids.extend(row[0] for row in cursor.fetchall())
                else:
                    # This is an individual metric
                    cursor.execute("""
                        SELECT metric_id FROM metrics WHERE metric_id = ?
                    """, (part,))
                    result = cursor.fetchone()
                    if result:
                        metric_ids.append(result[0])
            
            if not metric_ids:
                raise HTTPException(status_code=400, detail="No valid metrics specified")
            
            # Build the SQL filter
            placeholders = ','.join('?' for _ in metric_ids)
            metric_filter = f"AND s.metric_id IN ({placeholders})"
            metric_params = metric_ids
        
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
            
            # Use our helper method to handle time string values
            summaries[period_start]["metrics"][row[2]] = MetricValue.create_from_values(
                avg=row[3],
                min_val=row[4],
                max_val=row[5],
                sample_count=row[6],
                unit=row[7]
            )
        
        db.close()
        
        return HealthSummaryResponse(
            period_type=period,
            summaries=list(summaries.values())
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

Notes on implementation:
- Any duplicates arising from metrics being specified both individually and in groups will be handled by SQL's `IN` clause behavior
- Dictionary-based result processing naturally eliminates duplicates

### 2. Remove Redundant Endpoints
After enhancing `/health/summary`, the following endpoints will be deprecated and removed:

1. `/health/current` - Redundant as it only provides Withings data; latest data can be obtained from `/health/summary/day` with span=1
2. `/health/trends` - Functionality covered by `/health/summary` with period and span parameters
3. `/health/stats` - Statistical analysis functionality covered by metrics in `/health/summary`

## Migration Strategy & Order of Operations

1. First, implement and test the enhanced `/health/summary` endpoint
2. Add deprecation notices to the endpoints scheduled for removal
3. Remove endpoints in the following order:
   - `/health/current`
   - `/health/trends`
   - `/health/stats`
4. Update documentation to reflect the new API structure
5. Communicate changes to API users

## Benefits

- Simplified codebase with fewer endpoints to maintain
- Consistent data source (Senechal DB only)
- All health data accessible through a single, flexible endpoint
- Better integration of data from multiple sources (Withings, Garmin)
- More flexible filtering with metric groups support