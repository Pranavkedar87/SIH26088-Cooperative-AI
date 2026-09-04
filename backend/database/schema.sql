-- ═══════════════════════════════════════════════════════════════════════════
-- SIH26088 — Cooperative AI Assistant
-- Supabase PostgreSQL Schema — Task 3
--
-- Instructions:
--   1. Open your Supabase project → SQL Editor
--   2. Paste this entire file and click Run
--   3. Verify tables in Table Editor
--
-- Notes:
--   - Run this once on a fresh project.
--   - Re-running is safe: all statements use IF NOT EXISTS / OR REPLACE.
--   - pgvector extension is enabled but the embedding column is NOT added yet.
--     It will be added in Task 5 (RAG) once the embedding dimension is finalised.
-- ═══════════════════════════════════════════════════════════════════════════


-- ── Extensions ──────────────────────────────────────────────────────────────

-- UUID generation (built into Supabase, included for completeness)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- pgvector — enable now so the extension is ready for Task 5 (RAG/embeddings)
-- The vector column will be added to knowledge_chunks during Task 5.
CREATE EXTENSION IF NOT EXISTS vector;


-- ── TABLE: users ────────────────────────────────────────────────────────────
-- Foundation for future authentication. Not actively used yet.

CREATE TABLE IF NOT EXISTS users (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    language    TEXT        NOT NULL DEFAULT 'en'
);

COMMENT ON TABLE  users            IS 'Cooperative AI users — authentication will be added in a future task.';
COMMENT ON COLUMN users.language   IS 'Preferred language: en | hi | mr';


-- ── TABLE: sessions ─────────────────────────────────────────────────────────
-- One session per browser/device visit. Groups conversations together.

CREATE TABLE IF NOT EXISTS sessions (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        REFERENCES users(id) ON DELETE SET NULL,
    language    TEXT        NOT NULL DEFAULT 'en',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE sessions IS 'Browser sessions. user_id is nullable until authentication is added.';

CREATE INDEX IF NOT EXISTS idx_sessions_user_id   ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at DESC);


-- ── TABLE: conversations ─────────────────────────────────────────────────────
-- One session can have multiple topic-based conversations.

CREATE TABLE IF NOT EXISTS conversations (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID        NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    title       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE conversations IS 'A grouped sequence of messages within a session.';

CREATE INDEX IF NOT EXISTS idx_conversations_session_id  ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at  ON conversations(created_at DESC);


-- ── TABLE: messages ──────────────────────────────────────────────────────────
-- Individual user and assistant messages.

CREATE TABLE IF NOT EXISTS messages (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id  UUID        NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role             TEXT        NOT NULL CHECK (role IN ('user', 'assistant')),
    content          TEXT        NOT NULL,
    language         TEXT        NOT NULL DEFAULT 'en',
    intent           TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  messages                  IS 'Individual chat messages (user and assistant turns).';
COMMENT ON COLUMN messages.role             IS 'user | assistant';
COMMENT ON COLUMN messages.intent           IS 'Classified intent, e.g. PMFBY, GRIEVANCE, PACS_SERVICE';

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at      ON messages(created_at ASC);


-- ── TABLE: knowledge_documents ───────────────────────────────────────────────
-- Metadata for official cooperative/legal documents.
-- Content rows are inserted in Task 5 (RAG). Do NOT insert fake data.

CREATE TABLE IF NOT EXISTS knowledge_documents (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    title          TEXT        NOT NULL,
    description    TEXT,
    source_name    TEXT,
    source_url     TEXT,
    document_type  TEXT,
    language       TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE knowledge_documents IS 'Metadata for official cooperative/legal source documents. Populated in Task 5 (RAG).';


-- ── TABLE: knowledge_chunks ──────────────────────────────────────────────────
-- Text chunks from knowledge documents.
-- The `embedding` vector column is intentionally omitted here.
-- It will be added in Task 5 once the Gemini embedding dimension is confirmed.
-- Adding a vector column with the wrong dimension would require a table rebuild.

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id    UUID        NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    content        TEXT        NOT NULL,
    chunk_index    INTEGER     NOT NULL,
    language       TEXT,
    metadata       JSONB,
    embedding      vector(768),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  knowledge_chunks             IS 'Text chunks from knowledge documents with 768-dim Gemini embeddings.';
COMMENT ON COLUMN knowledge_chunks.chunk_index IS 'Position of this chunk within its source document (0-based).';
COMMENT ON COLUMN knowledge_chunks.metadata    IS 'JSON metadata: page number, section, headings, etc.';

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_document_id ON knowledge_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_language    ON knowledge_chunks(language);

-- Vector similarity search RPC function
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
  document_type text
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
    kd.document_type
  FROM knowledge_chunks kc
  JOIN knowledge_documents kd ON kc.document_id = kd.id
  WHERE kc.embedding IS NOT NULL
    AND (1 - (kc.embedding <=> query_embedding)) >= match_threshold
    AND (filter_language IS NULL OR kc.language = filter_language OR kc.language IS NULL)
  ORDER BY kc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;


-- ── TABLE: grievances ────────────────────────────────────────────────────────
-- Basic grievance records. Workflow will be implemented in a future task.

CREATE TABLE IF NOT EXISTS grievances (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id  UUID        REFERENCES conversations(id) ON DELETE SET NULL,
    category         TEXT,
    description      TEXT        NOT NULL,
    status           TEXT        NOT NULL DEFAULT 'draft',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  grievances        IS 'Cooperative grievance submissions. Workflow implemented in a future task.';
COMMENT ON COLUMN grievances.status IS 'Current status: draft | submitted | under_review | resolved | closed';

CREATE INDEX IF NOT EXISTS idx_grievances_status         ON grievances(status);
CREATE INDEX IF NOT EXISTS idx_grievances_created_at     ON grievances(created_at DESC);


-- ── Row Level Security ───────────────────────────────────────────────────────
-- RLS is enabled on all tables.
-- No public policies are created here — the FastAPI backend uses the
-- service-role key which bypasses RLS entirely.
-- User-facing policies will be added in Task 6 (Authentication).

ALTER TABLE users                ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions             ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations        ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages             ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_documents  ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_chunks     ENABLE ROW LEVEL SECURITY;
ALTER TABLE grievances           ENABLE ROW LEVEL SECURITY;

-- ═══════════════════════════════════════════════════════════════════════════
-- Schema complete.
-- Next step: copy SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
-- from Supabase Dashboard → Project Settings → API into backend/.env
-- ═══════════════════════════════════════════════════════════════════════════
