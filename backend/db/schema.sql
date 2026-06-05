-- Esegui questo nel SQL Editor di Supabase
-- https://app.supabase.com → tuo progetto → SQL Editor

-- Tabella principale: risultati screener aggiornati ogni notte
CREATE TABLE IF NOT EXISTS screener_results (
    id          BIGSERIAL PRIMARY KEY,
    ticker      TEXT NOT NULL UNIQUE,
    nome        TEXT,
    settore     TEXT,
    score       INTEGER DEFAULT 0,

    -- Metriche fondamentali
    pe_ratio            NUMERIC,
    revenue_growth      NUMERIC,   -- es. 0.15 = 15%
    margine_netto       NUMERIC,
    free_cash_flow      NUMERIC,
    debt_equity         NUMERIC,
    roe                 NUMERIC,

    -- Metriche tecniche
    prezzo_attuale      NUMERIC,
    momentum_1m         NUMERIC,
    momentum_3m         NUMERIC,
    momentum_6m         NUMERIC,
    momentum_1y         NUMERIC,

    -- Metadata
    aggiornato_il       TIMESTAMPTZ DEFAULT NOW(),
    passa_filtro        BOOLEAN DEFAULT FALSE
);

-- Tabella storico: ogni run notturno viene loggato
CREATE TABLE IF NOT EXISTS screener_history (
    id          BIGSERIAL PRIMARY KEY,
    ticker      TEXT NOT NULL,
    score       INTEGER,
    prezzo      NUMERIC,
    data_run    DATE NOT NULL,
    passa_filtro BOOLEAN
);

-- Indici per query veloci
CREATE INDEX IF NOT EXISTS idx_screener_score ON screener_results(score DESC);
CREATE INDEX IF NOT EXISTS idx_screener_filtro ON screener_results(passa_filtro);
CREATE INDEX IF NOT EXISTS idx_history_ticker ON screener_history(ticker, data_run);

-- View comoda: solo i candidati con score alto
CREATE OR REPLACE VIEW top_candidati AS
SELECT *
FROM screener_results
WHERE passa_filtro = TRUE
ORDER BY score DESC;
