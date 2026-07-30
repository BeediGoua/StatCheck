-- ==============================================================================
-- SCHÉMA POSTGRESQL : LOT 7 (MOTEUR DE RECHERCHE RAG HYBRIDE)
-- ==============================================================================
-- Pré-requis : l'extension pgvector doit être installée.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Configuration FTS personnalisée pour le français
DROP TEXT SEARCH CONFIGURATION IF EXISTS french_unaccent CASCADE;
CREATE TEXT SEARCH CONFIGURATION french_unaccent ( COPY = french );
ALTER TEXT SEARCH CONFIGURATION french_unaccent
    ALTER MAPPING FOR hword, hword_part, word
    WITH unaccent, french_stem;


-- 1. CATALOGUE ET TRAÇABILITÉ
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS catalog_snapshots (
    snapshot_id VARCHAR(100) PRIMARY KEY,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    dataset_count INTEGER,
    content_sha256 VARCHAR(64),
    is_fixture BOOLEAN DEFAULT FALSE,
    description TEXT
);

-- 2. DOCUMENTS DE RECHERCHE (FTS + VECTOR)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS search_documents (
    dataset_id VARCHAR(100) PRIMARY KEY,
    catalog_snapshot_id VARCHAR(100) REFERENCES catalog_snapshots(snapshot_id),
    
    -- Méta-données brutes pour filtrage métier (Reranker Déterministe)
    indicator_code VARCHAR(100),
    title TEXT,
    description TEXT,
    frequency VARCHAR(50),
    unit VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Nouvelles méta-données pour la modélisation avancée
    dimensions text[],
    modalities text[],
    aliases text[],
    territory_levels text[],
    source_id VARCHAR(100),
    time_coverage_start DATE,
    time_coverage_end DATE,
    
    -- Indexation Lexicale (FTS)
    -- Le tsvector combinera (Titre A, Indicateur B, Description C, Modalités D)
    lexical_vector tsvector,
    
    -- Indexation Vectorielle (pgvector)
    -- Le texte narratif brut donné au LLM d'embedding
    embedding_text TEXT,
    -- Le vecteur généré (dimension 1024 pour BGE-M3 par exemple. Ajustable selon le modèle)
    embedding vector(1024),
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Fonction Trigger pour mettre à jour automatiquement le tsvector avec pondérations
CREATE OR REPLACE FUNCTION search_documents_tsvector_trigger() RETURNS trigger AS $$
BEGIN
  NEW.lexical_vector :=
    setweight(to_tsvector('french_unaccent', coalesce(NEW.title, '')), 'A') ||
    setweight(to_tsvector('french_unaccent', coalesce(NEW.indicator_code, '') || ' ' || coalesce(array_to_string(NEW.dimensions, ' '), '')), 'B') ||
    setweight(to_tsvector('french_unaccent', coalesce(NEW.description, '')), 'C') ||
    setweight(to_tsvector('french_unaccent', coalesce(array_to_string(NEW.modalities, ' '), '') || ' ' || coalesce(array_to_string(NEW.aliases, ' '), '')), 'D');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tsvectorupdate ON search_documents;
CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
    ON search_documents FOR EACH ROW EXECUTE FUNCTION search_documents_tsvector_trigger();

-- Index pour la recherche lexicale
CREATE INDEX IF NOT EXISTS idx_search_documents_lexical 
ON search_documents USING GIN (lexical_vector);

-- Note : Pas d'index vectoriel approximatif (HNSW/IVFFlat) pour le moment,
-- la recherche exacte par cosinus (<=>) suffit amplement sur un catalogue INSEE.

-- Table de hachage incrémental pour éviter de recalculer les embeddings
CREATE TABLE IF NOT EXISTS entity_embeddings (
    model_id VARCHAR(100) NOT NULL,
    text_hash VARCHAR(64) NOT NULL,
    original_text TEXT NOT NULL,
    embedding vector(1024),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (model_id, text_hash)
);

-- Fonction de recherche sémantique exacte (Cosinus)
CREATE OR REPLACE FUNCTION search_vectorial(query_embedding vector(1024), match_limit INT DEFAULT 50)
RETURNS TABLE (
    dataset_id VARCHAR(100),
    similarity NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sd.dataset_id,
        (1 - (sd.embedding <=> query_embedding))::NUMERIC AS similarity
    FROM search_documents sd
    WHERE sd.embedding IS NOT NULL
    ORDER BY sd.embedding <=> query_embedding
    LIMIT match_limit;
END;
$$ LANGUAGE plpgsql;

-- 3. ALIAS ET SYNONYMES MÉTIER
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS search_aliases (
    alias_id SERIAL PRIMARY KEY,
    concept_type VARCHAR(50) NOT NULL, -- 'INDICATOR', 'DIMENSION', 'MODALITY'
    normalized_code VARCHAR(100) NOT NULL,
    raw_term VARCHAR(255) NOT NULL,
    provenance VARCHAR(50), -- 'EXPERT_RULE', 'LLM_EXTRACTION'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(concept_type, normalized_code, raw_term)
);

-- 4. POOLING, LOGS ET ÉVALUATION
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS retrieval_runs (
    run_id UUID PRIMARY KEY,
    claim_id VARCHAR(100) NOT NULL,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    k_lexical INTEGER,
    k_vector INTEGER,
    rrf_k_constant INTEGER DEFAULT 60,
    lexical_weight NUMERIC DEFAULT 1.0,
    vector_weight NUMERIC DEFAULT 1.0,
    -- Configuration globale
    cross_encoder_used BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS retrieval_candidates (
    candidate_id UUID PRIMARY KEY,
    run_id UUID REFERENCES retrieval_runs(run_id) ON DELETE CASCADE,
    dataset_id VARCHAR(100) REFERENCES search_documents(dataset_id),
    
    -- Rangs bruts
    lexical_rank INTEGER,
    vector_rank INTEGER,
    present_in_both BOOLEAN,
    
    -- Score de fusion
    rrf_score NUMERIC,
    
    -- Scores métier déterministes (Garde-fous)
    deterministic_score NUMERIC,
    hard_constraint_failed BOOLEAN DEFAULT FALSE,
    failure_reason VARCHAR(100),
    
    -- Reranker Neuronal (Optionnel)
    cross_encoder_score NUMERIC,
    
    -- Position finale
    final_rank INTEGER
);

-- Table pour stocker le Gold (optionnel en base, mais pratique pour les métriques SQL)
CREATE TABLE IF NOT EXISTS relevance_judgments (
    claim_id VARCHAR(100) NOT NULL,
    dataset_id VARCHAR(100) NOT NULL,
    relevance_score INTEGER CHECK (relevance_score IN (0, 1, 2, 3)),
    is_hard_negative BOOLEAN DEFAULT FALSE,
    justification TEXT,
    PRIMARY KEY (claim_id, dataset_id)
);
