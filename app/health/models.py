# app/health/models.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, HttpUrl


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

# Rowing-specific models
class RowingExtractRequest(BaseModel):
    """
    Request model for the rowing workout image extraction endpoint.
    
    Attributes:
        image_url: URL of the rowing machine workout screenshot to process
        workout_date: Optional timestamp when the workout was performed. 
                     If not provided, the current date will be used.
    """
    image_url: HttpUrl
    workout_date: Optional[datetime] = None


class RowingData(BaseModel):
    """
    Model representing extracted rowing workout data from an image.
    Used as an intermediary before database storage.
    
    Attributes:
        workout_type: Type of rowing workout - either "distance" (continuous) 
                     or "interval" (with rest periods)
        duration_seconds: Total duration of the workout in seconds
        distance_meters: Total distance rowed in meters
        avg_split: Average split time in seconds per 500m, typically only 
                  meaningful for continuous/distance workouts
    """
    workout_type: str  # "distance" or "interval"
    duration_seconds: float
    distance_meters: float
    avg_split: Optional[float] = None  # Average split in seconds per 500m


class RowingWorkout(BaseModel):
    """
    Model representing a rowing workout stored in the database.
    Includes all rowing metrics plus metadata like ID and timestamp.
    
    Attributes:
        id: Unique identifier for the workout record
        date: Timestamp when the workout was performed (UTC)
        workout_type: Type of workout - "distance" or "interval"
        duration_seconds: Total duration of the workout in seconds
        distance_meters: Total distance rowed in meters
        avg_split: Average split time in seconds per 500m (may be null for interval workouts)
    """
    id: int
    date: datetime
    workout_type: str
    duration_seconds: float
    distance_meters: float  
    avg_split: Optional[float] = None


class RowingResponse(BaseModel):
    """
    Response model for the rowing workout retrieval endpoint.
    Includes a list of workouts and metadata about the response.
    
    Attributes:
        workouts: List of rowing workout records matching the query parameters
        timestamp: UTC timestamp when the response was generated
        timezone: Timezone identifier for the timestamps in the response (always "UTC")
    
    Example:
        {
            "workouts": [
                {
                    "id": 1,
                    "date": "2023-10-15T08:30:00",
                    "workout_type": "distance",
                    "duration_seconds": 1800.5,
                    "distance_meters": 5000.0,
                    "avg_split": 120.0
                }
            ],
            "timestamp": "2023-10-16T14:22:10.123456",
            "timezone": "UTC"
        }
    """
    workouts: List[RowingWorkout]
    timestamp: datetime = datetime.utcnow()
    timezone: str = "UTC"