-- =============================================================================
-- 02 curriculum: taxonomy, concept graph, learning paths, lessons, question bank
-- Learner progress always references language-neutral ids (lesson, concept,
-- question), so switching language never forks a learner's record.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Taxonomy (hierarchical). `path` is a materialised ltree such as
-- artificial_intelligence.reinforcement_learning.mdp, maintained by trigger.
-- -----------------------------------------------------------------------------

CREATE TABLE curriculum.taxonomy_nodes (
    id          uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    parent_id   uuid REFERENCES curriculum.taxonomy_nodes (id) ON DELETE RESTRICT,
    slug        text NOT NULL CHECK (slug ~ '^[a-z0-9_]{1,80}$'),
    name        text NOT NULL,
    description text NOT NULL DEFAULT '',
    path        ltree NOT NULL,
    depth       integer GENERATED ALWAYS AS (nlevel(path)) STORED,
    position    integer NOT NULL DEFAULT 0,
    status      ref.content_status NOT NULL DEFAULT 'published',
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_taxonomy_sibling_slug UNIQUE (parent_id, slug),
    CONSTRAINT ck_taxonomy_not_self_parent CHECK (parent_id IS DISTINCT FROM id)
);
CREATE UNIQUE INDEX ux_taxonomy_path ON curriculum.taxonomy_nodes (path);
CREATE INDEX ix_taxonomy_path_gist ON curriculum.taxonomy_nodes USING gist (path);
CREATE INDEX ix_taxonomy_parent ON curriculum.taxonomy_nodes (parent_id, position);

CREATE OR REPLACE FUNCTION curriculum.taxonomy_set_path() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    v_parent_path ltree;
BEGIN
    IF NEW.parent_id IS NULL THEN
        NEW.path := text2ltree(NEW.slug);
    ELSE
        SELECT path INTO v_parent_path FROM curriculum.taxonomy_nodes WHERE id = NEW.parent_id;
        IF v_parent_path IS NULL THEN
            RAISE EXCEPTION 'parent % not found', NEW.parent_id;
        END IF;
        IF TG_OP = 'UPDATE' AND v_parent_path <@ OLD.path THEN
            RAISE EXCEPTION 'cannot move taxonomy node % under its own descendant', NEW.id
                USING ERRCODE = 'check_violation';
        END IF;
        NEW.path := v_parent_path || text2ltree(NEW.slug);
    END IF;
    RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION curriculum.taxonomy_cascade_path() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    -- Touching children re-fires taxonomy_set_path, which cascades level by level.
    UPDATE curriculum.taxonomy_nodes SET slug = slug WHERE parent_id = NEW.id;
    RETURN NULL;
END $$;

CREATE TRIGGER trg_taxonomy_set_path
    BEFORE INSERT OR UPDATE OF parent_id, slug ON curriculum.taxonomy_nodes
    FOR EACH ROW EXECUTE FUNCTION curriculum.taxonomy_set_path();
CREATE TRIGGER trg_taxonomy_cascade_path
    AFTER UPDATE OF parent_id, slug ON curriculum.taxonomy_nodes
    FOR EACH ROW WHEN (OLD.path IS DISTINCT FROM NEW.path)
    EXECUTE FUNCTION curriculum.taxonomy_cascade_path();

-- -----------------------------------------------------------------------------
-- Concepts and the knowledge graph
-- -----------------------------------------------------------------------------

CREATE TABLE curriculum.concepts (
    id                uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    slug              text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9_]{1,80}$'),
    taxonomy_node_id  uuid NOT NULL REFERENCES curriculum.taxonomy_nodes (id) ON DELETE RESTRICT,
    name              text NOT NULL,
    summary           text NOT NULL DEFAULT '',
    difficulty        ref.difficulty_level NOT NULL,
    base_locale       text NOT NULL DEFAULT 'en' REFERENCES ref.languages (code),
    estimated_minutes integer NOT NULL DEFAULT 30 CHECK (estimated_minutes > 0),
    status            ref.content_status NOT NULL DEFAULT 'draft',
    created_by        uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now(),
    search            tsvector GENERATED ALWAYS AS (
                          setweight(to_tsvector('english', name), 'A') ||
                          setweight(to_tsvector('english', summary), 'B')) STORED
);
CREATE INDEX ix_concepts_taxonomy ON curriculum.concepts (taxonomy_node_id);
CREATE INDEX ix_concepts_status_difficulty ON curriculum.concepts (status, difficulty);
CREATE INDEX ix_concepts_search ON curriculum.concepts USING gin (search);
CREATE INDEX ix_concepts_name_trgm ON curriculum.concepts USING gin (name gin_trgm_ops);

