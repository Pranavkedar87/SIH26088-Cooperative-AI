-- ═══════════════════════════════════════════════════════════════════════════
-- SAHKAARSETU (SIH26088) — PHASE 3A.1 HUMAN HANDOFF MIGRATION
-- Additive migration for `grievances` table to support multilingual human handoff,
-- official reference codes, translated summaries, and source citations.
--
-- Instructions:
--   1. Open Supabase Dashboard → SQL Editor
--   2. Paste this entire file and click Run
--   3. Verify columns in Table Editor → grievances
--
-- Safety:
--   - Non-destructive: uses ADD COLUMN IF NOT EXISTS
--   - Safe to execute repeatedly (idempotent)
--   - Preserves all existing columns and default values
-- ═══════════════════════════════════════════════════════════════════════════

ALTER TABLE grievances 
  ADD COLUMN IF NOT EXISTS citizen_language TEXT DEFAULT 'mr',
  ADD COLUMN IF NOT EXISTS translated_summary TEXT,
  ADD COLUMN IF NOT EXISTS reference_code TEXT,
  ADD COLUMN IF NOT EXISTS source_citations JSONB DEFAULT '[]'::jsonb;

-- Fast index for human-readable reference code lookup
CREATE INDEX IF NOT EXISTS idx_grievances_reference_code ON grievances(reference_code);

COMMENT ON COLUMN grievances.citizen_language   IS 'Original language in which citizen communicated (e.g. mr, hi, en).';
COMMENT ON COLUMN grievances.translated_summary IS 'NMT translated summary of the citizen issue for local officer triage.';
COMMENT ON COLUMN grievances.reference_code    IS 'Human-readable assistance slip reference code (e.g. PACS-2026-A1B2C3).';
COMMENT ON COLUMN grievances.source_citations   IS 'JSON array of verified knowledge sources cited in the assistance guidance.';
