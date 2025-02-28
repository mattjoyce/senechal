from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any
from logging import getLogger
import json

from ..auth import check_access, get_api_key
from .definition import MCP_DEFINITION
from .functions import FUNCTION_REGISTRY

router = APIRouter(
    prefix="/mcp",
    tags=["mcp"],
)

logger = getLogger(__name__)

@router.get("/definition", dependencies=[Depends(check_access("/mcp/definition"))])
async def get_mcp_definition():
    """
    Return the MCP definition file describing available functions.
    This endpoint provides a machine-readable description of all the functions
    available through the MCP API.
    """
    return MCP_DEFINITION.dict()


@router.post("/invoke/{function_name}", dependencies=[Depends(check_access("/mcp/invoke"))])
async def invoke_mcp_function(
    function_name: str,
    parameters: Dict[str, Any] = Body(...),
    api_key_data: dict = Depends(get_api_key)
):
    """
    Invoke an MCP function with the given parameters.
    
    Args:
        function_name: The name of the function to invoke
        parameters: The parameters to pass to the function
        api_key_data: API key information from authentication
        
    Returns:
        The result of the function call
    """
    logger.info(f"MCP invoke: {function_name} | API Key Role: {api_key_data['role']}")
    
    # Check if the function exists
    if function_name not in FUNCTION_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail=f"Function '{function_name}' not found"
        )
    
    try:
        # Call the function with the provided parameters
        function = FUNCTION_REGISTRY[function_name]
        result = await function(parameters)
        return result
    
    except HTTPException as e:
        # Re-raise HTTPExceptions (they already have status code and detail)
        raise e
    
    except Exception as e:
        logger.error(f"Error invoking function {function_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error invoking function: {str(e)}"
        )