CREATE TABLE curriculum.concept_translations (
    concept_id         uuid NOT NULL REFERENCES curriculum.concepts (id) ON DELETE CASCADE,
    locale             text NOT NULL REFERENCES ref.languages (code),
    name               text NOT NULL,
    summary            text NOT NULL DEFAULT '',
    translation_source text NOT NULL DEFAULT 'machine' CHECK (translation_source IN ('human', 'machine')),
    reviewed_by        uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    reviewed_at        timestamptz,
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (concept_id, locale)
);

-- For 'prerequisite': from_concept REQUIRES to_concept (q_learning -> mdp).
CREATE TABLE curriculum.concept_relations (
    from_concept_id uuid NOT NULL REFERENCES curriculum.concepts (id) ON DELETE CASCADE,
    to_concept_id   uuid NOT NULL REFERENCES curriculum.concepts (id) ON DELETE CASCADE,
    relation_type   ref.concept_relation NOT NULL,
    weight          numeric(3,2) NOT NULL DEFAULT 1.00 CHECK (weight BETWEEN 0 AND 1),
    created_by      uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (from_concept_id, to_concept_id, relation_type),
    CONSTRAINT ck_concept_relation_not_self CHECK (from_concept_id <> to_concept_id)
);
CREATE INDEX ix_concept_relations_to ON curriculum.concept_relations (to_concept_id, relation_type);

CREATE OR REPLACE FUNCTION curriculum.prevent_prerequisite_cycle() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.relation_type <> 'prerequisite' THEN
        RETURN NEW;
    END IF;
    -- Serialise prerequisite edits so two concurrent inserts cannot form a cycle.
    PERFORM pg_advisory_xact_lock(hashtext('curriculum.concept_relations.prerequisite'));
    IF EXISTS (
        WITH RECURSIVE reachable(concept_id) AS (
            SELECT NEW.to_concept_id
            UNION
            SELECT r.to_concept_id
            FROM curriculum.concept_relations r
            JOIN reachable ON r.from_concept_id = reachable.concept_id
            WHERE r.relation_type = 'prerequisite'
        )
        SELECT 1 FROM reachable WHERE concept_id = NEW.from_concept_id
    ) THEN
        RAISE EXCEPTION 'prerequisite cycle: % -> %', NEW.from_concept_id, NEW.to_concept_id
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER trg_concept_relations_acyclic
    BEFORE INSERT OR UPDATE ON curriculum.concept_relations
    FOR EACH ROW EXECUTE FUNCTION curriculum.prevent_prerequisite_cycle();

-- -----------------------------------------------------------------------------
-- Courses, modules, lessons. Positions use DEFERRABLE unique constraints so a
-- drag-and-drop reorder can swap positions inside one transaction.
-- -----------------------------------------------------------------------------

CREATE TABLE curriculum.courses (
    id          uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    slug        text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9_-]{1,80}$'),
    title       text NOT NULL,
    description text NOT NULL DEFAULT '',
    difficulty  ref.difficulty_level NOT NULL DEFAULT 'beginner',
    base_locale text NOT NULL DEFAULT 'en' REFERENCES ref.languages (code),
    status      ref.content_status NOT NULL DEFAULT 'draft',
    published_at timestamptz,
    created_by  uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE curriculum.modules (
    id          uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    course_id   uuid NOT NULL REFERENCES curriculum.courses (id) ON DELETE CASCADE,
    title       text NOT NULL,
    description text NOT NULL DEFAULT '',
    position    integer NOT NULL CHECK (position >= 0),
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_modules_position UNIQUE (course_id, position) DEFERRABLE INITIALLY IMMEDIATE
);

CREATE TABLE curriculum.lessons (
    id                 uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    module_id          uuid NOT NULL REFERENCES curriculum.modules (id) ON DELETE CASCADE,
    primary_concept_id uuid REFERENCES curriculum.concepts (id) ON DELETE SET NULL,
    slug               text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9_-]{1,80}$'),
    position           integer NOT NULL CHECK (position >= 0),
    difficulty         ref.difficulty_level NOT NULL DEFAULT 'beginner',
    estimated_minutes  integer NOT NULL DEFAULT 25 CHECK (estimated_minutes BETWEEN 1 AND 600),
    status             ref.content_status NOT NULL DEFAULT 'draft',
    created_by         uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_lessons_position UNIQUE (module_id, position) DEFERRABLE INITIALLY IMMEDIATE
);
CREATE INDEX ix_lessons_concept ON curriculum.lessons (primary_concept_id);

