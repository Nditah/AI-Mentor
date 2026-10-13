-- =============================================================================
-- 09 learning analytics
-- A small star schema inside PostgreSQL powers product dashboards, learner
-- reports, and the admin analytics page. Heavy ad-hoc analysis runs in the
-- warehouse (CDC from a read replica), not here.
--
-- Rollups are built incrementally by jobs that track analytics.etl_watermarks.
-- Fact tables carry user_id so erasure can delete a learner's rows; aggregates
-- carry no user identifiers and are kept indefinitely.
-- =============================================================================

CREATE TABLE analytics.dim_date (
    date_key     integer PRIMARY KEY,           -- yyyymmdd
    full_date    date NOT NULL UNIQUE,
    year         smallint NOT NULL,
    quarter      smallint NOT NULL,
    month        smallint NOT NULL,
    month_name   text NOT NULL,
    iso_year     smallint NOT NULL,
    iso_week     smallint NOT NULL,
    day_of_month smallint NOT NULL,
    day_of_week  smallint NOT NULL,             -- 1 = Monday
    is_weekend   boolean NOT NULL
);

INSERT INTO analytics.dim_date
SELECT to_char(d, 'YYYYMMDD')::int,
       d::date,
       extract(year FROM d)::smallint,
       extract(quarter FROM d)::smallint,
       extract(month FROM d)::smallint,
       to_char(d, 'FMMonth'),
       extract(isoyear FROM d)::smallint,
       extract(week FROM d)::smallint,
       extract(day FROM d)::smallint,
       extract(isodow FROM d)::smallint,
       extract(isodow FROM d) IN (6, 7)
FROM generate_series('2024-01-01'::date, '2036-12-31'::date, interval '1 day') AS d;

-- Slowly changing dimension (type 2) so historical facts are sliced by the
-- learner's attributes at the time (persona, country, tier), not today's.
CREATE TABLE analytics.dim_user (
    user_key          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id           uuid NOT NULL,
    persona           ref.learner_persona,
    country_code      char(2),
    region            text,
    locale            text,
    subscription_tier ref.subscription_tier NOT NULL DEFAULT 'free',
    role              ref.user_role NOT NULL,
    level_band        text NOT NULL,             -- '1-4', '5-9', '10-19', '20+'
    signup_date       date NOT NULL,
    valid_from        timestamptz NOT NULL,
    valid_to          timestamptz NOT NULL DEFAULT 'infinity',
    is_current        boolean NOT NULL DEFAULT true,
    CONSTRAINT ck_dim_user_validity CHECK (valid_to > valid_from)
);
CREATE UNIQUE INDEX ux_dim_user_current ON analytics.dim_user (user_id) WHERE is_current;
CREATE INDEX ix_dim_user_history ON analytics.dim_user (user_id, valid_from);

-- One row per learner per active day.
CREATE TABLE analytics.fact_user_daily (
    activity_date       date NOT NULL,
    user_id             uuid NOT NULL,
    sessions            smallint NOT NULL DEFAULT 0,
    active_seconds      integer  NOT NULL DEFAULT 0,
    lessons_started     smallint NOT NULL DEFAULT 0,
    lessons_completed   smallint NOT NULL DEFAULT 0,
    quiz_attempts       smallint NOT NULL DEFAULT 0,
    questions_answered  smallint NOT NULL DEFAULT 0,
    questions_correct   smallint NOT NULL DEFAULT 0,
    code_runs           smallint NOT NULL DEFAULT 0,
    code_passes         smallint NOT NULL DEFAULT 0,
    flashcards_reviewed smallint NOT NULL DEFAULT 0,
    messages_sent       smallint NOT NULL DEFAULT 0,
    challenges_completed smallint NOT NULL DEFAULT 0,
    xp_earned           integer  NOT NULL DEFAULT 0,
    concepts_improved   smallint NOT NULL DEFAULT 0,
    mastery_gain        numeric(8,2) NOT NULL DEFAULT 0,
    llm_tokens          integer  NOT NULL DEFAULT 0,
    llm_cost_usd        numeric(12,6) NOT NULL DEFAULT 0,
    PRIMARY KEY (activity_date, user_id)
) PARTITION BY RANGE (activity_date);
CREATE INDEX ix_fact_user_daily_user ON analytics.fact_user_daily (user_id, activity_date);

