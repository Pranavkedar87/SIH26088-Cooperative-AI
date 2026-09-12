-- ═══════════════════════════════════════════════════════════════════════════
-- SAHKAARSETU (SIH26088) — PHASE 2A.2 ADMIN GRIEVANCE TRIAGE MIGRATION
-- Additive migration for `grievances` table to support administrative triage,
-- staff assignment, priority tagging, and internal notes.
--
-- Instructions:
--   1. Open Supabase Dashboard → SQL Editor
--   2. Paste this entire file and click Run
--   3. Verify columns in Table Editor → grievances
--
-- Safety:
--   - Non-destructive: uses ADD COLUMN IF NOT EXISTS
--   - Preserves all existing columns: id, conversation_id, category, description, status, created_at, updated_at
--   - Compatible with citizen intake: default values populated automatically
-- ═══════════════════════════════════════════════════════════════════════════

ALTER TABLE grievances 
  ADD COLUMN IF NOT EXISTS priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('urgent', 'high', 'medium', 'low')),
  ADD COLUMN IF NOT EXISTS assigned_staff TEXT,
  ADD COLUMN IF NOT EXISTS pacs_name TEXT,
  ADD COLUMN IF NOT EXISTS citizen_masked_name TEXT DEFAULT 'Citizen (Protected)',
  ADD COLUMN IF NOT EXISTS citizen_phone_masked TEXT DEFAULT '+91 98******45',
  ADD COLUMN IF NOT EXISTS staff_notes JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS ai_guidance TEXT;

-- Indices for fast query filtering and sorting
CREATE INDEX IF NOT EXISTS idx_grievances_priority        ON grievances(priority);
CREATE INDEX IF NOT EXISTS idx_grievances_assigned_staff  ON grievances(assigned_staff);
CREATE INDEX IF NOT EXISTS idx_grievances_pacs_name       ON grievances(pacs_name);

COMMENT ON COLUMN grievances.priority             IS 'Operational priority tier: urgent | high | medium | low';
COMMENT ON COLUMN grievances.assigned_staff       IS 'Name or email of assigned staff or field extension officer.';
COMMENT ON COLUMN grievances.pacs_name            IS 'PACS society jurisdiction associated with the complaint.';
COMMENT ON COLUMN grievances.citizen_masked_name  IS 'Privacy-masked display name of the citizen.';
COMMENT ON COLUMN grievances.citizen_phone_masked IS 'Privacy-masked contact phone number.';
COMMENT ON COLUMN grievances.staff_notes          IS 'Chronological array of internal staff observations and verification notes.';
COMMENT ON COLUMN grievances.ai_guidance          IS 'AI-generated guidance/summary provided during citizen assistance.';