-- Lesson body per (locale, teaching style, version). One published row per
-- (lesson, locale, style). 'mixed' is the fallback style for every lesson.
CREATE TABLE curriculum.lesson_contents (
    id             uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    lesson_id      uuid NOT NULL REFERENCES curriculum.lessons (id) ON DELETE CASCADE,
    locale         text NOT NULL REFERENCES ref.languages (code),
    teaching_style ref.teaching_style NOT NULL DEFAULT 'mixed',
    version        integer NOT NULL DEFAULT 1 CHECK (version > 0),
    title          text NOT NULL,
    body_md        text NOT NULL,
    source         text NOT NULL DEFAULT 'authored' CHECK (source IN ('authored', 'generated', 'machine_translated')),
    status         ref.content_status NOT NULL DEFAULT 'draft',
    reviewed_by    uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    published_at   timestamptz,
    created_by     uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_lesson_contents_version UNIQUE (lesson_id, locale, teaching_style, version),
    CONSTRAINT ck_lesson_contents_size CHECK (octet_length(body_md) <= 1048576)
);
CREATE UNIQUE INDEX ux_lesson_contents_published ON curriculum.lesson_contents (lesson_id, locale, teaching_style)
    WHERE status = 'published';

-- -----------------------------------------------------------------------------
-- Learning paths
-- -----------------------------------------------------------------------------

CREATE TABLE curriculum.learning_paths (
    id              uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    slug            text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9_-]{1,80}$'),
    title           text NOT NULL,
    description     text NOT NULL DEFAULT '',
    level           ref.difficulty_level NOT NULL DEFAULT 'beginner',
    target_persona  ref.learner_persona,
    estimated_hours integer CHECK (estimated_hours > 0),
    cover_image_url text,
    base_locale     text NOT NULL DEFAULT 'en' REFERENCES ref.languages (code),
    status          ref.content_status NOT NULL DEFAULT 'draft',
    version         integer NOT NULL DEFAULT 1,
    published_at    timestamptz,
    created_by      uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE curriculum.learning_path_translations (
    path_id     uuid NOT NULL REFERENCES curriculum.learning_paths (id) ON DELETE CASCADE,
    locale      text NOT NULL REFERENCES ref.languages (code),
    title       text NOT NULL,
    description text NOT NULL DEFAULT '',
    updated_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (path_id, locale)
);

-- -----------------------------------------------------------------------------
-- Question bank and assessments
-- -----------------------------------------------------------------------------

CREATE TABLE curriculum.questions (
    id                    uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    concept_id            uuid NOT NULL REFERENCES curriculum.concepts (id) ON DELETE RESTRICT,
    kind                  ref.question_kind NOT NULL,
    difficulty            ref.difficulty_level NOT NULL,
    base_locale           text NOT NULL DEFAULT 'en' REFERENCES ref.languages (code),
    prompt                text NOT NULL,
    options               jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(options) = 'array'),
    answer_key            jsonb NOT NULL CHECK (jsonb_typeof(answer_key) = 'object'),
    explanation           text NOT NULL DEFAULT '',
    source                text NOT NULL DEFAULT 'authored' CHECK (source IN ('authored', 'generated', 'imported')),
    generated_artifact_id uuid,              -- FK added in 03_knowledge.sql
    irt_difficulty        numeric(6,3),      -- item response theory b-parameter, fitted offline
    irt_discrimination    numeric(6,3),      -- a-parameter
    status                ref.content_status NOT NULL DEFAULT 'draft',
    created_by            uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_questions_options CHECK (
        kind NOT IN ('mcq', 'multi_select') OR jsonb_array_length(options) >= 2)
);
CREATE INDEX ix_questions_selection ON curriculum.questions (concept_id, difficulty, kind) WHERE status = 'published';

CREATE TABLE curriculum.question_translations (
    question_id uuid NOT NULL REFERENCES curriculum.questions (id) ON DELETE CASCADE,
    locale      text NOT NULL REFERENCES ref.languages (code),
    prompt      text NOT NULL,
    options     jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(options) = 'array'),
    explanation text NOT NULL DEFAULT '',
    updated_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (question_id, locale)
);

