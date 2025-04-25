"""Basic FastAPI routes for learning features."""
import logging
from datetime import datetime

import requests
import yaml
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.auth import check_access
from app.config import SENECHAL_API_URL
from app.learning.models import LearningItemRequest, LearningResponse
from app.learning.utils import (get_content_path, parse_frontmatter,
                                save_learning_content, scrape_url)
from app.llm.llm_services import extract_knowledge

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

    scraped_result=scrape_url(request.url)
    if scraped_result is None:
        return LearningResponse(
            status="error",
            message="Failed to scrape the URL"
        )
    logger.info(f"Scraped content: {scraped_result[:2000]}")
    knowledge=extract_knowledge(scraped_result, model_name="gpt-4o")
    logger.info(f"Knowledge extracted: {knowledge[:2000]}")

    id=save_learning_content(
        title=request.url,
        content=knowledge,
        source_url=request.url,
        raw_content=scraped_result
    )

    ##create the new url
    new_url = f"{SENECHAL_API_URL}/learning/file/{id}"
    
    return LearningResponse(
        status="success",
        message=f"Knowledge extracted.",
        data={"url": new_url}
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
        for file_path in LEARNING_CONTENT_DIR.glob("*.md"):
            # Skip raw content files
            if file_path.stem.endswith("_raw"):
                continue
                
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            frontmatter, _ = parse_frontmatter(content)
            
            # Skip if doesn't match status filter
            if status.lower() != "all" and frontmatter.get("status", "active") != status.lower():
                continue
            
            files.append({
                "id": frontmatter.get("id", file_path.stem),
                "title": frontmatter.get("title", "Untitled"),
                "created": frontmatter.get("created"),
                "content_type": frontmatter.get("content_type", "text"),
                "status": frontmatter.get("status", "active"),
                "url": f"/learning/file/{file_path.stem}"
            })
        
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