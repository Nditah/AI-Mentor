-- =============================================================================
-- 08 activity tracking
--   sessions         RANGE (started_at)  monthly
--   events           RANGE (received_at) DAILY — highest-volume table
--   llm_invocations  RANGE (created_at)  monthly
--
-- Events are partitioned by server receive time, not client time, so a skewed
-- client clock cannot write into an old or future partition. No foreign keys
-- on the event stream: ingest throughput matters more, names are validated at
-- the API against activity.event_types, and erasure deletes by user_id.
-- PostgreSQL keeps 90 days hot; CDC ships everything to the warehouse.
-- =============================================================================

CREATE TABLE activity.event_types (
    name           text PRIMARY KEY CHECK (name ~ '^[a-z_]+\.[a-z_]+$'),
    category       text NOT NULL CHECK (category IN ('auth', 'onboarding', 'learning', 'assessment', 'coding',
                       'tutor', 'gamification', 'knowledge', 'navigation', 'billing', 'settings', 'research')),
    description    text NOT NULL,
    schema_version smallint NOT NULL DEFAULT 1,
    json_schema    jsonb,
    contains_pii   boolean NOT NULL DEFAULT false,
    is_active      boolean NOT NULL DEFAULT true,
    created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE activity.sessions (
    id            uuid NOT NULL DEFAULT util.uuid_v7(),
    started_at    timestamptz NOT NULL DEFAULT now(),
    user_id       uuid REFERENCES identity.users (id) ON DELETE CASCADE,
    anonymous_id  text,
    ended_at      timestamptz,
    last_event_at timestamptz,
    platform      text NOT NULL CHECK (platform IN ('web', 'ios', 'android', 'api')),
    app_version   text,
    device_type   text CHECK (device_type IN ('desktop', 'mobile', 'tablet', 'other')),
    os            text,
    browser       text,
    locale        text,
    country_code  char(2),                 -- geo-IP, not the profile country
    ip_hmac       bytea,                   -- keyed hash; raw IPs are never stored
    utm           jsonb,
    event_count   integer NOT NULL DEFAULT 0,
    PRIMARY KEY (id, started_at),
    CONSTRAINT ck_sessions_identity CHECK (user_id IS NOT NULL OR anonymous_id IS NOT NULL)
) PARTITION BY RANGE (started_at);
CREATE INDEX ix_sessions_user ON activity.sessions (user_id, started_at DESC);

CREATE TABLE activity.events (
    id            uuid NOT NULL,           -- client-generated for de-duplication
    received_at   timestamptz NOT NULL DEFAULT now(),
    occurred_at   timestamptz NOT NULL,
    user_id       uuid,
    anonymous_id  text,
    session_id    uuid,
    event_name    text NOT NULL,
    event_version smallint NOT NULL DEFAULT 1,
    entity_type   text,
    entity_id     uuid,
    concept_id    uuid,
    locale        text,
    platform      text,
    properties    jsonb NOT NULL DEFAULT '{}' CHECK (octet_length(properties::text) <= 16384),
    PRIMARY KEY (id, received_at)
) PARTITION BY RANGE (received_at);
CREATE INDEX ix_events_user ON activity.events (user_id, received_at) WHERE user_id IS NOT NULL;
CREATE INDEX ix_events_name ON activity.events (event_name, received_at);
CREATE INDEX ix_events_entity ON activity.events (entity_type, entity_id) WHERE entity_id IS NOT NULL;

-- Cost, latency, and reliability of every model call (chat, quiz generation,
-- embeddings, reviews). Prompts and completions are NOT stored here; they go
-- to Langfuse under its own retention, linked by trace_id.
CREATE TABLE activity.llm_invocations (
    id                uuid NOT NULL DEFAULT util.uuid_v7(),
    created_at        timestamptz NOT NULL DEFAULT now(),
    user_id           uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    agent             ref.agent_kind NOT NULL,
    operation         text NOT NULL CHECK (operation IN ('chat', 'quiz_generate', 'grade', 'code_review', 'embed',
                          'summarise', 'translate', 'plan', 'recommend', 'artifact_generate', 'moderate')),
    provider          text NOT NULL,
    model             text NOT NULL,
    conversation_id   uuid,
    message_id        uuid,
    prompt_version    text,
    prompt_tokens     integer NOT NULL DEFAULT 0 CHECK (prompt_tokens >= 0),
    completion_tokens integer NOT NULL DEFAULT 0 CHECK (completion_tokens >= 0),
    cached_tokens     integer NOT NULL DEFAULT 0 CHECK (cached_tokens >= 0),
    cost_usd          numeric(12,6) NOT NULL DEFAULT 0 CHECK (cost_usd >= 0),
    latency_ms        integer CHECK (latency_ms >= 0),
    ttft_ms           integer CHECK (ttft_ms >= 0),
    status            text NOT NULL CHECK (status IN ('ok', 'error', 'timeout', 'filtered', 'fallback')),
    error_code        text,
    trace_id          text,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);
CREATE INDEX ix_llm_invocations_user ON activity.llm_invocations (user_id, created_at) WHERE user_id IS NOT NULL;
CREATE INDEX ix_llm_invocations_model ON activity.llm_invocations (provider, model, created_at);
CREATE INDEX ix_llm_invocations_brin ON activity.llm_invocations USING brin (created_at);