CREATE TABLE curriculum.assessments (
    id                 uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    slug               text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9_-]{1,80}$'),
    title              text NOT NULL,
    kind               text NOT NULL CHECK (kind IN ('quiz', 'checkpoint', 'exam', 'placement')),
    concept_id         uuid REFERENCES curriculum.concepts (id) ON DELETE SET NULL,
    module_id          uuid REFERENCES curriculum.modules (id) ON DELETE SET NULL,
    difficulty         ref.difficulty_level NOT NULL,
    pass_score_pct     numeric(5,2) NOT NULL DEFAULT 70 CHECK (pass_score_pct BETWEEN 0 AND 100),
    time_limit_seconds integer CHECK (time_limit_seconds > 0),
    status             ref.content_status NOT NULL DEFAULT 'draft',
    created_by         uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE curriculum.assessment_questions (
    assessment_id uuid NOT NULL REFERENCES curriculum.assessments (id) ON DELETE CASCADE,
    question_id   uuid NOT NULL REFERENCES curriculum.questions (id) ON DELETE RESTRICT,
    position      integer NOT NULL CHECK (position >= 0),
    points        numeric(6,2) NOT NULL DEFAULT 1 CHECK (points > 0),
    PRIMARY KEY (assessment_id, question_id),
    CONSTRAINT uq_assessment_questions_position UNIQUE (assessment_id, position) DEFERRABLE INITIALLY IMMEDIATE
);
CREATE INDEX ix_assessment_questions_question ON curriculum.assessment_questions (question_id);

CREATE TABLE curriculum.coding_exercises (
    id              uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    slug            text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9_-]{1,80}$'),
    kind            text NOT NULL DEFAULT 'exercise' CHECK (kind IN ('exercise', 'project', 'debugging', 'notebook', 'simulation')),
    title           text NOT NULL,
    brief_md        text NOT NULL DEFAULT '',
    language        text NOT NULL DEFAULT 'python' CHECK (language IN ('python')),
    difficulty      ref.difficulty_level NOT NULL DEFAULT 'intermediate',
    concept_id      uuid REFERENCES curriculum.concepts (id) ON DELETE SET NULL,
    starter_code    text NOT NULL DEFAULT '',
    reference_solution text,                -- never returned to learners
    test_spec       jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(test_spec) = 'object'),
    time_limit_ms   integer NOT NULL DEFAULT 5000 CHECK (time_limit_ms BETWEEN 100 AND 60000),
    memory_limit_mb integer NOT NULL DEFAULT 256 CHECK (memory_limit_mb BETWEEN 16 AND 4096),
    status          ref.content_status NOT NULL DEFAULT 'draft',
    created_by      uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_coding_exercises_concept ON curriculum.coding_exercises (concept_id) WHERE status = 'published';

-- Ordered path contents. Exactly one target per item.
CREATE TABLE curriculum.learning_path_items (
    id            uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    path_id       uuid NOT NULL REFERENCES curriculum.learning_paths (id) ON DELETE CASCADE,
    position      integer NOT NULL CHECK (position >= 0),
    course_id     uuid REFERENCES curriculum.courses (id) ON DELETE RESTRICT,
    module_id     uuid REFERENCES curriculum.modules (id) ON DELETE RESTRICT,
    lesson_id     uuid REFERENCES curriculum.lessons (id) ON DELETE RESTRICT,
    concept_id    uuid REFERENCES curriculum.concepts (id) ON DELETE RESTRICT,
    assessment_id uuid REFERENCES curriculum.assessments (id) ON DELETE RESTRICT,
    exercise_id   uuid REFERENCES curriculum.coding_exercises (id) ON DELETE RESTRICT,
    asset_id      uuid,                    -- FK added in 03_knowledge.sql
    is_optional   boolean NOT NULL DEFAULT false,
    unlock_rule   jsonb CHECK (unlock_rule IS NULL OR jsonb_typeof(unlock_rule) = 'object'),
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_path_items_position UNIQUE (path_id, position) DEFERRABLE INITIALLY IMMEDIATE,
    CONSTRAINT ck_path_items_one_target CHECK (
        num_nonnulls(course_id, module_id, lesson_id, concept_id, assessment_id, exercise_id, asset_id) = 1)
);
CREATE INDEX ix_path_items_lesson ON curriculum.learning_path_items (lesson_id) WHERE lesson_id IS NOT NULL;
CREATE INDEX ix_path_items_concept ON curriculum.learning_path_items (concept_id) WHERE concept_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Cross-schema foreign keys deferred from 01_identity.sql
-- -----------------------------------------------------------------------------

ALTER TABLE identity.onboarding_assessments
    ADD CONSTRAINT fk_onboarding_recommended_path
    FOREIGN KEY (recommended_path_id) REFERENCES curriculum.learning_paths (id) ON DELETE SET NULL;

ALTER TABLE identity.user_interests
    ADD CONSTRAINT fk_user_interests_taxonomy
    FOREIGN KEY (taxonomy_node_id) REFERENCES curriculum.taxonomy_nodes (id) ON DELETE CASCADE;