-- Mastery snapshot only for (learner, concept, day) rows that changed.
CREATE TABLE analytics.fact_concept_mastery_daily (
    snapshot_date      date NOT NULL,
    user_id            uuid NOT NULL,
    concept_id         uuid NOT NULL,
    mastery_score      numeric(5,2) NOT NULL,
    mastery_delta      numeric(6,2) NOT NULL,
    attempts           smallint NOT NULL DEFAULT 0,
    correct            smallint NOT NULL DEFAULT 0,
    time_spent_seconds integer  NOT NULL DEFAULT 0,
    PRIMARY KEY (snapshot_date, user_id, concept_id)
) PARTITION BY RANGE (snapshot_date);
CREATE INDEX ix_fact_mastery_user ON analytics.fact_concept_mastery_daily (user_id, snapshot_date);
CREATE INDEX ix_fact_mastery_concept ON analytics.fact_concept_mastery_daily (concept_id, snapshot_date);

-- Concept difficulty and knowledge gaps across all learners.
CREATE TABLE analytics.agg_concept_daily (
    activity_date       date NOT NULL,
    concept_id          uuid NOT NULL REFERENCES curriculum.concepts (id) ON DELETE CASCADE,
    active_learners     integer NOT NULL DEFAULT 0,
    attempts            integer NOT NULL DEFAULT 0,
    correct             integer NOT NULL DEFAULT 0,
    correct_rate        numeric(5,4) GENERATED ALWAYS AS (
                            CASE WHEN attempts > 0 THEN round(correct::numeric / attempts, 4) END) STORED,
    avg_mastery         numeric(5,2),
    struggling_learners integer NOT NULL DEFAULT 0,    -- mastery < 40 with >= 3 attempts
    median_latency_ms   integer,
    tutor_questions     integer NOT NULL DEFAULT 0,    -- chat messages tagged with this concept
    PRIMARY KEY (activity_date, concept_id)
);
CREATE INDEX ix_agg_concept_daily_concept ON analytics.agg_concept_daily (concept_id, activity_date);

-- Engagement and effectiveness per content item.
CREATE TABLE analytics.agg_content_daily (
    activity_date         date NOT NULL,
    content_type          text NOT NULL CHECK (content_type IN ('lesson', 'asset', 'exercise', 'assessment',
                              'challenge', 'path')),
    content_id            uuid NOT NULL,
    views                 integer NOT NULL DEFAULT 0,
    unique_learners       integer NOT NULL DEFAULT 0,
    starts                integer NOT NULL DEFAULT 0,
    completions           integer NOT NULL DEFAULT 0,
    avg_time_seconds      integer,
    citations             integer NOT NULL DEFAULT 0,  -- tutor answers citing this asset
    helpful_votes         integer NOT NULL DEFAULT 0,
    unhelpful_votes       integer NOT NULL DEFAULT 0,
    recommendation_served integer NOT NULL DEFAULT 0,
    recommendation_clicks integer NOT NULL DEFAULT 0,
    post_mastery_gain     numeric(6,2),                -- avg mastery change within 7 days of use
    PRIMARY KEY (activity_date, content_type, content_id)
);
CREATE INDEX ix_agg_content_daily_content ON analytics.agg_content_daily (content_type, content_id, activity_date);

CREATE TABLE analytics.agg_platform_daily (
    activity_date             date PRIMARY KEY,
    dau                       integer NOT NULL,
    wau                       integer NOT NULL,
    mau                       integer NOT NULL,
    new_signups               integer NOT NULL,
    onboarding_completed      integer NOT NULL,
    paying_users              integer NOT NULL,
    messages                  integer NOT NULL,
    quiz_completion_rate      numeric(5,4),
    challenge_participation_rate numeric(5,4),
    avg_ttft_ms               integer,
    p95_ttft_ms               integer,
    llm_cost_usd              numeric(14,4) NOT NULL DEFAULT 0
);

CREATE TABLE analytics.cohort_retention (
    cohort_week  date NOT NULL CHECK (extract(isodow FROM cohort_week) = 1),
    weeks_since  smallint NOT NULL CHECK (weeks_since >= 0),
    cohort_size  integer NOT NULL CHECK (cohort_size > 0),
    active_users integer NOT NULL CHECK (active_users >= 0),
    retention    numeric(5,4) GENERATED ALWAYS AS (round(active_users::numeric / cohort_size, 4)) STORED,
    PRIMARY KEY (cohort_week, weeks_since)
);

