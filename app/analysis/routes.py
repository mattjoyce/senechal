from datetime import datetime, timezone
from typing import List
import logging

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse

from app.auth import check_access
from app.analysis.models import (
    AnalyzeRequest, AnalysisResponse, AnalysisResult, AnalysisListResponse, 
    AnalysisListItem, AnalysisType, ContentType
)
from app.analysis.utils import (
    process_content_for_analysis, perform_analysis, save_analysis_result,
    generate_analysis_id, get_analysis_file_content, list_analysis_files
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse, dependencies=[Depends(check_access("/analysis/analyze"))])
async def analyze_content(request: AnalyzeRequest):
    """
    Analyze content from URL or text input using LLM
    """
    try:
        # Validate input
        if not request.url and not request.text:
            raise HTTPException(status_code=400, detail="Either URL or text must be provided")
        
        if request.url and request.text:
            raise HTTPException(status_code=400, detail="Provide either URL or text, not both")
        
        # Process content for analysis
        logger.info(f"Processing content for analysis - Type: {request.analysis_type}")
        raw_content, title, content_type, source_url = process_content_for_analysis(
            url=request.url,
            text=request.text
        )
        
        if not raw_content.strip():
            raise HTTPException(status_code=400, detail="No content found to analyze")
        
        # Perform analysis
        logger.info(f"Performing {request.analysis_type} analysis using {request.model_name}")
        analysis_content = perform_analysis(
            content=raw_content,
            analysis_type=request.analysis_type,
            custom_prompt=request.custom_prompt,
            model_name=request.model_name
        )
        
        # Save result if requested
        analysis_id = generate_analysis_id()
        if request.save_result:
            logger.info(f"Saving analysis result with ID: {analysis_id}")
            save_analysis_result(
                analysis_id=analysis_id,
                title=title,
                analysis_type=request.analysis_type,
                content_type=content_type,
                source_url=source_url,
                analysis_content=analysis_content,
                raw_content=raw_content,
                model_used=request.model_name
            )
            
            # Return URL like learning endpoint when saving
            from app.config import SENECHAL_API_URL
            analysis_url = f"{SENECHAL_API_URL}/analysis/file/{analysis_id}"
            
            return AnalysisResponse(
                status="success",
                message=f"Analysis completed using {request.analysis_type} method and saved",
                data={"url": analysis_url}
            )
        
        # Create response with full content when not saving
        result = AnalysisResult(
            id=analysis_id,
            title=title,
            analysis_type=request.analysis_type,
            content_type=content_type,
            source_url=source_url,
            analysis_content=analysis_content,
            raw_content=raw_content,
            model_used=request.model_name,
            created=datetime.now(timezone.utc)
        )
        
        return AnalysisResponse(
            status="success",
            message=f"Analysis completed using {request.analysis_type} method",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/list", response_model=AnalysisListResponse, dependencies=[Depends(check_access("/analysis/list"))])
async def list_analyses():
    """
    List all saved analysis results
    """
    try:
        analysis_files = list_analysis_files()
        
        # Convert to response format
        analysis_items = []
        for item in analysis_files:
            try:
                analysis_items.append(AnalysisListItem(
                    id=item["id"],
                    title=item["title"],
                    analysis_type=AnalysisType(item["analysis_type"]),
                    content_type=ContentType(item["content_type"]),
                    created=datetime.fromisoformat(item["created"].replace('Z', '+00:00')),
                    source_url=item.get("source_url")
                ))
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid analysis item: {e}")
                continue
        
        return AnalysisListResponse(
            status="success",
            message=f"Found {len(analysis_items)} analysis results",
            data=analysis_items
        )
        
    except Exception as e:
        logger.error(f"Failed to list analyses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list analyses: {str(e)}")


@router.get("/file/{analysis_id}", response_class=PlainTextResponse, dependencies=[Depends(check_access("/analysis/file"))])
async def get_analysis_file(analysis_id: str):
    """
    Get analysis file content by ID
    """
    try:
        metadata, content = get_analysis_file_content(analysis_id)
        
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
        raise HTTPException(status_code=404, detail=f"Analysis file not found: {analysis_id}")
    except Exception as e:
        logger.error(f"Failed to get analysis file {analysis_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analysis file: {str(e)}")


@router.delete("/file/{analysis_id}", dependencies=[Depends(check_access("/analysis/file"))])
async def delete_analysis_file(analysis_id: str):
    """
    Delete analysis file by ID
    """
    try:
        from pathlib import Path
        from app.analysis.utils import get_analysis_content_dir
        
        content_dir = get_analysis_content_dir()
        main_file = content_dir / f"{analysis_id}.md"
        raw_file = content_dir / f"{analysis_id}_raw.md"
        
        if not main_file.exists():
            raise HTTPException(status_code=404, detail=f"Analysis file not found: {analysis_id}")
        
        # Delete both files
        main_file.unlink()
        if raw_file.exists():
            raw_file.unlink()
        
        return {"status": "success", "message": f"Analysis {analysis_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete analysis file {analysis_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete analysis file: {str(e)}")


@router.get("/types", dependencies=[Depends(check_access("/analysis/types"))])
async def get_analysis_types():
    """
    Get available analysis types
    """
    return {
        "status": "success",
        "message": "Available analysis types",
        "data": {
            "types": [
                {
                    "value": analysis_type.value,
                    "description": get_analysis_type_description(analysis_type)
                }
                for analysis_type in AnalysisType
            ]
        }
    }


def get_analysis_type_description(analysis_type: AnalysisType) -> str:
    """Get description for analysis type"""
    descriptions = {
        AnalysisType.SUMMARY: "Generate a comprehensive summary of the content",
        AnalysisType.EXTRACTION: "Extract structured data, entities, and key facts",
        AnalysisType.CLASSIFICATION: "Classify content by type, domain, audience, and quality",
        AnalysisType.SENTIMENT: "Analyze sentiment and emotional tone",
        AnalysisType.KEYWORDS: "Extract keywords and important terms",
        AnalysisType.CUSTOM: "Use a custom prompt for specialized analysis"
    }
    return descriptions.get(analysis_type, "Unknown analysis type")