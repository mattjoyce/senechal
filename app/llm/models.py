"""Models for the unified LLM API."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class OutputFormat(str, Enum):
    """Output format options for LLM responses"""
    MARKDOWN = "markdown"
    JSON = "json"
    TEXT = "text"


class LLMRequest(BaseModel):
    """Request model for unified LLM endpoint"""
    model: str = Field("gpt-4o", description="LLM model to use")
    prompt: str = Field(..., description="Named prompt (e.g., 'extract_learning', 'analyze_summary') or custom prompt text")
    query_text: Optional[str] = Field(None, description="Direct text input to process")
    query_url: Optional[str] = Field(None, description="URL to scrape and process")
    save_result: bool = Field(False, description="Whether to save result to file and return URL")
    output_format: OutputFormat = Field(OutputFormat.TEXT, description="Output format for the response")
    custom_title: Optional[str] = Field(None, description="Custom title for saved results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for saved results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "gpt-4o",
                "prompt": "analyze_summary",
                "query_url": "https://example.com/article",
                "save_result": True,
                "output_format": "markdown"
            }
        }


class LLMResult(BaseModel):
    """LLM processing result data"""
    id: str = Field(..., description="Unique identifier for the result")
    title: str = Field(..., description="Title of the processed content")
    prompt_used: str = Field(..., description="Prompt that was used")
    model_used: str = Field(..., description="LLM model used")
    source_type: str = Field(..., description="Type of source (url, text)")
    source_url: Optional[str] = Field(None, description="Source URL if applicable")
    content: str = Field(..., description="The LLM-generated content")
    raw_content: Optional[str] = Field(None, description="Original content that was processed")
    output_format: OutputFormat = Field(..., description="Format of the output")
    created: datetime = Field(..., description="When the result was created")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LLMResponse(BaseModel):
    """Standard response model for LLM operations"""
    status: str = Field(..., description="Response status (success/error)")
    message: str = Field(..., description="Response message")
    data: Optional[Union[Dict[str, Any], str]] = Field(None, description="Result data - either LLMResult dict, URL string, or direct content")


class LLMListItem(BaseModel):
    """Summary item for LLM result list responses"""
    id: str
    title: str
    prompt_used: str
    model_used: str
    source_type: str
    created: datetime
    source_url: Optional[str] = None


class LLMListResponse(BaseModel):
    """Response model for LLM results list endpoint"""
    status: str
    message: str
    data: list[LLMListItem]


class PromptInfo(BaseModel):
    """Information about available prompts"""
    name: str = Field(..., description="Prompt identifier")
    description: str = Field(..., description="Description of what the prompt does")
    category: str = Field(..., description="Category of the prompt (analysis, learning, etc.)")


class PromptsResponse(BaseModel):
    """Response model for available prompts endpoint"""
    status: str
    message: str
    data: list[PromptInfo]


class ExtractRequest(BaseModel):
    """Request model for extract convenience endpoint"""
    query_url: Optional[str] = None
    query_text: Optional[str] = None
    model: str = "gpt-4o"
    save_result: bool = True


class AnalyzeRequest(BaseModel):
    """Request model for analyze convenience endpoint"""
    analysis_type: str = "summary"
    query_url: Optional[str] = None
    query_text: Optional[str] = None
    model: str = "gpt-4o"
    save_result: bool = True


class CustomRequest(BaseModel):
    """Request model for custom processing endpoint"""
    custom_prompt: str
    query_url: Optional[str] = None
    query_text: Optional[str] = None
    model: str = "gpt-4o"
    save_result: bool = False
    output_format: OutputFormat = OutputFormat.TEXT