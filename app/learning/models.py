"""Models for the learning API."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class ContentType(str, Enum):
    """Type of content for learning items."""

    WEBPAGE = "webpage"
    YOUTUBE = "youtube"
    TEXT = "text"


class ConfidenceLevel(int, Enum):
    """Confidence level for learning recall."""

    FORGOT = 1  # Completely forgot
    DIFFICULT = 2  # Remembered with difficulty
    PARTIAL = 3  # Partially remembered
    GOOD = 4  # Remembered well
    PERFECT = 5  # Perfect recall


class LearningItemRequest(BaseModel):
    """Request model for creating a learning item from a URL."""

    url: Optional[HttpUrl] = None
    text: Optional[str] = None


class LearningItem(BaseModel):
    """Model representing a learning item."""

    id: int
    title: str
    source_url: Optional[str] = None
    content_type: ContentType
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    next_review: Optional[datetime] = None
    status: str = "active"  # active, completed, archived


class LearningPoint(BaseModel):
    """Model representing a specific learning point within an item."""

    id: int
    item_id: int
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    importance: int = 1  # 1-5 scale


class LearningReview(BaseModel):
    """Model representing a review of a learning point."""

    id: int
    point_id: int
    confidence_level: ConfidenceLevel
    review_date: datetime = Field(default_factory=datetime.utcnow)
    next_review_date: Optional[datetime] = None


class LearningResponse(BaseModel):
    """Response model for learning API endpoints."""

    status: str
    message: str
    data: Optional[dict] = None


class LearningItemResponse(BaseModel):
    """Response model for a learning item with its learning points."""

    item: LearningItem
    points: List[LearningPoint]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LearningListResponse(BaseModel):
    """Response model for listing learning items."""

    items: List[LearningItem]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FeedbackRequest(BaseModel):
    """Request model for providing feedback on a learning item."""

    item_id: int
    confidence_level: ConfidenceLevel