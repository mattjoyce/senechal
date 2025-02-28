from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import date, datetime


class MCPFunctionParameter(BaseModel):
    type: str
    description: str
    enum: Optional[List[str]] = None
    format: Optional[str] = None


class MCPFunctionParameterObject(BaseModel):
    type: str = "object"
    properties: Dict[str, MCPFunctionParameter]
    required: List[str]


class MCPFunctionReturn(BaseModel):
    type: str
    properties: Dict[str, Any]


class MCPFunction(BaseModel):
    name: str
    description: str
    parameters: MCPFunctionParameterObject
    returns: MCPFunctionReturn


class MCPDefinition(BaseModel):
    schema_version: str = "v1"
    functions: List[MCPFunction]


# Request models
class GetHealthDataRequest(BaseModel):
    start_date: date = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: date = Field(..., description="End date in YYYY-MM-DD format")
    metrics: List[str] = Field(..., description="List of health metrics to retrieve")


# Response models
class HealthDataPoint(BaseModel):
    date: datetime
    metric: str
    value: Union[float, int, str]
    unit: Optional[str] = None


class GetHealthDataResponse(BaseModel):
    data: List[HealthDataPoint]


# Error models
class MCPError(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None