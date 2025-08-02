"""Unified LLM routes for all LLM operations."""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse, HTMLResponse

from app.auth import check_access
from app.config import SENECHAL_API_URL
from app.llm.models import (
    LLMRequest, LLMResponse, LLMResult, LLMListResponse, LLMListItem,
    PromptsResponse, PromptInfo, OutputFormat, ExtractRequest, AnalyzeRequest, CustomRequest
)
from app.llm.llm_services import (
    get_available_prompts, get_prompt_by_name, process_input_content,
    perform_llm_processing, save_llm_result, generate_llm_id,
    get_llm_file_content, list_llm_results, render_markdown_to_html,
    get_available_themes, set_selected_theme
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["llm"])


@router.post("/process", response_model=LLMResponse, dependencies=[Depends(check_access("/llm/process"))])
async def process_with_llm(request: LLMRequest):
    """
    Unified LLM processing endpoint that can handle various prompts and input sources
    """
    try:
        # Validate input
        if not request.query_url and not request.query_text:
            raise HTTPException(status_code=400, detail="Either query_url or query_text must be provided")
        
        if request.query_url and request.query_text:
            raise HTTPException(status_code=400, detail="Provide either query_url or query_text, not both")
        
        # Process input content
        logger.info(f"Processing content with prompt: {request.prompt[:50]}...")
        raw_content, title, source_type, source_url = process_input_content(
            query_text=request.query_text,
            query_url=request.query_url
        )
        
        if not raw_content.strip():
            raise HTTPException(status_code=400, detail="No content found to process")
        
        # Get the prompt
        prompt = get_prompt_by_name(request.prompt)
        
        # Override title if custom title provided
        if request.custom_title:
            title = request.custom_title
        
        # Perform LLM processing
        logger.info(f"Processing with model: {request.model}")
        processed_content = perform_llm_processing(
            content=raw_content,
            prompt=prompt,
            model_name=request.model,
            output_format=request.output_format
        )
        
        # Generate result ID
        result_id = generate_llm_id()
        
        # Save result if requested
        if request.save_result:
            logger.info(f"Saving LLM result with ID: {result_id}")
            save_llm_result(
                result_id=result_id,
                title=title,
                prompt_used=request.prompt,
                model_used=request.model,
                source_type=source_type,
                source_url=source_url,
                content=processed_content,
                raw_content=raw_content,
                output_format=request.output_format,
                metadata=request.metadata
            )
            
            # Return URL when saving
            result_url = f"{SENECHAL_API_URL}/llm/view/{result_id}"
            
            return LLMResponse(
                status="success",
                message=f"Content processed with {request.model} and saved",
                data={"url": result_url}
            )
        
        # Create response with full content when not saving
        result = LLMResult(
            id=result_id,
            title=title,
            prompt_used=request.prompt,
            model_used=request.model,
            source_type=source_type,
            source_url=source_url,
            content=processed_content,
            raw_content=raw_content,
            output_format=request.output_format,
            created=datetime.now(timezone.utc),
            metadata=request.metadata
        )
        
        return LLMResponse(
            status="success",
            message=f"Content processed with {request.model}",
            data=result.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LLM processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM processing failed: {str(e)}")


@router.get("/prompts", response_model=PromptsResponse, dependencies=[Depends(check_access("/llm/prompts"))])
async def get_prompts():
    """
    Get list of available named prompts
    """
    try:
        available_prompts = get_available_prompts()
        
        prompt_list = [
            PromptInfo(
                name=name,
                description=info["description"],
                category=info["category"]
            )
            for name, info in available_prompts.items()
        ]
        
        return PromptsResponse(
            status="success",
            message=f"Found {len(prompt_list)} available prompts",
            data=prompt_list
        )
        
    except Exception as e:
        logger.error(f"Failed to get prompts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get prompts: {str(e)}")


@router.get("/list", response_model=LLMListResponse, dependencies=[Depends(check_access("/llm/list"))])
async def list_results():
    """
    List all saved LLM results
    """
    try:
        results = list_llm_results()
        
        # Convert to response format
        result_items = []
        for item in results:
            try:
                result_items.append(LLMListItem(
                    id=item["id"],
                    title=item["title"],
                    prompt_used=item["prompt_used"],
                    model_used=item["model_used"],
                    source_type=item["source_type"],
                    created=datetime.fromisoformat(item["created"].replace('Z', '+00:00')),
                    source_url=item.get("source_url")
                ))
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid LLM result item: {e}")
                continue
        
        return LLMListResponse(
            status="success",
            message=f"Found {len(result_items)} LLM results",
            data=result_items
        )
        
    except Exception as e:
        logger.error(f"Failed to list LLM results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list LLM results: {str(e)}")


@router.get("/file/{result_id}", response_class=PlainTextResponse)
async def get_result_file(result_id: str):
    """
    Get LLM result file content by ID
    """
    try:
        metadata, content = get_llm_file_content(result_id)
        
        # Return the full markdown content with frontmatter
        frontmatter_str = "---\n"
        for key, value in metadata.items():
            frontmatter_str += f"{key}: {value}\n"
        frontmatter_str += "---\n\n"
        
        return PlainTextResponse(
            content=frontmatter_str + content,
            media_type="text/markdown"
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"LLM result file not found: {result_id}")
    except Exception as e:
        logger.error(f"Failed to get LLM result file {result_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get LLM result file: {str(e)}")


@router.delete("/file/{result_id}", dependencies=[Depends(check_access("/llm/file"))])
async def delete_result_file(result_id: str):
    """
    Delete LLM result file by ID
    """
    try:
        from pathlib import Path
        from app.llm.llm_services import get_llm_content_dir
        
        content_dir = get_llm_content_dir()
        main_file = content_dir / f"{result_id}.md"
        raw_file = content_dir / f"{result_id}_raw.md"
        
        if not main_file.exists():
            raise HTTPException(status_code=404, detail=f"LLM result file not found: {result_id}")
        
        # Delete both files
        main_file.unlink()
        if raw_file.exists():
            raw_file.unlink()
        
        return {"status": "success", "message": f"LLM result {result_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete LLM result file {result_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete LLM result file: {str(e)}")


@router.get("/view/{result_id}", response_class=HTMLResponse)
async def view_result(result_id: str, theme: Optional[str] = Query(None)):
    """
    View LLM result as rendered HTML with theme support
    """
    try:
        metadata, content = get_llm_file_content(result_id)
        
        # Use provided theme or fall back to stored selection
        if theme:
            # Validate theme exists
            available_themes = get_available_themes()
            if theme not in available_themes:
                raise HTTPException(status_code=400, detail=f"Theme '{theme}' not found. Available: {available_themes}")
            
            # Persist theme selection
            set_selected_theme(theme)
            theme_name = theme
        else:
            theme_name = None  # Will use default from get_selected_theme()
        
        # Render markdown to HTML
        html_content = render_markdown_to_html(content, metadata, theme_name)
        
        return HTMLResponse(content=html_content)
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"LLM result file not found: {result_id}")
    except Exception as e:
        logger.error(f"Failed to view LLM result {result_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to view LLM result: {str(e)}")