-- Weekly / monthly learner reports with the AI-written narrative.
CREATE TABLE analytics.learner_reports (
    id              uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    user_id         uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    period_type     text NOT NULL CHECK (period_type IN ('weekly', 'monthly')),
    period_start    date NOT NULL,
    period_end      date NOT NULL,
    metrics         jsonb NOT NULL,
    strengths       jsonb NOT NULL DEFAULT '[]',
    weaknesses      jsonb NOT NULL DEFAULT '[]',
    recommendations jsonb NOT NULL DEFAULT '[]',
    narrative_md    text,
    locale          text NOT NULL DEFAULT 'en' REFERENCES ref.languages (code),
    model           text,
    generated_at    timestamptz NOT NULL DEFAULT now(),
    delivered_at    timestamptz,
    opened_at       timestamptz,
    CONSTRAINT uq_learner_reports_period UNIQUE (user_id, period_type, period_start),
    CONSTRAINT ck_learner_reports_period CHECK (period_end > period_start)
);

CREATE TABLE analytics.etl_watermarks (
    job_name          text PRIMARY KEY,
    last_processed_at timestamptz NOT NULL,
    last_run_at       timestamptz NOT NULL DEFAULT now(),
    last_status       text NOT NULL DEFAULT 'ok' CHECK (last_status IN ('ok', 'failed', 'running')),
    rows_processed    bigint NOT NULL DEFAULT 0,
    last_error        text
);

-- -----------------------------------------------------------------------------
-- Views and materialised views
-- -----------------------------------------------------------------------------

-- Strong and weak concepts per learner, live from current mastery.
CREATE OR REPLACE VIEW analytics.v_learner_strengths AS
SELECT m.user_id,
       m.concept_id,
       c.slug AS concept_slug,
       c.name AS concept_name,
       m.score,
       m.band,
       m.evidence_count,
       CASE WHEN m.band IN ('strong', 'mastered') THEN 'strength'
            WHEN m.band = 'weak' THEN 'weakness'
            ELSE 'developing' END AS classification
FROM learning.concept_mastery m
JOIN curriculum.concepts c ON c.id = m.concept_id
WHERE m.evidence_count >= 3;

-- Learning velocity: concepts crossing the 'strong' threshold per ISO week.
CREATE OR REPLACE VIEW analytics.v_learning_velocity_weekly AS
SELECT e.user_id,
       date_trunc('week', e.occurred_at)::date AS week_start,
       count(DISTINCT e.concept_id) FILTER (WHERE e.score_before < 70 AND e.score_after >= 70) AS concepts_mastered,
       sum(e.delta) FILTER (WHERE e.source <> 'decay')                                          AS mastery_gained,
       sum(e.delta) FILTER (WHERE e.source = 'decay')                                           AS mastery_decayed
FROM learning.mastery_events e
GROUP BY e.user_id, date_trunc('week', e.occurred_at)::date;

-- Hardest concepts over the trailing 30 days (admin dashboard).
CREATE MATERIALIZED VIEW analytics.mv_concept_difficulty_30d AS
SELECT a.concept_id,
       sum(a.attempts)                                                  AS attempts,
       round(sum(a.correct)::numeric / nullif(sum(a.attempts), 0), 4)   AS correct_rate,
       round(avg(a.avg_mastery), 2)                                     AS avg_mastery,
       max(a.struggling_learners)                                       AS peak_struggling_learners,
       rank() OVER (ORDER BY sum(a.correct)::numeric / nullif(sum(a.attempts), 0) ASC NULLS LAST) AS difficulty_rank
FROM analytics.agg_concept_daily a
WHERE a.activity_date >= current_date - 30
GROUP BY a.concept_id
WITH NO DATA;
CREATE UNIQUE INDEX ux_mv_concept_difficulty ON analytics.mv_concept_difficulty_30d (concept_id);

-- Content engagement over the trailing 30 days.
CREATE MATERIALIZED VIEW analytics.mv_content_engagement_30d AS
SELECT a.content_type,
       a.content_id,
       sum(a.views)            AS views,
       sum(a.unique_learners)  AS learner_days,
       sum(a.completions)      AS completions,
       round(sum(a.completions)::numeric / nullif(sum(a.starts), 0), 4) AS completion_rate,
       sum(a.citations)        AS citations,
       round(sum(a.helpful_votes)::numeric / nullif(sum(a.helpful_votes + a.unhelpful_votes), 0), 4) AS helpful_rate,
       round(avg(a.post_mastery_gain), 2) AS avg_post_mastery_gain
FROM analytics.agg_content_daily a
WHERE a.activity_date >= current_date - 30
GROUP BY a.content_type, a.content_id
WITH NO DATA;
CREATE UNIQUE INDEX ux_mv_content_engagement ON analytics.mv_content_engagement_30d (content_type, content_id);
