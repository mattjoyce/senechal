"""Workflow execution routes."""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.auth import check_access
from app.core.engine import engine

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow", tags=["workflow"])

class WorkflowRequest(BaseModel):
    """Request model for workflow execution."""
    workflow_name: Optional[str] = Field(None, description="Name of a registered workflow to execute")
    workflow_def: Optional[Dict[str, Any]] = Field(None, description="Ad-hoc workflow definition")
    input: Dict[str, Any] = Field(default_factory=dict, description="Input data for the workflow")

class WorkflowResponse(BaseModel):
    """Response model for workflow execution."""
    status: str
    message: str
    data: Dict[str, Any]

@router.post("/execute", response_model=WorkflowResponse, dependencies=[Depends(check_access("/workflow/execute"))])
async def execute_workflow(request: WorkflowRequest):
    """
    Execute a workflow.

    You can either provide a `workflow_name` to execute a registered workflow,
    or a `workflow_def` to execute an ad-hoc workflow.
    """
    try:
        if request.workflow_name:
            logger.info(f"Executing registered workflow: {request.workflow_name}")
            context = await engine.execute_registered_workflow(request.workflow_name, request.input)
        elif request.workflow_def:
            logger.info("Executing ad-hoc workflow")
            context = await engine.execute_workflow(request.workflow_def, request.input)
        else:
            raise HTTPException(status_code=400, detail="Either workflow_name or workflow_def must be provided")

        return WorkflowResponse(
            status="success",
            message="Workflow execution completed",
            data=context.data
        )

    except ValueError as e:
        logger.error(f"Workflow validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@router.get("/steps", dependencies=[Depends(check_access("/workflow/steps"))])
async def list_steps():
    """List available workflow steps."""
    return {
        "status": "success",
        "data": list(engine._step_registry.keys())
    }