# Convenience endpoints for common operations

@router.post("/extract", response_model=LLMResponse, dependencies=[Depends(check_access("/llm/extract"))])
async def extract_learning(request: ExtractRequest):
    """
    Convenience endpoint for learning extraction (equivalent to learning/scrape)
    """
    llm_request = LLMRequest(
        model=request.model,
        prompt="extract_learning",
        query_url=request.query_url,
        query_text=request.query_text,
        save_result=request.save_result,
        output_format=OutputFormat.MARKDOWN
    )
    return await process_with_llm(llm_request)


@router.post("/analyze", response_model=LLMResponse, dependencies=[Depends(check_access("/llm/analyze"))])
async def analyze_content(request: AnalyzeRequest):
    """
    Convenience endpoint for content analysis (equivalent to analysis/analyze)
    """
    # Map analysis types to prompt names
    prompt_map = {
        "summary": "analyze_summary",
        "extraction": "analyze_extraction", 
        "classification": "analyze_classification"
    }
    
    prompt = prompt_map.get(request.analysis_type, "analyze_summary")
    
    llm_request = LLMRequest(
        model=request.model,
        prompt=prompt,
        query_url=request.query_url,
        query_text=request.query_text,
        save_result=request.save_result,
        output_format=OutputFormat.MARKDOWN
    )
    return await process_with_llm(llm_request)


@router.post("/custom", response_model=LLMResponse, dependencies=[Depends(check_access("/llm/custom"))])
async def custom_processing(request: CustomRequest):
    """
    Custom prompt processing endpoint
    """
    llm_request = LLMRequest(
        model=request.model,
        prompt=request.custom_prompt,
        query_url=request.query_url,
        query_text=request.query_text,
        save_result=request.save_result,
        output_format=request.output_format
    )
    return await process_with_llm(llm_request)