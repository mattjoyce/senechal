from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class AnalysisType(str, Enum):
    """Types of analysis that can be performed"""
    SUMMARY = "summary"
    EXTRACTION = "extraction"
    CLASSIFICATION = "classification"
    SENTIMENT = "sentiment"
    KEYWORDS = "keywords"
    CUSTOM = "custom"


class ContentType(str, Enum):
    """Type of content being analyzed"""
    WEBPAGE = "webpage"
    YOUTUBE = "youtube"
    TEXT = "text"
    DOCUMENT = "document"


class AnalyzeRequest(BaseModel):
    """Request model for analysis endpoint"""
    url: Optional[str] = Field(None, description="URL to analyze")
    text: Optional[str] = Field(None, description="Text content to analyze")
    analysis_type: AnalysisType = Field(AnalysisType.SUMMARY, description="Type of analysis to perform")
    custom_prompt: Optional[str] = Field(None, description="Custom prompt for analysis (when analysis_type is CUSTOM)")
    model_name: Optional[str] = Field("gpt-4o", description="LLM model to use for analysis")
    save_result: bool = Field(True, description="Whether to save the analysis result")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/article",
                "analysis_type": "summary",
                "model_name": "gpt-4o",
                "save_result": True
            }
        }


class AnalysisResult(BaseModel):
    """Analysis result data"""
    id: str = Field(..., description="Unique identifier for the analysis")
    title: str = Field(..., description="Title of the analyzed content")
    analysis_type: AnalysisType = Field(..., description="Type of analysis performed")
    content_type: ContentType = Field(..., description="Type of source content")
    source_url: Optional[str] = Field(None, description="Source URL if applicable")
    analysis_content: str = Field(..., description="The analysis result")
    raw_content: str = Field(..., description="Original content that was analyzed")
    model_used: str = Field(..., description="LLM model used for analysis")
    created: datetime = Field(..., description="When the analysis was created")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AnalysisResponse(BaseModel):
    """Standard response model for analysis operations"""
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Analysis result data")


class AnalysisListItem(BaseModel):
    """Summary item for analysis list responses"""
    id: str
    title: str
    analysis_type: AnalysisType
    content_type: ContentType
    created: datetime
    source_url: Optional[str] = None


class AnalysisListResponse(BaseModel):
    """Response model for analysis list endpoint"""
    status: str
    message: str
    data: List[AnalysisListItem]


class AnalysisMetadata(BaseModel):
    """Metadata structure for analysis files"""
    id: str
    title: str
    analysis_type: str
    content_type: str
    source_url: Optional[str] = None
    model_used: str
    created: str
    metadata: Dict[str, Any] = Field(default_factory=dict)