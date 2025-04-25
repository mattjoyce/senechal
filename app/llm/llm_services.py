"""LLM services for extracting rowing data from machine screenshots."""
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict

import llm

from app.health.models import RowingData

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