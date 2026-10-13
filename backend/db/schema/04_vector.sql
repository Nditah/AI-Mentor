-- =============================================================================
-- 04 vector storage model
-- Qdrant stores the vectors; PostgreSQL is the system of record for what was
-- embedded, with which model, into which collection. That makes re-embedding
-- with a new model a controlled blue/green operation, and lets a reconciler
-- prove Qdrant matches the database.
--
-- Point id conventions:
--   chunk embeddings   -> Qdrant point id = knowledge.chunks.id
--   entity embeddings  -> Qdrant point id = vector.entity_embeddings.point_id
-- =============================================================================

CREATE TABLE vector.embedding_models (
    id               smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    provider         text NOT NULL CHECK (provider IN ('openai', 'azure_openai', 'cohere', 'voyage', 'gemini', 'local')),
    model            text NOT NULL,
    revision         text NOT NULL DEFAULT '1',
    dimensions       integer NOT NULL CHECK (dimensions BETWEEN 1 AND 8192),
    distance         text NOT NULL DEFAULT 'cosine' CHECK (distance IN ('cosine', 'dot', 'euclid')),
    max_input_tokens integer NOT NULL CHECK (max_input_tokens > 0),
    is_active        boolean NOT NULL DEFAULT true,
    created_at       timestamptz NOT NULL DEFAULT now(),
    retired_at       timestamptz,
    CONSTRAINT uq_embedding_models UNIQUE (provider, model, revision)
);

-- A physical Qdrant collection. `alias` is the logical name the API queries;
-- re-indexing builds a new collection, then swaps the alias.
CREATE TABLE vector.collections (
    id                 smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name               text NOT NULL UNIQUE CHECK (name ~ '^[a-z0-9_]{3,100}$'),
    alias              text NOT NULL CHECK (alias ~ '^[a-z0-9_]{3,60}$'),
    purpose            text NOT NULL CHECK (purpose IN ('curated_knowledge', 'personal_documents', 'concepts',
                           'questions', 'lessons', 'semantic_cache', 'learner_memory')),
    embedding_model_id smallint NOT NULL REFERENCES vector.embedding_models (id) ON DELETE RESTRICT,
    status             text NOT NULL DEFAULT 'building' CHECK (status IN ('building', 'active', 'draining', 'retired')),
    multitenant        boolean NOT NULL DEFAULT false,   -- true => every query must filter on owner_user_id
    shard_number       smallint NOT NULL DEFAULT 1 CHECK (shard_number BETWEEN 1 AND 256),
    replication_factor smallint NOT NULL DEFAULT 2 CHECK (replication_factor BETWEEN 1 AND 8),
    hnsw_m             smallint NOT NULL DEFAULT 16,
    hnsw_ef_construct  smallint NOT NULL DEFAULT 128,
    quantization       text NOT NULL DEFAULT 'scalar' CHECK (quantization IN ('none', 'scalar', 'product', 'binary')),
    on_disk_vectors    boolean NOT NULL DEFAULT false,
    point_count        bigint NOT NULL DEFAULT 0,        -- last reconciled count
    reconciled_at      timestamptz,
    created_at         timestamptz NOT NULL DEFAULT now(),
    activated_at       timestamptz,
    retired_at         timestamptz,
    CONSTRAINT ck_collections_personal_multitenant CHECK (purpose <> 'personal_documents' OR multitenant)
);
CREATE UNIQUE INDEX ux_collections_active_alias ON vector.collections (alias) WHERE status = 'active';

CREATE TABLE vector.chunk_embeddings (
    chunk_id      uuid     NOT NULL REFERENCES knowledge.chunks (id) ON DELETE CASCADE,
    collection_id smallint NOT NULL REFERENCES vector.collections (id) ON DELETE RESTRICT,
    content_hash  bytea    NOT NULL CHECK (octet_length(content_hash) = 32),
    status        text     NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'indexed', 'failed')),
    attempts      smallint NOT NULL DEFAULT 0,
    last_error    text,
    embedded_at   timestamptz,
    created_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (chunk_id, collection_id)
);
CREATE INDEX ix_chunk_embeddings_backlog ON vector.chunk_embeddings (collection_id, created_at)
    WHERE status <> 'indexed';

