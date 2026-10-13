-- =============================================================================
-- 03 knowledge repository
-- Curated assets (admin library) and personal assets (a learner's own papers)
-- share one pipeline: file -> asset -> version -> ingestion -> chunks -> vectors.
-- Scope is enforced three ways: the `scope` column, RLS (11_security.sql), and
-- separate Qdrant collections (04_vector.sql).
-- =============================================================================

CREATE TABLE knowledge.files (
    id                uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    storage_provider  text NOT NULL CHECK (storage_provider IN ('azure_blob', 's3', 'gcs', 'external_url')),
    storage_uri       text NOT NULL UNIQUE,
    mime_type         text NOT NULL,
    byte_size         bigint NOT NULL CHECK (byte_size >= 0),
    sha256            bytea NOT NULL CHECK (octet_length(sha256) = 32),
    original_filename text,
    uploaded_by       uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    malware_scan      text NOT NULL DEFAULT 'pending' CHECK (malware_scan IN ('pending', 'clean', 'infected', 'failed')),
    created_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_files_sha256 ON knowledge.files (sha256);

CREATE TABLE knowledge.assets (
    id                 uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    scope              ref.asset_scope NOT NULL,
    owner_user_id      uuid REFERENCES identity.users (id) ON DELETE CASCADE,
    slug               text UNIQUE CHECK (slug ~ '^[a-z0-9_-]{1,120}$'),
    kind               ref.asset_kind NOT NULL,
    title              text NOT NULL CHECK (char_length(title) BETWEEN 1 AND 500),
    description        text NOT NULL DEFAULT '',
    authors            text[] NOT NULL DEFAULT '{}',
    publisher          text,
    source_url         text,
    doi                text CHECK (doi ~ '^10\.\d{4,9}/\S+$'),
    publication_date   date,
    license            text,
    base_locale        text NOT NULL DEFAULT 'en' REFERENCES ref.languages (code),
    difficulty         ref.difficulty_level,
    estimated_minutes  integer CHECK (estimated_minutes > 0),
    status             ref.content_status NOT NULL DEFAULT 'draft',
    current_version_id uuid,          -- FK below (circular with asset_versions)
    published_at       timestamptz,
    archived_at        timestamptz,
    created_by         uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now(),
    search             tsvector GENERATED ALWAYS AS (
                           setweight(to_tsvector('english', title), 'A') ||
                           setweight(to_tsvector('english', description), 'B')) STORED,
    CONSTRAINT ck_assets_scope_owner CHECK ((scope = 'personal') = (owner_user_id IS NOT NULL)),
    CONSTRAINT ck_assets_personal_no_slug CHECK (scope = 'curated' OR slug IS NULL)
);
CREATE INDEX ix_assets_catalog ON knowledge.assets (status, kind, difficulty) WHERE scope = 'curated';
CREATE INDEX ix_assets_owner ON knowledge.assets (owner_user_id, created_at DESC) WHERE scope = 'personal';
CREATE INDEX ix_assets_search ON knowledge.assets USING gin (search);
CREATE INDEX ix_assets_title_trgm ON knowledge.assets USING gin (title gin_trgm_ops);
CREATE UNIQUE INDEX ux_assets_doi ON knowledge.assets (doi) WHERE scope = 'curated' AND doi IS NOT NULL;

CREATE TABLE knowledge.asset_versions (
    id             uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    asset_id       uuid NOT NULL REFERENCES knowledge.assets (id) ON DELETE CASCADE,
    version_no     integer NOT NULL CHECK (version_no > 0),
    file_id        uuid REFERENCES knowledge.files (id) ON DELETE RESTRICT,
    source_url     text,
    content_hash   bytea CHECK (octet_length(content_hash) = 32),
    metadata       jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(metadata) = 'object'),
    change_summary text NOT NULL DEFAULT '',
    status         ref.content_status NOT NULL DEFAULT 'draft',
    editor_id      uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    approved_by    uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    approved_at    timestamptz,
    published_at   timestamptz,
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_asset_versions_no UNIQUE (asset_id, version_no),
    CONSTRAINT ck_asset_versions_source CHECK (file_id IS NOT NULL OR source_url IS NOT NULL)
);
CREATE UNIQUE INDEX ux_asset_versions_one_published ON knowledge.asset_versions (asset_id)
    WHERE status = 'published';
CREATE INDEX ix_asset_versions_review_queue ON knowledge.asset_versions (status, updated_at)
    WHERE status IN ('review', 'approved');

ALTER TABLE knowledge.assets
    ADD CONSTRAINT fk_assets_current_version
    FOREIGN KEY (current_version_id) REFERENCES knowledge.asset_versions (id)
    ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

-- Approval workflow: draft -> review -> approved -> published -> archived.
-- Every transition is logged. The API may pass a reviewer comment with
-- SET LOCAL app.workflow_comment = '...'.
CREATE TABLE knowledge.workflow_transitions (
    id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    asset_version_id uuid NOT NULL REFERENCES knowledge.asset_versions (id) ON DELETE CASCADE,
    from_status      ref.content_status,
    to_status        ref.content_status NOT NULL,
    actor_id         uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    comment          text,
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_workflow_transitions_version ON knowledge.workflow_transitions (asset_version_id, created_at);

CREATE OR REPLACE FUNCTION knowledge.enforce_version_workflow() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    v_allowed boolean;
BEGIN
    IF TG_OP = 'UPDATE' AND NEW.status IS NOT DISTINCT FROM OLD.status THEN
        RETURN NEW;
    END IF;

    -- Curated content must enter as a draft so it cannot skip review.
    -- Personal uploads are only visible to their owner and may start published.
    IF TG_OP = 'INSERT' AND NEW.status <> 'draft' AND NOT EXISTS (
        SELECT 1 FROM knowledge.assets WHERE id = NEW.asset_id AND scope = 'personal'
    ) THEN
        RAISE EXCEPTION 'curated asset versions must be created as draft'
            USING ERRCODE = 'check_violation';
    END IF;

    IF TG_OP = 'UPDATE' THEN
        v_allowed := (OLD.status, NEW.status) IN (
            ('draft', 'review'), ('review', 'draft'), ('review', 'approved'),
            ('approved', 'draft'), ('approved', 'published'),
            ('published', 'archived'), ('archived', 'draft'));
        IF NOT v_allowed THEN
            RAISE EXCEPTION 'invalid workflow transition % -> % for asset version %', OLD.status, NEW.status, NEW.id
                USING ERRCODE = 'check_violation';
        END IF;
    END IF;

    IF NEW.status = 'approved' THEN
        NEW.approved_at := coalesce(NEW.approved_at, now());
        NEW.approved_by := coalesce(NEW.approved_by, util.current_user_id());
    ELSIF NEW.status = 'published' THEN
        NEW.published_at := coalesce(NEW.published_at, now());
    END IF;

    IF TG_OP = 'UPDATE' THEN
        INSERT INTO knowledge.workflow_transitions (asset_version_id, from_status, to_status, actor_id, comment)
        VALUES (NEW.id, OLD.status, NEW.status,
                util.current_user_id(), nullif(current_setting('app.workflow_comment', true), ''));
    END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER trg_asset_versions_workflow
    BEFORE INSERT OR UPDATE OF status ON knowledge.asset_versions
    FOR EACH ROW EXECUTE FUNCTION knowledge.enforce_version_workflow();

-- The initial state is logged after insert, once the row exists for the FK.

CREATE OR REPLACE FUNCTION knowledge.log_version_created() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO knowledge.workflow_transitions (asset_version_id, from_status, to_status, actor_id)
    VALUES (NEW.id, NULL, NEW.status, util.current_user_id());
    RETURN NULL;
END $$;

CREATE TRIGGER trg_asset_versions_created
    AFTER INSERT ON knowledge.asset_versions
    FOR EACH ROW EXECUTE FUNCTION knowledge.log_version_created();

CREATE TABLE knowledge.tags (
    id         integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    slug       text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9_-]{1,60}$'),
    name       text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE knowledge.asset_tags (
    asset_id uuid    NOT NULL REFERENCES knowledge.assets (id) ON DELETE CASCADE,
    tag_id   integer NOT NULL REFERENCES knowledge.tags (id) ON DELETE CASCADE,
    PRIMARY KEY (asset_id, tag_id)
);
CREATE INDEX ix_asset_tags_tag ON knowledge.asset_tags (tag_id);

CREATE TABLE knowledge.asset_concepts (
    asset_id   uuid NOT NULL REFERENCES knowledge.assets (id) ON DELETE CASCADE,
    concept_id uuid NOT NULL REFERENCES curriculum.concepts (id) ON DELETE CASCADE,
    relevance  numeric(3,2) NOT NULL DEFAULT 1.00 CHECK (relevance BETWEEN 0 AND 1),
    is_primary boolean NOT NULL DEFAULT false,
    source     text NOT NULL DEFAULT 'manual' CHECK (source IN ('manual', 'auto')),
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (asset_id, concept_id)
);
CREATE INDEX ix_asset_concepts_concept ON knowledge.asset_concepts (concept_id, relevance DESC);

CREATE TABLE knowledge.learning_objectives (
    id               uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    asset_version_id uuid NOT NULL REFERENCES knowledge.asset_versions (id) ON DELETE CASCADE,
    position         smallint NOT NULL CHECK (position >= 0),
    objective        text NOT NULL,
    concept_id       uuid REFERENCES curriculum.concepts (id) ON DELETE SET NULL,
    CONSTRAINT uq_learning_objectives_position UNIQUE (asset_version_id, position)
);

-- RAG pipeline: parse -> extract_metadata -> chunk -> embed -> index -> link.
CREATE TABLE knowledge.ingestion_jobs (
    id               uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    asset_version_id uuid NOT NULL REFERENCES knowledge.asset_versions (id) ON DELETE CASCADE,
    stage            ref.ingestion_stage NOT NULL,
    status           ref.job_status NOT NULL DEFAULT 'queued',
    attempt          smallint NOT NULL DEFAULT 1 CHECK (attempt BETWEEN 1 AND 20),
    worker_id        text,
    error            text,
    metrics          jsonb NOT NULL DEFAULT '{}',
    queued_at        timestamptz NOT NULL DEFAULT now(),
    started_at       timestamptz,
    finished_at      timestamptz,
    CONSTRAINT ck_ingestion_timing CHECK (finished_at IS NULL OR started_at IS NULL OR finished_at >= started_at)
);
CREATE INDEX ix_ingestion_jobs_queue ON knowledge.ingestion_jobs (queued_at) WHERE status IN ('queued', 'running');
CREATE INDEX ix_ingestion_jobs_version ON knowledge.ingestion_jobs (asset_version_id, stage);

-- Text chunks. Vectors live in Qdrant (point id = chunk id). The tsvector
-- powers lexical / hybrid retrieval and the fallback when Qdrant is down.
CREATE TABLE knowledge.chunks (
    id               uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    asset_version_id uuid NOT NULL REFERENCES knowledge.asset_versions (id) ON DELETE CASCADE,
    owner_user_id    uuid,       -- copied from the asset by trigger; NULL for curated content (used by RLS)
    ordinal          integer NOT NULL CHECK (ordinal >= 0),
    content          text NOT NULL,
    token_count      integer NOT NULL CHECK (token_count >= 0),
    content_hash     bytea NOT NULL CHECK (octet_length(content_hash) = 32),
    locale           text NOT NULL DEFAULT 'en' REFERENCES ref.languages (code),
    page_start       integer,
    page_end         integer,
    section_path     text[] NOT NULL DEFAULT '{}',
    citation_label   text NOT NULL,
    created_at       timestamptz NOT NULL DEFAULT now(),
    content_tsv      tsvector GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED,
    CONSTRAINT uq_chunks_ordinal UNIQUE (asset_version_id, ordinal),
    CONSTRAINT ck_chunks_pages CHECK (page_end IS NULL OR page_start IS NULL OR page_end >= page_start)
);
CREATE INDEX ix_chunks_tsv ON knowledge.chunks USING gin (content_tsv);
CREATE INDEX ix_chunks_hash ON knowledge.chunks (content_hash);
CREATE INDEX ix_chunks_owner ON knowledge.chunks (owner_user_id) WHERE owner_user_id IS NOT NULL;

CREATE OR REPLACE FUNCTION knowledge.chunks_fill_owner() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    SELECT a.owner_user_id INTO NEW.owner_user_id
    FROM knowledge.asset_versions v
    JOIN knowledge.assets a ON a.id = v.asset_id
    WHERE v.id = NEW.asset_version_id;
    RETURN NEW;
END $$;

CREATE TRIGGER trg_chunks_fill_owner
    BEFORE INSERT ON knowledge.chunks
    FOR EACH ROW EXECUTE FUNCTION knowledge.chunks_fill_owner();

-- AI-generated material awaiting review (lesson notes, flashcards, quizzes...).
CREATE TABLE knowledge.generated_artifacts (
    id                      uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    source_asset_version_id uuid REFERENCES knowledge.asset_versions (id) ON DELETE SET NULL,
    concept_id              uuid REFERENCES curriculum.concepts (id) ON DELETE SET NULL,
    kind                    ref.artifact_kind NOT NULL,
    title                   text NOT NULL,
    locale                  text NOT NULL DEFAULT 'en' REFERENCES ref.languages (code),
    payload                 jsonb NOT NULL,
    status                  ref.content_status NOT NULL DEFAULT 'draft',
    model                   text NOT NULL,
    prompt_version          text NOT NULL,
    llm_invocation_id       uuid,     -- activity.llm_invocations (partitioned; no FK)
    reviewed_by             uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    reviewed_at             timestamptz,
    published_entity_type   text CHECK (published_entity_type IN
                                ('lesson_content', 'question', 'assessment', 'coding_exercise', 'flashcard_deck')),
    published_entity_id     uuid,
    created_by              uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    created_at              timestamptz NOT NULL DEFAULT now(),
    updated_at              timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_artifacts_published_ref CHECK ((published_entity_type IS NULL) = (published_entity_id IS NULL))
);
CREATE INDEX ix_artifacts_review_queue ON knowledge.generated_artifacts (status, kind, created_at)
    WHERE status IN ('draft', 'review');
CREATE INDEX ix_artifacts_source ON knowledge.generated_artifacts (source_asset_version_id);

-- Research assistant output on a learner's own document (or a curated paper).
CREATE TABLE knowledge.document_analyses (
    id               uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    asset_version_id uuid NOT NULL REFERENCES knowledge.asset_versions (id) ON DELETE CASCADE,
    user_id          uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    kind             text NOT NULL CHECK (kind IN ('summary', 'equations', 'research_gaps', 'methodology_critique',
                         'literature_review', 'reviewer_simulation', 'citations', 'experimental_design')),
    result_md        text NOT NULL,
    result           jsonb NOT NULL DEFAULT '{}',
    model            text NOT NULL,
    llm_invocation_id uuid,
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_document_analyses_user ON knowledge.document_analyses (user_id, created_at DESC);
CREATE INDEX ix_document_analyses_version ON knowledge.document_analyses (asset_version_id, kind);

-- -----------------------------------------------------------------------------
-- Cross-schema foreign keys deferred from 02_curriculum.sql
-- -----------------------------------------------------------------------------

ALTER TABLE curriculum.learning_path_items
    ADD CONSTRAINT fk_path_items_asset
    FOREIGN KEY (asset_id) REFERENCES knowledge.assets (id) ON DELETE RESTRICT;

ALTER TABLE curriculum.questions
    ADD CONSTRAINT fk_questions_generated_artifact
    FOREIGN KEY (generated_artifact_id) REFERENCES knowledge.generated_artifacts (id) ON DELETE SET NULL;
