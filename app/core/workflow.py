"""Core workflow abstractions for the integration engine."""
import abc
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

class Context(BaseModel):
    """
    Context object passed between steps in a workflow.
    It holds the state of the workflow execution.
    """
    data: Dict[str, Any] = Field(default_factory=dict, description="Workflow data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context data."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the context data."""
        self.data[key] = value

    def update(self, data: Dict[str, Any]) -> None:
        """Update context data with a dictionary."""
        self.data.update(data)


class Step(abc.ABC):
    """
    Abstract base class for workflow steps.
    """
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}

    @abc.abstractmethod
    async def execute(self, context: Context) -> None:
        """
        Execute the step logic.

        Args:
            context: The workflow execution context.
        """
        pass


class Workflow:
    """
    A workflow is a sequence of steps executed in order.
    """
    def __init__(self, name: str, steps: List[Step]):
        self.name = name
        self.steps = steps

    async def execute(self, initial_data: Optional[Dict[str, Any]] = None) -> Context:
        """
        Execute the workflow.

        Args:
            initial_data: Initial data to populate the context.

        Returns:
            The final context after execution.
        """
        context = Context(data=initial_data or {})
        logger.info(f"Starting workflow: {self.name}")

        for step in self.steps:
            logger.info(f"Executing step: {step.name}")
            try:
                await step.execute(context)
            except Exception as e:
                logger.error(f"Error in step {step.name}: {str(e)}")
                raise e

        logger.info(f"Workflow {self.name} completed")
        return context
