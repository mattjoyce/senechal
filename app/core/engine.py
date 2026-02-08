"""Workflow execution engine."""
import logging
from typing import Any, Dict, List, Type, Optional

from app.core.workflow import Step, Workflow, Context
from app.core.steps.common import FetchURLStep, SaveResultStep, ProcessInputStep
from app.core.steps.llm import LLMProcessStep

# Configure logging
logger = logging.getLogger(__name__)

class WorkflowEngine:
    """
    Engine to manage and execute workflows.
    """
    def __init__(self):
        self._step_registry: Dict[str, Type[Step]] = {}
        self._workflow_registry: Dict[str, Dict[str, Any]] = {}

        # Register built-in steps
        self.register_step("fetch_url", FetchURLStep)
        self.register_step("process_input", ProcessInputStep)
        self.register_step("llm_process", LLMProcessStep)
        self.register_step("save_result", SaveResultStep)

    def register_step(self, name: str, step_class: Type[Step]) -> None:
        """Register a step class with a name."""
        self._step_registry[name] = step_class
        logger.info(f"Registered step: {name}")

    def register_workflow(self, name: str, workflow_def: Dict[str, Any]) -> None:
        """Register a workflow definition."""
        self._workflow_registry[name] = workflow_def
        logger.info(f"Registered workflow: {name}")

    def create_workflow(self, workflow_def: Dict[str, Any]) -> Workflow:
        """Create a Workflow instance from a definition."""
        name = workflow_def.get("name", "unnamed_workflow")
        steps_def = workflow_def.get("steps", [])

        steps = []
        for step_def in steps_def:
            step_type = step_def.get("type")
            step_config = step_def.get("config", {})
            step_name = step_def.get("name", step_type)

            step_class = self._step_registry.get(step_type)
            if not step_class:
                raise ValueError(f"Unknown step type: {step_type}")

            steps.append(step_class(name=step_name, config=step_config))

        return Workflow(name=name, steps=steps)

    async def execute_workflow(self, workflow_def: Dict[str, Any], input_data: Dict[str, Any]) -> Context:
        """Execute a workflow defined by a dictionary."""
        workflow = self.create_workflow(workflow_def)
        return await workflow.execute(input_data)

    async def execute_registered_workflow(self, name: str, input_data: Dict[str, Any]) -> Context:
        """Execute a registered workflow by name."""
        workflow_def = self._workflow_registry.get(name)
        if not workflow_def:
            raise ValueError(f"Unknown workflow: {name}")

        return await self.execute_workflow(workflow_def, input_data)


# Global engine instance
engine = WorkflowEngine()
