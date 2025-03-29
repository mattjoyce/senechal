# app/health/models.py
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

# Existing health models could go here

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