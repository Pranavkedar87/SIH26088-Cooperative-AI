"""
Knowledge Base Ingestion Script.

Reads curated knowledge documents from `knowledge_base/`,
chunks content, generates 768-dim Gemini embeddings, and
persists documents and vector chunks into Supabase PostgreSQL.

Idempotent and safe to run multiple times.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import uuid

# Ensure backend root is on sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from database.supabase import get_supabase_client
from rag.chunker import chunk_text
from rag.embeddings import GeminiEmbeddingProvider

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger("ingest_knowledge")


def _gen_uuid() -> str:
    return str(uuid.uuid4())


def run_ingestion():
    client = get_supabase_client()
    if client is None:
        logger.error("❌ Supabase client is unconfigured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env")
        sys.exit(1)

    kb_dir = os.path.join(os.path.dirname(BACKEND_DIR), "knowledge_base")
    if not os.path.exists(kb_dir):
        logger.error("❌ Knowledge base directory not found at %s", kb_dir)
        sys.exit(1)

    embedding_provider = GeminiEmbeddingProvider()

    json_files = []
    for root, _, files in os.walk(kb_dir):
        for f in files:
            if f.endswith(".json"):
                json_files.append(os.path.join(root, f))

    logger.info("Found %d knowledge document files to process in %s", len(json_files), kb_dir)

    total_docs = 0
    total_chunks = 0

    for filepath in json_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                doc_data = json.load(f)
        except Exception as exc:
            logger.error("Failed to read JSON file %s: %s", filepath, exc)
            continue

        title = doc_data.get("title")
        content = doc_data.get("content")
        if not title or not content:
            logger.warning("Skipping %s — missing title or content", filepath)
            continue

        description = doc_data.get("description")
        source_name = doc_data.get("source_name")
        source_url = doc_data.get("source_url")
        document_type = doc_data.get("document_type", "guide")
        language = doc_data.get("language", "en")

        logger.info("Processing document: '%s' (%s)", title, language)

        # Remove existing document with same title for idempotency
        try:
            existing = client.table("knowledge_documents").select("id").eq("title", title).execute()
            if existing and existing.data:
                for old in existing.data:
                    doc_id_to_del = old["id"]
                    client.table("knowledge_chunks").delete().eq("document_id", doc_id_to_del).execute()
                    client.table("knowledge_documents").delete().eq("id", doc_id_to_del).execute()
                logger.info("Deleted previous instance of document '%s'", title)
        except Exception as exc:
            logger.debug("Idempotency cleanup check: %s", exc)

        # 1. Insert document record
        doc_id = _gen_uuid()
        try:
            client.table("knowledge_documents").insert({
                "id": doc_id,
                "title": title,
                "description": description,
                "source_name": source_name,
                "source_url": source_url,
                "document_type": document_type,
                "language": language,
            }).execute()
            total_docs += 1
        except Exception as exc:
            logger.error("Failed to insert document '%s': %s", title, exc)
            continue

        # 2. Chunk text
        chunks = chunk_text(content, max_chunk_size=500, overlap=50)
        logger.info("Generated %d chunks for document '%s'", len(chunks), title)

        # 3. Embed & insert chunks
        for idx, chunk_str in enumerate(chunks):
            embedding_vec = embedding_provider.embed_text(chunk_str)
            chunk_id = _gen_uuid()

            chunk_record = {
                "id": chunk_id,
                "document_id": doc_id,
                "content": chunk_str,
                "chunk_index": idx,
                "language": language,
                "metadata": {
                    "source_name": source_name,
                    "source_url": source_url,
                    "document_type": document_type,
                    "embedding": embedding_vec,
                },
                "embedding": embedding_vec,
            }

            try:
                client.table("knowledge_chunks").insert(chunk_record).execute()
                total_chunks += 1
            except Exception as exc:
                # If 'embedding' column is missing from table schema cache, retry without column field
                # (embedding remains safely stored inside metadata JSONB for python similarity search)
                try:
                    chunk_record_no_col = dict(chunk_record)
                    del chunk_record_no_col["embedding"]
                    client.table("knowledge_chunks").insert(chunk_record_no_col).execute()
                    total_chunks += 1
                except Exception as exc2:
                    logger.error("Failed to insert chunk %d for doc '%s': %s", idx, title, exc2)

    logger.info("\n" + "="*50)
    logger.info("🎉 Ingestion complete!")
    logger.info("   Documents ingested: %d", total_docs)
    logger.info("   Chunks stored:     %d", total_chunks)
    logger.info("="*50)


if __name__ == "__main__":
    run_ingestion()