-- Embeddings of non-chunk entities: concepts, lessons, questions (dedup and
-- similar-question search), learner memories, semantic cache keys.
CREATE TABLE vector.entity_embeddings (
    point_id      uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    collection_id smallint NOT NULL REFERENCES vector.collections (id) ON DELETE RESTRICT,
    entity_type   text NOT NULL CHECK (entity_type IN ('concept', 'lesson_content', 'question', 'coding_exercise',
                      'asset', 'learner_memory', 'cache_entry')),
    entity_id     uuid NOT NULL,
    locale        text NOT NULL DEFAULT 'en' REFERENCES ref.languages (code),
    owner_user_id uuid REFERENCES identity.users (id) ON DELETE CASCADE,
    content_hash  bytea NOT NULL CHECK (octet_length(content_hash) = 32),
    status        text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'indexed', 'failed')),
    embedded_at   timestamptz,
    created_at    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_entity_embeddings UNIQUE (collection_id, entity_type, entity_id, locale)
);
CREATE INDEX ix_entity_embeddings_entity ON vector.entity_embeddings (entity_type, entity_id);
CREATE INDEX ix_entity_embeddings_owner ON vector.entity_embeddings (owner_user_id) WHERE owner_user_id IS NOT NULL;

-- Transactional outbox. Writers enqueue in the same transaction as the source
-- change; a worker drains it with SELECT ... FOR UPDATE SKIP LOCKED and calls
-- Qdrant. Guarantees deletes reach Qdrant even if the API crashes mid-request.
CREATE TABLE vector.sync_outbox (
    id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    collection_id smallint NOT NULL REFERENCES vector.collections (id) ON DELETE CASCADE,
    operation     text NOT NULL CHECK (operation IN ('upsert', 'delete', 'set_payload')),
    point_id      uuid NOT NULL,
    payload       jsonb,
    status        text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'done', 'failed')),
    attempts      smallint NOT NULL DEFAULT 0,
    available_at  timestamptz NOT NULL DEFAULT now(),
    locked_by     text,
    locked_at     timestamptz,
    last_error    text,
    created_at    timestamptz NOT NULL DEFAULT now(),
    processed_at  timestamptz
);
CREATE INDEX ix_sync_outbox_ready ON vector.sync_outbox (available_at, id) WHERE status IN ('pending', 'failed');
CREATE INDEX ix_sync_outbox_done ON vector.sync_outbox (processed_at) WHERE status = 'done';
ALTER TABLE vector.sync_outbox SET (autovacuum_vacuum_scale_factor = 0.02, fillfactor = 80);

CREATE OR REPLACE FUNCTION vector.enqueue_chunk_point_delete() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO vector.sync_outbox (collection_id, operation, point_id)
    VALUES (OLD.collection_id, 'delete', OLD.chunk_id);
    RETURN NULL;
END $$;

CREATE TRIGGER trg_chunk_embeddings_delete
    AFTER DELETE ON vector.chunk_embeddings
    FOR EACH ROW EXECUTE FUNCTION vector.enqueue_chunk_point_delete();

CREATE OR REPLACE FUNCTION vector.enqueue_entity_point_delete() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO vector.sync_outbox (collection_id, operation, point_id)
    VALUES (OLD.collection_id, 'delete', OLD.point_id);
    RETURN NULL;
END $$;

CREATE TRIGGER trg_entity_embeddings_delete
    AFTER DELETE ON vector.entity_embeddings
    FOR EACH ROW EXECUTE FUNCTION vector.enqueue_entity_point_delete();

-- When an asset is archived or unpublished, flip the payload status so
-- retrieval filters (status = 'published') stop returning it immediately.
CREATE OR REPLACE FUNCTION vector.enqueue_asset_status_payload() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO vector.sync_outbox (collection_id, operation, point_id, payload)
    SELECT ce.collection_id, 'set_payload', ce.chunk_id, jsonb_build_object('status', NEW.status)
    FROM knowledge.asset_versions v
    JOIN knowledge.chunks c ON c.asset_version_id = v.id
    JOIN vector.chunk_embeddings ce ON ce.chunk_id = c.id
    WHERE v.asset_id = NEW.id;
    RETURN NULL;
END $$;

CREATE TRIGGER trg_assets_status_payload
    AFTER UPDATE OF status ON knowledge.assets
    FOR EACH ROW WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION vector.enqueue_asset_status_payload();
