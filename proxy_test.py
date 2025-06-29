#!/usr/bin/env python3
"""
Tiny demo: fetch a YouTube transcript through an HTTP(S) proxy.

Requires:  pip install youtube-transcript-api
"""

import os
import sys
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
# ─── Edit these three lines ────────────────────────────────────────────────────
PROXY_HTTP_URL  = "http://159.196.114.23:3128"
PROXY_HTTPS_URL = PROXY_HTTP_URL                           # same endpoint for HTTPS CONNECT
VIDEO_ID        = sys.argv[1] if len(sys.argv) > 1 else "dQw4w9WgXcQ"
# ───────────────────────────────────────────────────────────────────────────────

def main() -> None:
    # Build a proxy‑aware API client
    api = YouTubeTranscriptApi(
        proxy_config=GenericProxyConfig(
            http_url=PROXY_HTTP_URL,
            https_url=PROXY_HTTPS_URL,
        )
    )

    try:
	
        transcript_fragments = api.fetch(VIDEO_ID)
        transcript_text = "\n".join(f.text for f in transcript_fragments)
        print(transcript_text)
    except Exception as err:  # youtube_transcript_api._errors could be more specific
        print(f"❌ Failed to fetch transcript for {VIDEO_ID}: {err}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
