import os
import uuid
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from app.config import LEARNING_CONTENT_PATH
from app.learning.utils import scrape_url
from app.llm.llm_services import load_prompt
from app.analysis.models import AnalysisType, ContentType, AnalysisMetadata

import llm


def get_analysis_content_dir() -> Path:
    """Get the directory for storing analysis content"""
    # Use the same parent directory as learning content
    base_dir = Path(LEARNING_CONTENT_PATH).parent if LEARNING_CONTENT_PATH else Path(".")
    content_dir = base_dir / "analysis_content"
    content_dir.mkdir(exist_ok=True)
    return content_dir


def generate_analysis_id() -> str:
    """Generate a unique 8-character ID for analysis"""
    return str(uuid.uuid4())[:8]


def get_analysis_prompt(analysis_type: AnalysisType) -> str:
    """Load the appropriate prompt for the analysis type"""
    prompt_map = {
        AnalysisType.SUMMARY: "analyze_summary.md",
        AnalysisType.EXTRACTION: "analyze_extraction.md", 
        AnalysisType.CLASSIFICATION: "analyze_classification.md",
        AnalysisType.SENTIMENT: "analyze_summary.md",  # Use summary for now
        AnalysisType.KEYWORDS: "analyze_extraction.md",  # Use extraction for now
    }
    
    prompt_file = prompt_map.get(analysis_type, "analyze_summary.md")
    return load_prompt(prompt_file)


def perform_analysis(
    content: str,
    analysis_type: AnalysisType,
    custom_prompt: Optional[str] = None,
    model_name: str = "gpt-4o"
) -> str:
    """Perform LLM analysis on the provided content"""
    try:
        if analysis_type == AnalysisType.CUSTOM and custom_prompt:
            prompt = custom_prompt
        else:
            prompt = get_analysis_prompt(analysis_type)
        
        # Combine prompt with content
        full_prompt = f"{prompt}\n\n{content}"
        
        # Get LLM model and generate response
        model = llm.get_model(model_name)
        response = model.prompt(prompt=full_prompt)
        
        return response.text()
        
    except Exception as e:
        raise Exception(f"Analysis failed: {str(e)}")


def process_content_for_analysis(
    url: Optional[str] = None,
    text: Optional[str] = None
) -> Tuple[str, str, ContentType, Optional[str]]:
    """
    Process input content for analysis
    Returns: (content, title, content_type, source_url)
    """
    if url:
        # Use existing scraping functionality from learning module
        scraped_data = scrape_url(url)
        content = scraped_data.get("content", "")
        title = scraped_data.get("title", "Untitled")
        content_type_str = scraped_data.get("content_type", "webpage")
        
        # Map content type
        content_type = ContentType.YOUTUBE if content_type_str == "youtube" else ContentType.WEBPAGE
        
        return content, title, content_type, url
        
    elif text:
        # Direct text input
        title = f"Text Analysis - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
        return text, title, ContentType.TEXT, None
        
    else:
        raise ValueError("Either URL or text must be provided")


def save_analysis_result(
    analysis_id: str,
    title: str,
    analysis_type: AnalysisType,
    content_type: ContentType,
    source_url: Optional[str],
    analysis_content: str,
    raw_content: str,
    model_used: str,
    metadata: Dict[str, Any] = None
) -> str:
    """Save analysis result to file with frontmatter"""
    content_dir = get_analysis_content_dir()
    
    # Create metadata
    analysis_metadata = AnalysisMetadata(
        id=analysis_id,
        title=title,
        analysis_type=analysis_type.value,
        content_type=content_type.value,
        source_url=source_url,
        model_used=model_used,
        created=datetime.now(timezone.utc).isoformat(),
        metadata=metadata or {}
    )
    
    # Create frontmatter content
    frontmatter = yaml.dump(analysis_metadata.dict(), default_flow_style=False, allow_unicode=True)
    
    # Create main analysis file
    main_content = f"---\n{frontmatter}---\n\n# {title}\n\n{analysis_content}"
    main_file = content_dir / f"{analysis_id}.md"
    
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(main_content)
    
    # Save raw content file
    raw_file = content_dir / f"{analysis_id}_raw.md"
    with open(raw_file, 'w', encoding='utf-8') as f:
        f.write(raw_content)
    
    return analysis_id


def parse_analysis_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse frontmatter from analysis markdown content"""
    if not content.startswith('---'):
        return {}, content
    
    try:
        # Split frontmatter and content
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content
        
        frontmatter_str = parts[1].strip()
        content_str = parts[2].strip()
        
        # Parse YAML frontmatter
        frontmatter = yaml.safe_load(frontmatter_str)
        
        return frontmatter or {}, content_str
        
    except yaml.YAMLError:
        return {}, content


def get_analysis_file_content(analysis_id: str) -> Tuple[Dict[str, Any], str]:
    """Get analysis file content and metadata"""
    content_dir = get_analysis_content_dir()
    file_path = content_dir / f"{analysis_id}.md"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Analysis file not found: {analysis_id}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return parse_analysis_frontmatter(content)


def list_analysis_files() -> list:
    """List all analysis files with metadata"""
    content_dir = get_analysis_content_dir()
    analysis_files = []
    
    for file_path in content_dir.glob("*.md"):
        if file_path.name.endswith("_raw.md"):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metadata, _ = parse_analysis_frontmatter(content)
            if metadata:
                analysis_files.append({
                    "id": metadata.get("id", file_path.stem),
                    "title": metadata.get("title", "Untitled"),
                    "analysis_type": metadata.get("analysis_type", "unknown"),
                    "content_type": metadata.get("content_type", "unknown"),
                    "created": metadata.get("created", ""),
                    "source_url": metadata.get("source_url")
                })
                
        except Exception as e:
            print(f"Error reading analysis file {file_path}: {e}")
            continue
    
    # Sort by creation date (newest first)
    analysis_files.sort(key=lambda x: x.get("created", ""), reverse=True)
    return analysis_files