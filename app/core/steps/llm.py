"""LLM workflow steps."""
import asyncio
import logging
from typing import Any, Dict, Optional

from app.core.workflow import Step, Context
from app.llm.llm_services import perform_llm_processing, get_prompt_by_name
from app.llm.models import OutputFormat

# Configure logging
logger = logging.getLogger(__name__)

class LLMProcessStep(Step):
    """
    Step to process content with an LLM.
    Input context keys: 'content'
    Config keys: 'prompt' (required), 'model' (optional, default 'gpt-4o')
    Output context keys: 'content' (updated), 'prompt_used', 'model_used'
    """
    async def execute(self, context: Context) -> None:
        content = context.get("content")
        if not content:
            raise ValueError("No content provided in context for LLM processing")

        # Get prompt name from config or context
        prompt_name = self.config.get("prompt") or context.get("prompt")
        if not prompt_name:
            raise ValueError("No prompt specified for LLM processing")

        # Get model from config or context or default
        model_name = self.config.get("model") or context.get("model") or "gpt-4o"

        # Get output format
        output_format_str = self.config.get("output_format") or context.get("output_format") or "markdown"
        try:
            output_format = OutputFormat(output_format_str)
        except ValueError:
            output_format = OutputFormat.MARKDOWN

        logger.info(f"Processing content with LLM using prompt '{prompt_name}' and model '{model_name}'")

        # Resolve prompt content
        prompt_content = get_prompt_by_name(prompt_name)

        # Perform processing in thread pool to avoid blocking
        result = await asyncio.to_thread(
            perform_llm_processing,
            content=content,
            prompt=prompt_content,
            model_name=model_name,
            output_format=output_format
        )

        # Update context
        # We keep raw_content as is (from previous step)
        context.set("content", result)
        context.set("prompt_used", prompt_name)
        context.set("model_used", model_name)
