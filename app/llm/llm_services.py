"""Unified LLM services for all LLM operations."""
import json
import logging
import re
import uuid
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple, Optional, Union

import llm

from app.health.models import RowingData
from app.config import LEARNING_CONTENT_PATH
from app.learning.utils import scrape_url
from app.llm.models import OutputFormat, LLMResult

# Set up logging
logger = logging.getLogger(__name__)


def load_prompt(prompt_file: str) -> str:
    """
    Load a prompt from a markdown file.

    Args:
        prompt_file: Path to the markdown file containing the prompt

    Returns:
        The prompt text
    """
    prompt_path = Path(__file__).parent / "prompts" / prompt_file
    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read()


def extract_json_from_text(text: str) -> dict:
    """Extract JSON from text with multiple fallback methods."""
    # Method 1: Try direct JSON parsing
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Method 2: Look for JSON in markdown code blocks

    json_pattern = r"```(?:json)?\s*([\s\S]*?)```"
    matches = re.findall(json_pattern, text)

    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # Method 3: More aggressive pattern matching for JSON objects
    bracket_pattern = r"(\{(?:[^{}]|(?:\{[^{}]*\}))*\})"
    matches = re.search(bracket_pattern, text)
    if matches:
        try:
            return json.loads(matches.group(1))
        except json.JSONDecodeError:
            pass

    # If all attempts fail, raise an error
    raise ValueError(f"Failed to extract any valid JSON from text")


async def extract_rowing_data(
    image_data: bytes, model_name: str = "gpt-4o"
) -> Dict[str, Any]:
    """
    Extract rowing workout data from an image using an LLM.

    This function sends an image to an LLM and extracts structured workout data
    using a specific prompt designed for rowing machine screenshots.

    Args:
        image_data: Binary image data of the rowing machine display
        model_name: The name of the LLM model to use

    Returns:
        Dictionary containing the extracted workout data with keys:
        - workout_type: "distance" or "interval"
        - duration_seconds: Total duration in seconds (float)
        - distance_meters: Total distance in meters (float)
        - avg_split: Average split time in seconds per 500m (float or None)

    Raises:
        ValueError: If the image cannot be processed or data extraction fails
        JSONDecodeError: If the LLM response cannot be parsed as valid JSON
    """
    # Load the prompt from the prompt file
    prompt = load_prompt("rowing_extractor.md")

    logger.debug(f"Calling LLM with model: {model_name}")

    try:

        # Get the model and send the prompt with the image
        model = llm.get_model(model_name)
        llm_response = model.prompt(
            prompt, attachments=[llm.Attachment(content=image_data)], json_object=True
        )
        result_text = llm_response.text()

        logger.debug(f"LLM raw response: {result_text[:200]}...")

        parsed_data = extract_json_from_text(result_text)
        logger.debug(f"Successfully extracted JSON from text: {parsed_data}")
    except Exception as error:
        logger.error(f"Failed to extract JSON from text: {str(error)}")
        raise ValueError(f"Failed to extract JSON from text: {str(error)}")

    try:
        # After extracting JSON using any method
        validated_data = RowingData.model_validate(parsed_data)
        return validated_data.model_dump()
    except Exception as error:
        logger.error(f"Data validation failed: {str(error)}")
        raise ValueError(f"Extracted data does not match expected schema: {str(error)}")


def extract_knowledge(text: str, model_name: str = "gpt-4o") -> str:
    """
    Extract knowledge from a text using a specific prompt.

    This function uses a prompt to extract knowledge from a given text.
    The knowledge is extracted using a specific prompt designed for
    extracting knowledge from text.

    Args:
        text: The text to extract knowledge from
    """
    # Load the prompt from the prompt file
    prompt = load_prompt("extract_learning.md")
    logger.debug(f"Calling LLM with prompt: {prompt}")
    context = prompt + "\n" + text
    try:
        # Get the model and send the prompt with the image
        model = llm.get_model(model_name)
        llm_response = model.prompt(prompt=context)
        result_text = llm_response.text()

        logger.debug(f"LLM raw response: {result_text[:200]}...")

        return result_text
    except Exception as error:
        logger.error(f"Failed to extract knowledge: {str(error)}")
        raise ValueError(f"Failed to extract knowledge: {str(error)}")


# Unified LLM utilities

def get_llm_content_dir() -> Path:
    """Get the directory for storing LLM results"""
    base_dir = Path(LEARNING_CONTENT_PATH).parent if LEARNING_CONTENT_PATH else Path(".")
    content_dir = base_dir / "llm_content"
    content_dir.mkdir(exist_ok=True)
    return content_dir


def generate_llm_id() -> str:
    """Generate a unique 8-character ID for LLM results"""
    return str(uuid.uuid4())[:8]


def get_available_prompts() -> Dict[str, Dict[str, str]]:
    """Get information about available prompts"""
    prompts_dir = Path(__file__).parent / "prompts"
    prompts = {}
    
    # Map prompt files to their info
    prompt_info = {
        "extract_learning.md": {
            "name": "extract_learning",
            "description": "Extract key learning points and knowledge from text content",
            "category": "learning"
        },
        "analyze_summary.md": {
            "name": "analyze_summary", 
            "description": "Generate a comprehensive summary of content",
            "category": "analysis"
        },
        "analyze_extraction.md": {
            "name": "analyze_extraction",
            "description": "Extract structured data, entities, and key facts",
            "category": "analysis"
        },
        "analyze_classification.md": {
            "name": "analyze_classification",
            "description": "Classify content by type, domain, audience, and quality",
            "category": "analysis"
        },
        "rowing_extractor.md": {
            "name": "rowing_extractor",
            "description": "Extract rowing workout data from machine screenshots",
            "category": "health"
        }
    }
    
    for file_name, info in prompt_info.items():
        prompt_path = prompts_dir / file_name
        if prompt_path.exists():
            prompts[info["name"]] = info
    
    return prompts


