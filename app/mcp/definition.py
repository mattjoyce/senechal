from .schema import (
    MCPDefinition,
    MCPFunction,
    MCPFunctionParameterObject,
    MCPFunctionParameter,
    MCPFunctionReturn,
)


# Define the MCP function for retrieving health data
GET_HEALTH_DATA = MCPFunction(
    name="get_health_data",
    description="Retrieves health data for a specific date range and metrics",
    parameters=MCPFunctionParameterObject(
        properties={
            "start_date": MCPFunctionParameter(
                type="string",
                description="Start date in YYYY-MM-DD format",
                format="date",
            ),
            "end_date": MCPFunctionParameter(
                type="string",
                description="End date in YYYY-MM-DD format",
                format="date",
            ),
            "metrics": MCPFunctionParameter(
                type="array",
                description="List of health metrics to retrieve",
                enum=["steps", "sleep", "heart_rate", "weight", "stress", "calories"],
            ),
        },
        required=["start_date", "end_date", "metrics"],
    ),
    returns=MCPFunctionReturn(
        type="object",
        properties={
            "data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "format": "date-time"},
                        "metric": {"type": "string"},
                        "value": {"type": "number"},
                        "unit": {"type": "string"},
                    },
                },
            }
        },
    ),
)

# Define the MCP function for retrieving health trends
GET_HEALTH_TRENDS = MCPFunction(
    name="get_health_trends",
    description="Retrieves health trend data for a specific metric and time period",
    parameters=MCPFunctionParameterObject(
        properties={
            "period": MCPFunctionParameter(
                type="string",
                description="Time period for trend analysis",
                enum=["week", "month", "year"],
            ),
            "metric": MCPFunctionParameter(
                type="string",
                description="Health metric to analyze",
                enum=["steps", "sleep", "heart_rate", "weight", "stress", "calories"],
            ),
        },
        required=["period", "metric"],
    ),
    returns=MCPFunctionReturn(
        type="object",
        properties={
            "data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "period": {"type": "string"},
                        "type": {"type": "string"},
                        "average": {"type": "number"},
                        "min": {"type": "number"},
                        "max": {"type": "number"},
                    },
                },
            }
        },
    ),
)

# Define the MCP function for retrieving available metrics
GET_AVAILABLE_METRICS = MCPFunction(
    name="get_available_metrics",
    description="Retrieves list of all available health metrics with their details",
    parameters=MCPFunctionParameterObject(
        properties={},
        required=[],
    ),
    returns=MCPFunctionReturn(
        type="object",
        properties={
            "metrics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "unit": {"type": "string"},
                        "description": {"type": "string"},
                    },
                },
            }
        },
    ),
)

# Combine all functions into the MCP definition
MCP_DEFINITION = MCPDefinition(
    functions=[
        GET_HEALTH_DATA,
        GET_HEALTH_TRENDS,
        GET_AVAILABLE_METRICS,
    ]
)