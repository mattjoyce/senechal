import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os

import requests
import yaml
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig

from app.config import (JINAAI_API_KEY, JINAAI_URL, LEARNING_CONTENT_PATH,PROXY_HTTP_URL, PROXY_HTTPS_URL,
                        YOUTUBE_API_KEY, YOUTUBE_API_URL)

# Get logger
logger = logging.getLogger("api")


def get_content_path(file_id: str) -> Path:
    """
    Get the path to a learning content file

    Args:
        file_id: ID of the learning content file

    Returns:
        Path to the file
    """
    return  Path(f"{LEARNING_CONTENT_PATH}/{file_id}.md").absolute()


def save_learning_content(
    title: str,
    content: str,
    source_url: Optional[str] = None,
    content_type: str = "text",
    raw_content: Optional[str] = None,
    channel_name: Optional[str] = None,
) -> str:
    """
    Save learning content to a markdown file with frontmatter

    Args:
        title: Title of the content
        content: The main content text (processed/extracted knowledge)
        source_url: Optional source URL
        content_type: Type of content (webpage, youtube, text)
        raw_content: Optional original raw content
        channel_name: Optional channel name for YouTube videos

    Returns:
        ID of the created file
    """
    # Generate a unique ID for the file
    file_id = str(uuid.uuid4())[:8]

    # Create frontmatter metadata
    metadata = {
        "id": file_id,
        "title": title,
        "created": datetime.utcnow().isoformat(),
        "source_url": source_url,
        "content_type": content_type,
        "status": "active",
    }
    
    # Add channel name if provided (for YouTube videos)
    if channel_name:
        metadata["channel_name"] = channel_name

    # Format the markdown file with frontmatter
    frontmatter = yaml.dump(metadata, default_flow_style=False)
    file_content = f"---\n{frontmatter}---\n\n{content}"

    # Save to file
    file_path = get_content_path(file_id)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(file_content)

    # Optionally save raw content to a separate file
    if raw_content:
        raw_path = Path(f"{LEARNING_CONTENT_PATH}/{file_id}_raw.md").absolute()
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(raw_content)

    logger.info(f"Saved learning content to {file_path}")
    return file_id


def parse_frontmatter(content: str) -> tuple:
    """
    Parse YAML frontmatter from markdown content

    Args:
        content: Markdown content with frontmatter

    Returns:
        tuple: (frontmatter_dict, content_without_frontmatter)
    """
    frontmatter_pattern = r"^---\n(.*?)\n---\n\n(.*)"
    match = re.search(frontmatter_pattern, content, re.DOTALL)

    if not match:
        return {}, content

    try:
        frontmatter = yaml.safe_load(match.group(1))
        content = match.group(2)
        return frontmatter, content
    except Exception as e:
        logger.error(f"Error parsing frontmatter: {e}")
        return {}, content


def scrape_url(url: str) -> dict:
    """
    Scrape content from a URL
    
    Args:
        url: URL to scrape
        
    Returns:
        dict: Dictionary containing content and metadata
    """
    url_str = str(url)
    # Check if the URL is a YouTube link
    if 'youtube.com' in url_str or 'youtu.be' in url_str:
        # Use YouTube specific extraction
        title, content = get_youtube_transcript(url_str)
        
        # Extract channel name from content
        channel_name = None
        if "**Author:** " in content:
            author_line = [line for line in content.split('\n') if line.startswith('**Author:** ')][0]
            channel_name = author_line.replace('**Author:** ', '')
        
        return {
            'content': content,
            'title': title,
            'channel_name': channel_name,
            'content_type': 'youtube'
        }



    # build jin ai request
    jina_url = JINAAI_URL + str(url)
    bearer_token = f"Bearer {JINAAI_API_KEY}"

    ## scrape url
    headers = {
        "Authorization": bearer_token,
        "X-Remove-Selector": "header, .class, #id",
        "X-Retain-Images": "none",
        "X-Return-Format": "markdown",
    }

    logger.info(f"Requesting JINA URL: {jina_url}")
    response = requests.get(jina_url, headers=headers)
    
    return {
        'content': response.text,
        'title': None,
        'channel_name': None,
        'content_type': 'webpage'
    }


   

def extract_youtube_id(url: str) -> str:
    """
    Extract YouTube video ID from various URL formats
    
    Args:
        url: YouTube URL (supports regular youtube.com, youtu.be, embed, shorts)
        
    Returns:
        Video ID or empty string if not found
    """
    import re
    
    # Common YouTube URL patterns
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([^&\?/]+)',
        r'youtube\.com/watch\?.*v=([^&]+)',
        r'youtube\.com/v/([^&\?/]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return ""


def get_youtube_transcript(url: str) -> tuple[str, str]:
    """
    Download transcript and metadata for a YouTube video
    
    Args:
        url: YouTube URL
        
    Returns:
        tuple: (title, formatted_content)
    """

    video_id = extract_youtube_id(url)
    if not video_id:
        raise ValueError(f"Could not extract YouTube video ID from URL: {url}")
    
    # Get video details using YouTube API
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY environment variable not set")
    
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    request = youtube.videos().list(
        part="snippet",
        id=video_id
    )
    response = request.execute()
    
    if 'items' not in response or not response['items']:
        raise ValueError(f"Video details not found for ID: {video_id}")
    
    snippet = response['items'][0]['snippet']
    title = snippet['title']
    author = snippet['channelTitle']
    date = snippet['publishedAt']
    description = snippet['description']
    
    # Get transcript (proxy optional; use only if configured)
    try:
        proxy_config = None
        if PROXY_HTTP_URL or PROXY_HTTPS_URL:
            proxy_config = GenericProxyConfig(
                http_url=PROXY_HTTP_URL,
                https_url=PROXY_HTTPS_URL,
            )

        if proxy_config:
            ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config)
        else:
            ytt_api = YouTubeTranscriptApi()

        transcript_list = ytt_api.fetch(video_id)
        transcript = '\n'.join([item.text for item in transcript_list])
        
        # Format content as markdown
        content = f"# {title}\n\n**Author:** {author}\n\n**Date:** {date}\n\n**Description:**\n\n{description}\n\n## Transcript\n\n{transcript}"
        return title, content
    except Exception as e:
        raise ValueError(f"Error downloading transcript for video {video_id}: {str(e)}")
