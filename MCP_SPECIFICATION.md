# Senechal MCP Integration Specification

## Overview

This document outlines the implementation of Model Context Protocol (MCP) integration for the Senechal API. This enhancement will allow AI models like Claude to interact with Senechal in a standardized way, accessing personal data through well-defined function calls.

## Implementation Goals

1. Provide a standardized interface for AI models to query Senechal data
2. Maintain existing security model with API keys and role-based access
3. Allow flexible, discoverable access to Senechal's capabilities
4. Minimize redundant code by leveraging existing routes and handlers

## Technical Design

### 1. MCP Module Structure

Create a new module within the Senechal app directory:

```
app/
  mcp/
    __init__.py
    routes.py      # FastAPI route definitions
    schema.py      # Pydantic schemas for MCP
    functions.py   # MCP function implementations
    definition.py  # MCP function definitions
```

### 2. MCP Endpoint Implementation

Implement the following endpoints:

- `GET /mcp/definition` - Returns the MCP definition file describing available functions
- `POST /mcp/invoke/{function_name}` - Endpoint to invoke MCP functions

### 3. Function Definition Schema

The definition file will follow MCP specification format:

```python
MCP_DEFINITION = {
  "schema_version": "v1",
  "functions": [
    {
      "name": "get_health_data",
      "description": "Retrieves health data for a specific date range and metrics",
      "parameters": {
        "type": "object",
        "properties": {
          "start_date": {
            "type": "string",
            "format": "date",
            "description": "Start date in YYYY-MM-DD format"
          },
          "end_date": {
            "type": "string",
            "format": "date",
            "description": "End date in YYYY-MM-DD format"
          },
          "metrics": {
            "type": "array",
            "items": {
              "type": "string",
              "enum": ["steps", "sleep", "heart_rate", "weight"]
            },
            "description": "List of health metrics to retrieve"
          }
        },
        "required": ["start_date", "end_date", "metrics"]
      },
      "returns": {
        "type": "object",
        "properties": {
          "data": {
            "type": "array",
            "items": {
              "type": "object"
            }
          }
        }
      }
    }
    // Additional function definitions
  ]
}
```

### 4. Authentication Integration

- All MCP endpoints will use the existing API key authentication mechanism
- Claude and other AI models will need to be provided with a valid API key
- Consider implementing single-use or time-limited tokens for AI sessions

### 5. Function Implementation

Each function will be mapped to existing Senechal functionality:

```python
async def get_health_data(start_date: str, end_date: str, metrics: List[str]) -> Dict:
    """Implements the get_health_data MCP function"""
    # Reuse existing health route functionality
    # Format response according to MCP specification
    return formatted_data
```

### 6. Error Handling

- Follow MCP specification for error responses
- Map Senechal error codes to appropriate MCP error formats
- Provide clear error messages suitable for AI interpretation

## Usage Examples

### Example: Claude Using Senechal MCP

```
User: What was my step count for the last week?

Claude: I'll check your Senechal data for that information. 
[Uses MCP to call get_health_data with appropriate parameters]

User: Can you show me my sleep trends for the past month?

Claude: Let me analyze your sleep data.
[Uses MCP to retrieve sleep metrics and performs analysis]
```

## Implementation Phases

1. Create MCP module structure and basic routes
2. Implement the definition endpoint with initial function definitions
3. Create function handlers that map to existing Senechal functionality
4. Add authentication integration and error handling
5. Test with Claude and other AI models
6. Add additional functions based on usage patterns

## Security Considerations

- Ensure API keys have appropriate permissions
- Consider rate limiting for MCP endpoints
- Log all MCP function calls for auditing
- Implement function-level permission checks
- Consider implementing user confirmation for sensitive data requests

## Future Enhancements

- Dynamic function discovery based on available data sources
- Streaming responses for large datasets
- Session-based context for multi-turn interactions
- Custom visualization instructions for data representation