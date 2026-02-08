"""Basic FastAPI routes for learning features."""
import logging
from datetime import datetime

import requests
import yaml
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.auth import check_access
from app.config import SENECHAL_API_URL, LEARNING_CONTENT_PATH
from app.learning.models import LearningItemRequest, LearningResponse
from pathlib import Path

from app.learning.utils import (get_content_path, parse_frontmatter,
                                save_learning_content, scrape_url)
from app.llm.llm_services import (
    process_input_content, perform_llm_processing, get_prompt_by_name,
    generate_llm_id, save_llm_result
)
from app.llm.models import OutputFormat

# Get logger
logger = logging.getLogger("api")

router = APIRouter(prefix="/learning", tags=["learning"])


@router.post(
    "/scrape",
    response_model=LearningResponse,
    dependencies=[Depends(check_access("/learning/scrape"))]
)
async def scrape(request: LearningItemRequest):
    """
    Basic endpoint to test URL processing.
    
    This is a placeholder that will later extract content from the provided URL.
    
    Returns:
        LearningResponse: Status and message
    """
    logger.info(f"Received URL processing request: {request.url}")

    try:
        # Use unified LLM service for processing
        raw_content, title, source_type, source_url = process_input_content(
            query_url=str(request.url) if request.url else None,
            query_text=request.text
        )
        
        if not raw_content.strip():
            return LearningResponse(
                status="error",
                message="No content found to process"
            )
        
        # Get the learning extraction prompt
        prompt = get_prompt_by_name("extract_learning")
        
        # Perform LLM processing
        logger.info(f"Processing content with unified LLM service")
        processed_content = perform_llm_processing(
            content=raw_content,
            prompt=prompt,
            model_name="gpt-4o",
            output_format=OutputFormat.MARKDOWN
        )
        
        # Generate ID and save using unified LLM service
        result_id = generate_llm_id()
        save_llm_result(
            result_id=result_id,
            title=title,
            prompt_used="extract_learning",
            model_used="gpt-4o",
            source_type=source_type,
            source_url=source_url,
            content=processed_content,
            raw_content=raw_content,
            output_format=OutputFormat.MARKDOWN,
            metadata={"legacy_endpoint": "learning_scrape"}
        )
        
        # Create the URL pointing to LLM service
        new_url = f"{SENECHAL_API_URL.rstrip('/')}/llm/view/{result_id}"
        
        return LearningResponse(
            status="success",
            message=f"Knowledge extracted using unified LLM service.",
            data={"url": new_url}
        )
        
    except Exception as e:
        logger.error(f"Learning processing failed: {str(e)}")
        return LearningResponse(
            status="error",
            message=f"Failed to process content: {str(e)}"
        )


@router.post(
    "/memo",
    response_model=LearningResponse,
    dependencies=[Depends(check_access("/learning/memo"))]
)
async def create_memo(request: LearningItemRequest):
    """
    Basic endpoint to test memo text processing.
    
    This is a placeholder that will later process the provided text content.
    
    Returns:
        LearningResponse: Status and message
    """
    text = request.text
    logger.info(f"Received memo text: {text[:50]}...")
    
    return LearningResponse(
        status="success",
        message="Memo text received",
        data={"text_length": len(text or "")}
    )


@router.post(
    "/rm",
    response_model=LearningResponse,
    dependencies=[Depends(check_access("/learning/rm"))]
)
async def remove_learning_item(id: str):
    """
    Remove a learning file.
    
    Args:
        id: ID of the learning file to remove
        
    Returns:
        LearningResponse: Status and message
    """
    logger.info(f"Removing learning item ID: {id}")
    
    file_path = get_content_path(id)
    
    if not file_path.exists():
        return LearningResponse(
            status="error",
            message=f"Learning item with ID {id} not found"
        )
    
    try:
        # You could either delete the file or just update its status in the frontmatter
        # Here's the approach to update the frontmatter
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        frontmatter, text_content = parse_frontmatter(content)
        
        # Update the status
        frontmatter["status"] = "archived"
        frontmatter["archived_at"] = datetime.utcnow().isoformat()
        
        # Write back to file
        updated_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{text_content}"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        
        return LearningResponse(
            status="success",
            message=f"Learning item {id} archived successfully"
        )
        
    except Exception as e:
        logger.error(f"Error removing learning item: {e}")
        return LearningResponse(
            status="error",
            message=f"Error removing learning item: {str(e)}"
        )


@router.get(
    "/file/{file_id}",
    response_class=PlainTextResponse,
    #dependencies=[Depends(check_access("/learning/file"))]
)
async def get_learning_file(file_id: str):
    """
    Get a learning content file by ID.
    
    Args:
        file_id: ID of the learning file to retrieve
        
    Returns:
        PlainTextResponse: The markdown content
    """
    file_path = get_content_path(file_id)
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Learning file with ID {file_id} not found"
        )
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading learning file: {str(e)}"
        )


@router.get(
    "/list",
    response_model=LearningResponse,
    dependencies=[Depends(check_access("/learning/list"))]
)
async def list_learning_files(
    status: str = Query("active", description="Filter by status (active, archived, all)")
):
    """
    List learning content files.
    
    Args:
        status: Filter by file status
        
    Returns:
        LearningResponse: List of learning files
    """
    files = []
    
    try:
        content_path = Path(LEARNING_CONTENT_PATH)
        for file_path in content_path.glob("*.md"):
            # Skip raw content files
            if file_path.stem.endswith("_raw"):
                continue
                
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            frontmatter, _ = parse_frontmatter(content)
            
            # Skip if doesn't match status filter
            if status.lower() != "all" and frontmatter.get("status", "active") != status.lower():
                continue
            
            file_info = {
                "id": frontmatter.get("id", file_path.stem),
                "title": frontmatter.get("title", "Untitled"),
                "created": frontmatter.get("created"),
                "content_type": frontmatter.get("content_type", "text"),
                "status": frontmatter.get("status", "active"),
                "source_url": frontmatter.get("source_url"),
                "url": f"/learning/file/{file_path.stem}"
            }
            
            # Add channel name for YouTube videos
            if frontmatter.get("channel_name"):
                file_info["channel_name"] = frontmatter.get("channel_name")
                
            files.append(file_info)
        
        return LearningResponse(
            status="success",
            message=f"Found {len(files)} learning files",
            data={"files": files}
        )
        
    except Exception as e:
        logger.error(f"Error listing learning files: {e}")
        return LearningResponse(
            status="error",
            message=f"Error listing learning files: {str(e)}"
        )