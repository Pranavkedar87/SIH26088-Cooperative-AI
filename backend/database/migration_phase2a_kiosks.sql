-- ═══════════════════════════════════════════════════════════════════════════
-- SAHKAARSETU (SIH26088) — PHASE 2A.3 KIOSK FLEET MONITORING MIGRATION
-- Additive migration for `kiosks` table to support rural touchpoint monitoring,
-- machine-to-machine heartbeat telemetry, and operational maintenance status.
--
-- Instructions:
--   1. Open Supabase Dashboard → SQL Editor
--   2. Paste this entire file and click Run
--   3. Verify table in Table Editor → kiosks
--
-- Safety:
--   - Non-destructive: uses CREATE TABLE IF NOT EXISTS
--   - Stores ONLY cryptographic SHA-256 hash in api_key_hash (never plaintext keys)
--   - Monitoring telemetry only (no remote execution or device control)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS kiosks (
    id                 TEXT PRIMARY KEY,
    name               TEXT NOT NULL,
    location           TEXT NOT NULL,
    district           TEXT NOT NULL,
    state              TEXT NOT NULL DEFAULT 'Maharashtra',
    pacs_name          TEXT NOT NULL,
    status             TEXT NOT NULL DEFAULT 'offline' CHECK (status IN ('online', 'offline', 'maintenance')),
    ip_address         TEXT,
    software_version   TEXT DEFAULT 'v2.4.1',
    installation_date  DATE DEFAULT CURRENT_DATE,
    uptime_percent     NUMERIC(5, 2) DEFAULT 99.0,
    health             JSONB NOT NULL DEFAULT '{"device": "ok", "network": "online", "printer": "ready", "sync": "synced"}'::jsonb,
    last_heartbeat     TIMESTAMPTZ,
    api_key_hash       TEXT,
    notes              TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indices for fast querying, filtering, and RBAC PACS isolation
CREATE INDEX IF NOT EXISTS idx_kiosks_pacs_name ON kiosks(pacs_name);
CREATE INDEX IF NOT EXISTS idx_kiosks_status    ON kiosks(status);
CREATE INDEX IF NOT EXISTS idx_kiosks_district  ON kiosks(district);

COMMENT ON TABLE kiosks                  IS 'Rural PACS kiosks deployed for citizen cooperative voice/vision assistance.';
COMMENT ON COLUMN kiosks.id              IS 'Unique kiosk identifier (e.g. KSK-001).';
COMMENT ON COLUMN kiosks.api_key_hash    IS 'Cryptographic SHA-256 hash of the machine-to-machine heartbeat key (never plaintext).';
COMMENT ON COLUMN kiosks.health          IS 'Diagnostic health JSON: device, network, printer, sync.';
COMMENT ON COLUMN kiosks.last_heartbeat  IS 'Timestamp of last verified telemetry heartbeat transmission.';
COMMENT ON COLUMN kiosks.status          IS 'Operational status: online (recent heartbeat) | offline | maintenance (admin controlled).';
