-- ═══════════════════════════════════════════════════════════════════════════
-- SAHKAARSETU (SIH26088) — PHASE 2A.1 ADMIN AUTHENTICATION MIGRATION
-- Additive migration for `users` table to support secure Admin & Staff authentication.
--
-- Instructions:
--   1. Open Supabase Dashboard → SQL Editor
--   2. Paste this file and click Run
--   3. Verify columns in Table Editor → users
--
-- Safety:
--   - Non-destructive: uses ADD COLUMN IF NOT EXISTS
--   - Preserves existing columns: id, created_at, language
--   - Preserves existing foreign key constraints with sessions.user_id
-- ═══════════════════════════════════════════════════════════════════════════

ALTER TABLE users 
  ADD COLUMN IF NOT EXISTS email TEXT UNIQUE,
  ADD COLUMN IF NOT EXISTS password_hash TEXT,
  ADD COLUMN IF NOT EXISTS full_name TEXT,
  ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'STAFF' CHECK (role IN ('ADMIN', 'STAFF')),
  ADD COLUMN IF NOT EXISTS assigned_pacs TEXT,
  ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true,
  ADD COLUMN IF NOT EXISTS last_login TIMESTAMPTZ;

-- Indices for fast lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role  ON users(role);

COMMENT ON COLUMN users.email         IS 'Operator login email address (unique).';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt salted password hash (never plaintext).';
COMMENT ON COLUMN users.role          IS 'Operational role: ADMIN (full operations) or STAFF (assigned PACS/cases).';
COMMENT ON COLUMN users.assigned_pacs IS 'Optional PACS society name or jurisdiction assigned to this staff member.';
COMMENT ON COLUMN users.is_active     IS 'Whether the operator account is currently active.';
COMMENT ON COLUMN users.last_login    IS 'Timestamp of last successful authentication.';
