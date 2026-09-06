"""
Voice Response Processor for SahkaarSetu (SIH26088).

Transforms retrieved RAG / Web Search factual answers into Alexa-style short, natural,
conversational spoken responses (1-3 sentences) paired with rich display answers.
"""
from __future__ import annotations

import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def clean_spoken_text(text: str) -> str:
    """
    Strips markdown formatting, headings, bullet markers, URLs, citations,
    and technical artifacts for clean, natural speech TTS playback.
    """
    if not text:
        return ""
    # Strip URLs
    cleaned = re.sub(r'https?://\S+', '', text)
    # Strip markdown headers, asterisks, underscores, backticks, hashes
    cleaned = re.sub(r'#+\s*', '', cleaned)
    cleaned = re.sub(r'[\*\_\`]', '', cleaned)
    # Strip :: artifacts or technical metadata
    cleaned = re.sub(r'::+', ' ', cleaned)
    # Strip citation brackets e.g. [1], [Web-1], [Source: ...]
    cleaned = re.sub(r'\[\s*(?:web-)?\d+\s*\]', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
    # Strip leading bullet numbers/markers line by line
    cleaned = re.sub(r'^\s*[-*+•]\s+', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^\s*\d+[\.\)]\s+', '', cleaned, flags=re.MULTILINE)
    # Collapse whitespace & newlines into natural speech spacing
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def format_alexa_spoken_answer(
    user_query: str,
    factual_answer: str,
    language: str = "mr",
) -> str:
    """
    Converts raw factual/retrieved answer into a short, natural Alexa-style spoken sentence.
    Target: 1-3 concise, conversational sentences without markdown or technical jargon.
    """
    cleaned = clean_spoken_text(factual_answer)
    if not cleaned:
        if language == "hi":
            return "क्षमा करें, मुझे इस प्रश्न की सटीक जानकारी नहीं मिल सकी। कृपया पुनः पूछें।"
        elif language == "en":
            return "I couldn't find exact details for that. Could you please rephrase your question?"
        else:
            return "क्षमस्व, मला या प्रश्नाची अचूक माहिती मिळाली नाही. कृपया पुन्हा विचारून पहा."

    # Extract first 2-3 sentences max for spoken answer
    sentences = re.split(r'(?<=[.!?।])\s+', cleaned)
    short_sentences = [s.strip() for s in sentences if len(s.strip()) > 5][:3]
    spoken_summary = " ".join(short_sentences) if short_sentences else cleaned[:200]

    # Ensure spoken answer ends with clean punctuation
    if spoken_summary and spoken_summary[-1] not in ".!?।":
        spoken_summary += "." if language == "en" else "।"

    return spoken_summary


def generate_voice_response(
    user_query: str,
    factual_answer: str,
    language: str = "mr",
    sources: Optional[list[dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Generates presentation payload containing:
    1. display_answer: Rich text formatted response with sources.
    2. spoken_answer: Short, natural Alexa-style spoken text.
    """
    spoken = format_alexa_spoken_answer(user_query, factual_answer, language)

    return {
        "display_answer": factual_answer,
        "spoken_answer": spoken,
        "language": language,
        "sources": sources or [],
    }
