"""Common workflow steps."""
import asyncio
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from app.core.workflow import Step, Context
from app.learning.utils import scrape_url
from app.llm.llm_services import save_llm_result, generate_llm_id, process_input_content
from app.llm.models import OutputFormat

# Configure logging
logger = logging.getLogger(__name__)

class FetchURLStep(Step):
    """
    Step to fetch content from a URL.
    Input context keys: 'url'
    Output context keys: 'content', 'title', 'source_type', 'source_url'
    """
    async def execute(self, context: Context) -> None:
        url = context.get("url")
        if not url:
            raise ValueError("URL not provided in context")

        logger.info(f"Fetching content from URL: {url}")

        # Use existing utility in thread pool to avoid blocking
        scraped_data = await asyncio.to_thread(scrape_url, url)

        if not scraped_data:
            raise ValueError(f"Failed to scrape content from {url}")

        # Update context
        context.set("content", scraped_data.get("content"))
        context.set("title", scraped_data.get("title") or "Untitled")
        context.set("source_type", scraped_data.get("content_type", "url"))
        context.set("source_url", url)

        # Also set raw_content for later steps
        context.set("raw_content", scraped_data.get("content"))


class ProcessInputStep(Step):
    """
    Step to process input (either text or URL).
    Input context keys: 'url' OR 'text'
    Output context keys: 'content', 'title', 'source_type', 'source_url', 'raw_content'
    """
    async def execute(self, context: Context) -> None:
        url = context.get("url")
        text = context.get("text")

        if not url and not text:
            raise ValueError("Neither 'url' nor 'text' provided in context")

        logger.info("Processing input content")

        # Run blocking call in thread pool
        raw_content, title, source_type, source_url = await asyncio.to_thread(
            process_input_content,
            query_text=text,
            query_url=url
        )

        context.set("content", raw_content)
        context.set("raw_content", raw_content)
        context.set("title", title)
        context.set("source_type", source_type)
        context.set("source_url", source_url)


class SaveResultStep(Step):
    """
    Step to save the result.
    Input context keys: 'content', 'title', 'prompt_used', 'model_used',
                       'source_type', 'source_url', 'raw_content'
    Output context keys: 'result_id', 'result_url'
    """
    async def execute(self, context: Context) -> None:
        content = context.get("content")
        if not content:
            raise ValueError("No content to save")

        result_id = generate_llm_id()

        # Get metadata from context or config
        metadata = context.get("metadata", {})

        # Update metadata with step config if provided
        if self.config.get("metadata"):
            metadata.update(self.config.get("metadata"))

        # Run blocking file I/O in thread pool
        await asyncio.to_thread(
            save_llm_result,
            result_id=result_id,
            title=context.get("title", "Untitled"),
            prompt_used=context.get("prompt_used", "unknown"),
            model_used=context.get("model_used", "unknown"),
            source_type=context.get("source_type", "unknown"),
            source_url=context.get("source_url"),
            content=content,
            raw_content=context.get("raw_content"),
            output_format=OutputFormat.MARKDOWN,
            metadata=metadata
        )

        from app.config import SENECHAL_API_URL
        # Handle case where SENECHAL_API_URL might be None
        api_url = SENECHAL_API_URL or "http://localhost:8000"
        result_url = f"{api_url.rstrip('/')}/llm/view/{result_id}"

        context.set("result_id", result_id)
        context.set("result_url", result_url)
        logger.info(f"Saved result with ID: {result_id}")
