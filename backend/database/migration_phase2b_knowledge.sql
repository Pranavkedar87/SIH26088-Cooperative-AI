-- ═══════════════════════════════════════════════════════════════════════════
-- SAHKAARSETU (SIH26088) — PHASE 2B.1 GOVERNED KNOWLEDGE SAFETY GATE MIGRATION
-- Additive migration for `knowledge_documents`, `knowledge_chunks`,
-- `document_versions`, and RPC `match_knowledge_chunks`.
--
-- Objective:
--   Enforce at database/RPC level that ONLY documents with:
--     status = 'published' AND is_current = true
--   can participate in live citizen RAG vector retrieval.
--
-- Instructions:
--   1. Open Supabase Dashboard → SQL Editor
--   2. Paste this entire file and click Run
--   3. Verify table schema in Table Editor
--
-- Safety:
--   - Non-destructive: uses ALTER TABLE ... ADD COLUMN IF NOT EXISTS
--   - Preserves existing 768-dim embeddings and all knowledge chunks
--   - Applies conservative governance defaults to existing active corpus
-- ═══════════════════════════════════════════════════════════════════════════

-- ── 1. ADDITIVE GOVERNANCE COLUMNS ON knowledge_documents ──────────────────

ALTER TABLE knowledge_documents
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'published'
        CHECK (status IN ('draft', 'under_review', 'verified', 'published', 'review_due', 'outdated', 'superseded')),
    ADD COLUMN IF NOT EXISTS version TEXT NOT NULL DEFAULT 'v1.0',
    ADD COLUMN IF NOT EXISTS is_current BOOLEAN NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS parent_document_id UUID REFERENCES knowledge_documents(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS superseded_by UUID REFERENCES knowledge_documents(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS authority_level TEXT DEFAULT 'UNKNOWN',
    ADD COLUMN IF NOT EXISTS jurisdiction TEXT DEFAULT 'MAHARASHTRA',
    ADD COLUMN IF NOT EXISTS applicability JSONB DEFAULT '["ALL_COOPERATIVES"]'::jsonb,
    ADD COLUMN IF NOT EXISTS year INTEGER,
    ADD COLUMN IF NOT EXISTS effective_date DATE,
    ADD COLUMN IF NOT EXISTS expiry_review_date DATE,
    ADD COLUMN IF NOT EXISTS verification_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION'
        CHECK (verification_status IN ('VERIFIED_OFFICIAL', 'OFFICIAL_NEEDS_VERIFICATION', 'VERIFIED_EXPERT', 'REFERENCE_ONLY', 'NEEDS_VERIFICATION')),
    ADD COLUMN IF NOT EXISTS currentness_status TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION'
        CHECK (currentness_status IN ('ACTIVE_IN_FORCE', 'AMENDED', 'SUPERSEDED', 'DRAFT', 'NEEDS_VERIFICATION', 'UNKNOWN')),
    ADD COLUMN IF NOT EXISTS precedence_tier INTEGER NOT NULL DEFAULT 50,
    ADD COLUMN IF NOT EXISTS raw_file_url TEXT,
    ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ DEFAULT now(),
    ADD COLUMN IF NOT EXISTS published_by UUID REFERENCES users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS review_notes TEXT;

-- Indices for governance filtering, version queries, and status filtering
CREATE INDEX IF NOT EXISTS idx_knowledge_docs_status       ON knowledge_documents(status);
CREATE INDEX IF NOT EXISTS idx_knowledge_docs_is_current   ON knowledge_documents(is_current);
CREATE INDEX IF NOT EXISTS idx_knowledge_docs_parent       ON knowledge_documents(parent_document_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_docs_jurisdiction ON knowledge_documents(jurisdiction);


-- ── 2. ADDITIVE TRACEABILITY COLUMNS ON knowledge_chunks ───────────────────

ALTER TABLE knowledge_chunks
    ADD COLUMN IF NOT EXISTS page_number TEXT,
    ADD COLUMN IF NOT EXISTS section_number TEXT;

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_doc_chunk ON knowledge_chunks(document_id, chunk_index);


-- ── 3. DOCUMENT VERSION AUDIT TABLE ────────────────────────────────────────

CREATE TABLE IF NOT EXISTS document_versions (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id          UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    version              TEXT NOT NULL,
    status               TEXT NOT NULL CHECK (status IN ('draft', 'under_review', 'verified', 'published', 'review_due', 'outdated', 'superseded')),
    is_current           BOOLEAN NOT NULL DEFAULT false,
    effective_date       DATE,
    verification_status  TEXT NOT NULL DEFAULT 'NEEDS_VERIFICATION',
    notes                TEXT,
    created_by           UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_doc_versions_document_id ON document_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_doc_versions_is_current  ON document_versions(is_current);


-- ── 4. RAG VECTOR RETRIEVAL RPC FUNCTION (WITH SAFETY GATE) ────────────────

CREATE OR REPLACE FUNCTION match_knowledge_chunks (
  query_embedding vector(768),
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 5,
  filter_language text DEFAULT NULL,
  filter_intent text DEFAULT NULL
)
RETURNS TABLE (
  id uuid,
  document_id uuid,
  content text,
  chunk_index int,
  language text,
  metadata jsonb,
  similarity float,
  title text,
  source_name text,
  source_url text,
  document_type text,
  status text,
  version text,
  is_current boolean,
  authority_level text,
  jurisdiction text,
  applicability jsonb,
  verification_status text,
  currentness_status text,
  precedence_tier int
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    kc.id,
    kc.document_id,
    kc.content,
    kc.chunk_index,
    kc.language,
    kc.metadata,
    (1 - (kc.embedding <=> query_embedding))::float AS similarity,
    kd.title,
    kd.source_name,
    kd.source_url,
    kd.document_type,
    kd.status,
    kd.version,
    kd.is_current,
    kd.authority_level,
    kd.jurisdiction,
    kd.applicability,
    kd.verification_status,
    kd.currentness_status,
    kd.precedence_tier
  FROM knowledge_chunks kc
  JOIN knowledge_documents kd ON kc.document_id = kd.id
  WHERE kc.embedding IS NOT NULL
    -- CRITICAL SAFETY GATE: Only published and current documents participate in live RAG
    AND kd.status = 'published'
    AND kd.is_current = true
    AND (1 - (kc.embedding <=> query_embedding)) >= match_threshold
    AND (filter_language IS NULL OR kc.language = filter_language OR kc.language IS NULL)
  ORDER BY kc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;


-- ── 5. CONSERVATIVE DATA BACKFILL FOR EXISTING CORPUS ───────────────────────
-- Updates the 8 existing corpus documents with their verified metadata from
-- knowledge_base JSON files. Conservative defaults: verification_status = NEEDS_VERIFICATION
-- or OFFICIAL_NEEDS_VERIFICATION (never invented VERIFIED_OFFICIAL).

UPDATE knowledge_documents
SET
    status = 'published',
    version = 'v1.0',
    is_current = true,
    authority_level = 'CENTRAL_GOVERNMENT',
    jurisdiction = 'INDIA',
    applicability = '["ALL_COOPERATIVES"]'::jsonb,
    verification_status = 'OFFICIAL_NEEDS_VERIFICATION',
    currentness_status = 'NEEDS_VERIFICATION',
    precedence_tier = 70
WHERE title LIKE '%PMFBY%' OR title LIKE '%प्रधानमंत्री फसल%';

UPDATE knowledge_documents
SET
    status = 'published',
    version = 'v1.0',
    is_current = true,
    authority_level = 'NABARD',
    jurisdiction = 'INDIA',
    applicability = '["ALL_COOPERATIVES"]'::jsonb,
    verification_status = 'NEEDS_VERIFICATION',
    currentness_status = 'UNKNOWN',
    precedence_tier = 50
WHERE title LIKE '%Financial Literacy%';

UPDATE knowledge_documents
SET
    status = 'published',
    version = 'v1.0',
    is_current = true,
    authority_level = 'STATE_GOVERNMENT',
    jurisdiction = 'MAHARASHTRA',
    applicability = '["ALL_COOPERATIVES"]'::jsonb,
    verification_status = 'OFFICIAL_NEEDS_VERIFICATION',
    currentness_status = 'NEEDS_VERIFICATION',
    precedence_tier = 100
WHERE title LIKE '%Maharashtra Cooperative Societies Act%' OR title LIKE '%महाराष्ट्र सहकारी संस्था कायदा%';

UPDATE knowledge_documents
SET
    status = 'published',
    version = 'v1.0',
    is_current = true,
    authority_level = 'CENTRAL_GOVERNMENT',
    jurisdiction = 'INDIA',
    applicability = '["PACS"]'::jsonb,
    verification_status = 'NEEDS_VERIFICATION',
    currentness_status = 'UNKNOWN',
    precedence_tier = 50
WHERE title LIKE '%Primary Agricultural Credit Societies%' OR title LIKE '%प्राथमिक कृषी पतसंस्था%';
