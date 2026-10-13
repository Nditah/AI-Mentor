-- =============================================================================
-- 06 chat history
--   conversations      regular table (one row per thread)
--   messages           RANGE (created_at) monthly
--   message_citations  RANGE (message_created_at) — co-partitioned with messages
--   message_feedback   RANGE (message_created_at) — co-partitioned with messages
-- Co-partitioning lets retention drop a month of citations, feedback, and
-- messages together; FKs to a partitioned parent block detaching a partition
-- that still has referencing rows.
--
-- Reading a thread: WHERE conversation_id = $1 AND created_at >= $conv_created_at
-- lets the planner prune every partition older than the conversation.
-- =============================================================================

CREATE TABLE chat.conversations (
    id                uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    user_id           uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    title             text NOT NULL DEFAULT 'New conversation' CHECK (char_length(title) <= 200),
    agent             ref.agent_kind NOT NULL DEFAULT 'tutor',
    teaching_style    ref.teaching_style,
    tutor_personality ref.tutor_personality,
    technical_depth   ref.difficulty_level,
    locale            text NOT NULL DEFAULT 'en' REFERENCES ref.languages (code),
    concept_id        uuid REFERENCES curriculum.concepts (id) ON DELETE SET NULL,
    lesson_id         uuid REFERENCES curriculum.lessons (id) ON DELETE SET NULL,
    asset_id          uuid REFERENCES knowledge.assets (id) ON DELETE SET NULL,
    message_count     integer NOT NULL DEFAULT 0 CHECK (message_count >= 0),
    last_message_at   timestamptz,
    pinned            boolean NOT NULL DEFAULT false,
    archived_at       timestamptz,
    deleted_at        timestamptz,             -- soft delete; purged after 30 days
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now()
) WITH (fillfactor = 80);
CREATE INDEX ix_conversations_user_recent ON chat.conversations (user_id, last_message_at DESC NULLS LAST)
    WHERE deleted_at IS NULL;
CREATE INDEX ix_conversations_purge ON chat.conversations (deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX ix_conversations_concept ON chat.conversations (concept_id) WHERE concept_id IS NOT NULL;

CREATE TABLE chat.messages (
    id                uuid NOT NULL DEFAULT util.uuid_v7(),
    created_at        timestamptz NOT NULL DEFAULT now(),
    conversation_id   uuid NOT NULL REFERENCES chat.conversations (id) ON DELETE CASCADE,
    user_id           uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    role              ref.message_role NOT NULL,
    parent_message_id uuid,               -- regenerations / branches (same conversation)
    content           text NOT NULL CHECK (char_length(content) <= 100000),
    content_format    text NOT NULL DEFAULT 'markdown' CHECK (content_format IN ('markdown', 'plain', 'json')),
    locale            text REFERENCES ref.languages (code),
    agent             ref.agent_kind,
    intent            text,               -- router decision: explain, quiz, plan, code, research, career...
    concept_id        uuid,
    socratic_step     text CHECK (socratic_step IN ('probe', 'hint', 'check', 'explain', 'summarise')),
    grounded          boolean,            -- answer used the curated repository
    model             text,
    prompt_tokens     integer CHECK (prompt_tokens >= 0),
    completion_tokens integer CHECK (completion_tokens >= 0),
    latency_ms        integer CHECK (latency_ms >= 0),
    ttft_ms           integer CHECK (ttft_ms >= 0),
    safety_flags      jsonb,
    tool_calls        jsonb,
    llm_invocation_id uuid,
    edited_at         timestamptz,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);
CREATE INDEX ix_messages_conversation ON chat.messages (conversation_id, created_at);
CREATE INDEX ix_messages_user ON chat.messages (user_id, created_at);
CREATE INDEX ix_messages_concept ON chat.messages (concept_id, created_at) WHERE concept_id IS NOT NULL;

CREATE TABLE chat.message_citations (
    message_id         uuid NOT NULL,
    message_created_at timestamptz NOT NULL,
    rank               smallint NOT NULL CHECK (rank >= 1),
    chunk_id           uuid REFERENCES knowledge.chunks (id) ON DELETE SET NULL,
    asset_id           uuid REFERENCES knowledge.assets (id) ON DELETE SET NULL,
    asset_version_id   uuid REFERENCES knowledge.asset_versions (id) ON DELETE SET NULL,
    citation_label     text NOT NULL,
    retrieval_score    real,
    rerank_score       real,
    quoted_span        text CHECK (char_length(quoted_span) <= 2000),
    PRIMARY KEY (message_id, message_created_at, rank),
    CONSTRAINT fk_message_citations_message FOREIGN KEY (message_id, message_created_at)
        REFERENCES chat.messages (id, created_at) ON DELETE CASCADE
) PARTITION BY RANGE (message_created_at);
CREATE INDEX ix_message_citations_asset ON chat.message_citations (asset_id, message_created_at)
    WHERE asset_id IS NOT NULL;

CREATE TABLE chat.message_feedback (
    message_id         uuid NOT NULL,
    message_created_at timestamptz NOT NULL,
    user_id            uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    rating             smallint NOT NULL CHECK (rating IN (-1, 1)),
    reason             text CHECK (reason IN ('helpful', 'incorrect', 'unclear', 'too_long', 'too_short',
                           'not_grounded', 'unsafe', 'wrong_language', 'other')),
    comment            text CHECK (char_length(comment) <= 2000),
    created_at         timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (message_id, message_created_at, user_id),
    CONSTRAINT fk_message_feedback_message FOREIGN KEY (message_id, message_created_at)
        REFERENCES chat.messages (id, created_at) ON DELETE CASCADE
) PARTITION BY RANGE (message_created_at);
CREATE INDEX ix_message_feedback_negative ON chat.message_feedback (created_at) WHERE rating = -1;

-- Rolling summaries keep long threads inside the model context window.
CREATE TABLE chat.conversation_summaries (
    conversation_id uuid NOT NULL REFERENCES chat.conversations (id) ON DELETE CASCADE,
    version         integer NOT NULL CHECK (version > 0),
    covers_until    timestamptz NOT NULL,
    summary         text NOT NULL,
    token_count     integer NOT NULL CHECK (token_count >= 0),
    model           text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (conversation_id, version)
);

-- Keeps conversations.message_count / last_message_at current.
CREATE OR REPLACE FUNCTION chat.bump_conversation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE chat.conversations
    SET message_count   = message_count + 1,
        last_message_at = greatest(coalesce(last_message_at, NEW.created_at), NEW.created_at)
    WHERE id = NEW.conversation_id;
    RETURN NULL;
END $$;

CREATE TRIGGER trg_messages_bump_conversation
    AFTER INSERT ON chat.messages
    FOR EACH ROW EXECUTE FUNCTION chat.bump_conversation();
