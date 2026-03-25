-- ═══════════════════════════════════════════════════
--  DeggBi AI — Schema Supabase
--  À exécuter dans Supabase SQL Editor
-- ═══════════════════════════════════════════════════

-- Extension pgvector pour le RAG
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Table principale des analyses ───────────────
CREATE TABLE IF NOT EXISTS analyses (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_type    TEXT NOT NULL,          -- text, image, audio, video
    channel         TEXT NOT NULL,          -- whatsapp, telegram, api
    sender_id       TEXT,                   -- numéro WhatsApp ou chat_id Telegram
    score_truthscan FLOAT NOT NULL DEFAULT 0,
    score_deepshield FLOAT NOT NULL DEFAULT 0,
    score_final     FLOAT NOT NULL DEFAULT 0,
    verdict         TEXT NOT NULL,
    report_text     TEXT,
    analysis_time_ms INTEGER,
    language        TEXT DEFAULT 'fr',
    media_url       TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour le dashboard (tri par date)
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_channel ON analyses(channel);
CREATE INDEX IF NOT EXISTS idx_analyses_verdict ON analyses(verdict);

-- ─── Table embeddings RAG (pgvector) ─────────────
CREATE TABLE IF NOT EXISTS embeddings (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content     TEXT NOT NULL,
    source_url  TEXT,
    language    TEXT DEFAULT 'fr',
    embedding   vector(768),    -- AfroXLMR dimension
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Index vectoriel pour recherche sémantique rapide
CREATE INDEX IF NOT EXISTS idx_embeddings_vector
    ON embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- ─── Table sessions bot ──────────────────────────
CREATE TABLE IF NOT EXISTS bot_sessions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sender_id   TEXT NOT NULL,
    channel     TEXT NOT NULL,
    state       TEXT DEFAULT 'idle',
    last_seen   TIMESTAMPTZ DEFAULT NOW(),
    analyses_count INTEGER DEFAULT 0
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_sender
    ON bot_sessions(sender_id, channel);

-- ─── Supabase Storage — bucket médias ────────────
INSERT INTO storage.buckets (id, name, public)
VALUES ('media-inbox', 'media-inbox', false)
ON CONFLICT DO NOTHING;

-- Politique : service role uniquement peut écrire
CREATE POLICY "Service role can upload media"
    ON storage.objects FOR INSERT
    TO service_role
    WITH CHECK (bucket_id = 'media-inbox');

CREATE POLICY "Service role can read media"
    ON storage.objects FOR SELECT
    TO service_role
    USING (bucket_id = 'media-inbox');

-- ─── Realtime pour le dashboard ──────────────────
ALTER TABLE analyses REPLICA IDENTITY FULL;

-- ─── Vues utiles pour le dashboard ───────────────
CREATE OR REPLACE VIEW dashboard_stats AS
SELECT
    COUNT(*)                                        AS total_analyses,
    COUNT(*) FILTER (WHERE verdict LIKE '%DEEPFAKE%')  AS deepfakes_detected,
    COUNT(*) FILTER (WHERE verdict LIKE '%ARNAQUE%')   AS arnaques_detected,
    COUNT(*) FILTER (WHERE verdict = 'CONTENU FIABLE') AS contenus_fiables,
    AVG(analysis_time_ms)::INTEGER                  AS avg_time_ms,
    COUNT(DISTINCT sender_id)                       AS unique_users
FROM analyses
WHERE created_at > NOW() - INTERVAL '30 days';

-- ─── Données de test (démo hackathon) ────────────
INSERT INTO analyses (
    content_type, channel, sender_id,
    score_truthscan, score_deepshield, score_final,
    verdict, report_text, analysis_time_ms
) VALUES
(
    'audio', 'whatsapp', '221771234567',
    92, 96, 94,
    'DEEPFAKE CONFIRMÉ',
    '🚨 *DEEPFAKE CONFIRMÉ* — Score 94/100 — Voix synthétique détectée',
    18000
),
(
    'image', 'whatsapp', '221781234567',
    70, 86, 78,
    'PROBABLEMENT FAUX',
    '🔴 *PROBABLEMENT FAUX* — Score 78/100 — Image Bangladesh 2022',
    22000
),
(
    'text', 'whatsapp', '221791234567',
    88, 0, 88,
    'ARNAQUE CONFIRMÉE',
    '🚫 *ARNAQUE CONFIRMÉE* — Score 88/100 — Phishing Orange Money',
    9000
);

SELECT 'Schema DeggBi AI initialisé avec succès ✅' AS status;