def get_prompt_by_name(prompt_name: str) -> str:
    """Get prompt content by name, falling back to treating it as custom prompt"""
    # Check if it's a known prompt file
    prompt_files = {
        "extract_learning": "extract_learning.md",
        "analyze_summary": "analyze_summary.md", 
        "analyze_extraction": "analyze_extraction.md",
        "analyze_classification": "analyze_classification.md",
        "rowing_extractor": "rowing_extractor.md"
    }
    
    if prompt_name in prompt_files:
        return load_prompt(prompt_files[prompt_name])
    
    # Otherwise, treat as custom prompt text
    return prompt_name


def process_input_content(
    query_text: Optional[str] = None,
    query_url: Optional[str] = None
) -> Tuple[str, str, str, Optional[str]]:
    """
    Process input content for LLM processing
    Returns: (content, title, source_type, source_url)
    """
    if query_url:
        # Use existing scraping functionality
        scraped_data = scrape_url(query_url)
        if not scraped_data:
            raise ValueError("Failed to scrape content from URL")
            
        content = scraped_data.get("content", "")
        title = scraped_data.get("title") or "Untitled"
        source_type = "url"
        
        return content, title, source_type, query_url
        
    elif query_text:
        # Direct text input
        title = f"Text Processing - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
        return query_text, title, "text", None
        
    else:
        raise ValueError("Either query_text or query_url must be provided")


def perform_llm_processing(
    content: str,
    prompt: str,
    model_name: str = "gpt-4o",
    output_format: OutputFormat = OutputFormat.TEXT
) -> str:
    """Perform LLM processing on content with given prompt"""
    try:
        # Combine prompt with content
        full_prompt = f"{prompt}\n\n{content}"
        
        # Get LLM model and generate response
        model = llm.get_model(model_name)
        
        # Use JSON mode if requested
        if output_format == OutputFormat.JSON:
            response = model.prompt(prompt=full_prompt, json_object=True)
        else:
            response = model.prompt(prompt=full_prompt)
        
        result_text = response.text()
        
        # Format output if needed
        if output_format == OutputFormat.MARKDOWN and not result_text.startswith('#'):
            # Ensure markdown formatting
            result_text = f"# Result\n\n{result_text}"
        
        return result_text
        
    except Exception as e:
        raise Exception(f"LLM processing failed: {str(e)}")


def save_llm_result(
    result_id: str,
    title: str,
    prompt_used: str,
    model_used: str,
    source_type: str,
    source_url: Optional[str],
    content: str,
    raw_content: Optional[str],
    output_format: OutputFormat,
    metadata: Dict[str, Any] = None
) -> str:
    """Save LLM result to file with frontmatter"""
    content_dir = get_llm_content_dir()
    
    # Create result metadata
    result_metadata = {
        "id": result_id,
        "title": title,
        "prompt_used": prompt_used,
        "model_used": model_used,
        "source_type": source_type,
        "source_url": source_url,
        "output_format": output_format.value,
        "created": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {}
    }
    
    # Create frontmatter content
    frontmatter = yaml.dump(result_metadata, default_flow_style=False, allow_unicode=True)
    
    # Create main result file
    main_content = f"---\n{frontmatter}---\n\n# {title}\n\n{content}"
    main_file = content_dir / f"{result_id}.md"
    
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(main_content)
    
    # Save raw content file if provided
    if raw_content:
        raw_file = content_dir / f"{result_id}_raw.md"
        with open(raw_file, 'w', encoding='utf-8') as f:
            f.write(raw_content)
    
    return result_id


def parse_llm_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse frontmatter from LLM result markdown content"""
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


def get_llm_file_content(result_id: str) -> Tuple[Dict[str, Any], str]:
    """Get LLM result file content and metadata"""
    content_dir = get_llm_content_dir()
    file_path = content_dir / f"{result_id}.md"
    
    if not file_path.exists():
        raise FileNotFoundError(f"LLM result file not found: {result_id}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return parse_llm_frontmatter(content)


def list_llm_results() -> list:
    """List all LLM result files with metadata"""
    content_dir = get_llm_content_dir()
    results = []
    
    for file_path in content_dir.glob("*.md"):
        if file_path.name.endswith("_raw.md"):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metadata, _ = parse_llm_frontmatter(content)
            if metadata:
                results.append({
                    "id": metadata.get("id", file_path.stem),
                    "title": metadata.get("title", "Untitled"),
                    "prompt_used": metadata.get("prompt_used", "unknown"),
                    "model_used": metadata.get("model_used", "unknown"),
                    "source_type": metadata.get("source_type", "unknown"),
                    "created": metadata.get("created", ""),
                    "source_url": metadata.get("source_url")
                })
                
        except Exception as e:
            logger.warning(f"Error reading LLM result file {file_path}: {e}")
            continue
    
    # Sort by creation date (newest first)
    results.sort(key=lambda x: x.get("created", ""), reverse=True)
    return results