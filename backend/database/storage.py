"""
Storage service for knowledge document uploads.
Uses persistent private Supabase Storage bucket ('knowledge_documents')
with safe fallback to local scratch/uploads directory for offline development/testing.
"""
from __future__ import annotations

import os
import re
import uuid
import logging
from typing import Optional, Tuple

from database.supabase import get_supabase_client

logger = logging.getLogger(__name__)

KNOWLEDGE_BUCKET_NAME = "knowledge_documents"
MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".json", ".csv"}
DISALLOWED_EXTENSIONS = {
    ".exe", ".sh", ".bat", ".cmd", ".py", ".pyc", ".js", ".ts", ".html",
    ".htm", ".php", ".bin", ".dll", ".so", ".vbs", ".ps1", ".jar", ".war"
}


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and shell injection.
    Strips directory paths and restricts to safe alphanumeric, dot, underscore, dash.
    """
    if not filename:
        return f"document_{uuid.uuid4().hex[:8]}.pdf"
    
    # Strip directory components
    base = os.path.basename(filename).strip()
    # Remove null bytes
    base = base.replace("\x00", "")
    # Replace dangerous characters
    safe = re.sub(r"[^\w\.\-\s]", "_", base)
    # Collapse multiple dots to prevent .. traversal
    safe = re.sub(r"\.{2,}", ".", safe)
    # Trim whitespace
    safe = safe.strip()
    if not safe or safe.startswith("."):
        safe = f"doc_{uuid.uuid4().hex[:8]}_{safe.lstrip('.')}"
    return safe[:120]  # Safe length limit


def validate_file_content(content: bytes, filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate file content against allowed MIME types and inspect magic bytes.
    Returns (is_valid, error_message).
    """
    if not content or len(content) == 0:
        return False, "File is empty (0 bytes). Please upload a valid document."

    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        max_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        return False, f"File exceeds maximum allowed size of {max_mb} MB."

    ext = os.path.splitext(filename)[1].lower()

    if ext in DISALLOWED_EXTENSIONS:
        return False, f"Executable or script file type '{ext}' is strictly prohibited."

    if ext not in ALLOWED_EXTENSIONS:
        allowed_list = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return False, f"File extension '{ext}' is not supported. Supported extensions: {allowed_list}."

    # Magic byte verification
    if ext == ".pdf":
        # PDFs must begin with %PDF-
        if not content.startswith(b"%PDF-"):
            return False, "Malformed or invalid PDF file header (missing %PDF- signature)."
    elif ext in {".txt", ".md", ".csv"}:
        # Plaintext files must not contain binary null bytes and must decode cleanly
        if b"\x00" in content:
            return False, "File contains forbidden binary characters (null bytes)."
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content.decode("latin-1")
            except Exception:
                return False, "Text document is not valid UTF-8 or standard text encoding."
    elif ext == ".json":
        import json
        try:
            json.loads(content.decode("utf-8"))
        except Exception as exc:
            return False, f"Invalid JSON document structure: {str(exc)}"

    return True, None


def store_knowledge_file(
    content: bytes,
    filename: str,
    doc_id: str,
    content_type: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Persist uploaded file safely into Supabase Storage.
    Falls back to backend/scratch/uploads for offline development.
    Returns (storage_path, raw_file_url).
    """
    safe_name = sanitize_filename(filename)
    storage_path = f"uploads/{doc_id}/{safe_name}"

    # Inferred MIME type
    ext = os.path.splitext(safe_name)[1].lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".json": "application/json",
        ".csv": "text/csv",
    }
    resolved_mime = content_type or mime_map.get(ext, "application/octet-stream")

    client = get_supabase_client()
    if client is not None:
        try:
            res = client.storage.from_(KNOWLEDGE_BUCKET_NAME).upload(
                storage_path,
                content,
                file_options={"content-type": resolved_mime, "upsert": "true"},
            )
            logger.info("Uploaded knowledge file to Supabase Storage: %s", storage_path)
            file_url = f"/api/admin/knowledge/documents/{doc_id}/file"
            return storage_path, file_url
        except Exception as exc:
            logger.warning("Supabase Storage upload error, engaging safe local fallback: %s", exc)

    # Local fallback persistence
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    local_dir = os.path.join(backend_dir, "scratch", "uploads", doc_id)
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, safe_name)
    with open(local_path, "wb") as f:
        f.write(content)

    logger.info("Saved knowledge file locally to %s", local_path)
    file_url = f"/api/admin/knowledge/documents/{doc_id}/file"
    return storage_path, file_url


def read_knowledge_file(storage_path: str, doc_id: str) -> Optional[bytes]:
    """
    Read stored file content from Supabase Storage or local fallback.
    """
    client = get_supabase_client()
    if client is not None:
        try:
            data = client.storage.from_(KNOWLEDGE_BUCKET_NAME).download(storage_path)
            if data:
                return data
        except Exception as exc:
            logger.debug("Failed to download from Supabase Storage, checking local fallback: %s", exc)

    # Local fallback check
    safe_name = sanitize_filename(os.path.basename(storage_path))
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    local_path = os.path.join(backend_dir, "scratch", "uploads", doc_id, safe_name)
    if os.path.exists(local_path):
        with open(local_path, "rb") as f:
            return f.read()

    return None


def extract_text_and_pages(content: bytes, filename: str) -> list[tuple[int, str]]:
    """
    Extract text from file bytes preserving page/section structure.
    Returns list of (page_number, text).
    """
    if not content:
        return []

    ext = os.path.splitext(filename.lower())[1]

    if ext in (".txt", ".md", ".csv"):
        text = content.decode("utf-8", errors="replace").strip()
        return [(1, text)] if text else []

    if ext == ".json":
        try:
            parsed = json.loads(content.decode("utf-8", errors="replace"))
            if isinstance(parsed, dict):
                lines = [f"{k}: {v}" for k, v in parsed.items()]
                text = "\n".join(lines)
            elif isinstance(parsed, list):
                text = "\n".join(str(item) for item in parsed)
            else:
                text = str(parsed)
            return [(1, text.strip())] if text.strip() else []
        except Exception:
            text = content.decode("utf-8", errors="replace").strip()
            return [(1, text)] if text else []

    if ext == ".pdf":
        import zlib
        # Split by streams and extract text objects
        stream_matches = re.findall(b"stream[\r\n]+(.*?)[\r\n]+endstream", content, re.DOTALL)
        extracted_chunks: list[str] = []
        for raw_stream in stream_matches:
            stream_data = raw_stream
            try:
                stream_data = zlib.decompress(raw_stream)
            except Exception:
                pass
            text_parts = re.findall(rb"\((.*?)\)\s*T[jJ]", stream_data)
            if text_parts:
                text = " ".join(tp.decode("utf-8", errors="ignore") for tp in text_parts if tp)
                if text.strip():
                    extracted_chunks.append(text.strip())
        if extracted_chunks:
            return [(i + 1, t) for i, t in enumerate(extracted_chunks)]

        # Fallback: scan for readable strings in PDF byte stream
        words = re.findall(rb"[A-Za-z0-9\u0900-\u097F,.\- ]{4,}", content)
        cleaned_words = [
            w.decode("utf-8", errors="ignore")
            for w in words
            if not w.startswith(b"PDF") and not w.startswith(b"obj") and not w.startswith(b"endobj")
        ]
        text = " ".join(cleaned_words).strip()
        if text:
            return [(1, text)]

    # General fallback
    try:
        text = content.decode("utf-8", errors="replace").strip()
        return [(1, text)] if text else []
    except Exception:
        return []

