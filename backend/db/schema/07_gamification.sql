-- =============================================================================
-- 07 gamification
-- The XP ledger is the source of truth; game.user_stats is a cached projection
-- updated in the same transaction as each ledger insert. Level, streak, and
-- cap rules live in backend/app/domain/gamification.py.
--
-- Catalog text (badges, titles, challenges) uses *_i18n jsonb ({"en": ..., "fr": ...})
-- because these are short strings without a review workflow. Curriculum content
-- uses translation tables instead (per-locale review status, full-text search).
-- =============================================================================

CREATE TABLE game.titles (
    id          smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    slug        text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9_]{1,60}$'),
    name_i18n   jsonb NOT NULL CHECK (name_i18n ? 'en'),
    description_i18n jsonb NOT NULL DEFAULT '{}',
    min_level   integer NOT NULL DEFAULT 1 CHECK (min_level >= 1),
    criteria    jsonb NOT NULL DEFAULT '{}',   -- e.g. {"path_completed": "reinforcement-learning"}
    sort_order  smallint NOT NULL DEFAULT 0,
    is_active   boolean NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE game.badges (
    id                 smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    slug               text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9_]{1,60}$'),
    name_i18n          jsonb NOT NULL CHECK (name_i18n ? 'en'),
    description_i18n   jsonb NOT NULL DEFAULT '{}',
    icon               text NOT NULL DEFAULT 'seal',
    category           text NOT NULL CHECK (category IN ('learning', 'streak', 'mastery', 'coding', 'research',
                           'community', 'challenge', 'special')),
    tier               text NOT NULL DEFAULT 'bronze' CHECK (tier IN ('bronze', 'silver', 'gold', 'platinum')),
    xp_reward          integer NOT NULL DEFAULT 0 CHECK (xp_reward >= 0),
    achievement_points integer NOT NULL DEFAULT 10 CHECK (achievement_points >= 0),
    criteria           jsonb NOT NULL DEFAULT '{}',
    is_secret          boolean NOT NULL DEFAULT false,
    is_active          boolean NOT NULL DEFAULT true,
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE game.user_badges (
    user_id    uuid     NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    badge_id   smallint NOT NULL REFERENCES game.badges (id) ON DELETE RESTRICT,
    awarded_at timestamptz NOT NULL DEFAULT now(),
    source_ref uuid,
    PRIMARY KEY (user_id, badge_id)
);
CREATE INDEX ix_user_badges_badge ON game.user_badges (badge_id, awarded_at);

CREATE TABLE game.user_titles (
    user_id     uuid     NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    title_id    smallint NOT NULL REFERENCES game.titles (id) ON DELETE RESTRICT,
    earned_at   timestamptz NOT NULL DEFAULT now(),
    is_equipped boolean NOT NULL DEFAULT false,
    PRIMARY KEY (user_id, title_id)
);
CREATE UNIQUE INDEX ux_user_titles_one_equipped ON game.user_titles (user_id) WHERE is_equipped;

-- Hot row per learner. Low fillfactor leaves room for HOT updates.
CREATE TABLE game.user_stats (
    user_id                 uuid PRIMARY KEY REFERENCES identity.users (id) ON DELETE CASCADE,
    total_xp                bigint  NOT NULL DEFAULT 0 CHECK (total_xp >= 0),
    level                   integer NOT NULL DEFAULT 1 CHECK (level >= 1),
    achievement_points      integer NOT NULL DEFAULT 0 CHECK (achievement_points >= 0),
    current_streak          integer NOT NULL DEFAULT 0 CHECK (current_streak >= 0),
    longest_streak          integer NOT NULL DEFAULT 0 CHECK (longest_streak >= 0),
    last_active_on          date,                       -- learner's local date
    streak_freezes          smallint NOT NULL DEFAULT 0 CHECK (streak_freezes BETWEEN 0 AND 10),
    lessons_completed       integer NOT NULL DEFAULT 0 CHECK (lessons_completed >= 0),
    quizzes_completed       integer NOT NULL DEFAULT 0 CHECK (quizzes_completed >= 0),
    perfect_quizzes         integer NOT NULL DEFAULT 0 CHECK (perfect_quizzes >= 0),
    code_passes             integer NOT NULL DEFAULT 0 CHECK (code_passes >= 0),
    challenges_completed    integer NOT NULL DEFAULT 0 CHECK (challenges_completed >= 0),
    projects_completed      integer NOT NULL DEFAULT 0 CHECK (projects_completed >= 0),
    research_contributions  integer NOT NULL DEFAULT 0 CHECK (research_contributions >= 0),
    community_points        integer NOT NULL DEFAULT 0 CHECK (community_points >= 0),
    updated_at              timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_user_stats_streak CHECK (longest_streak >= current_streak)
) WITH (fillfactor = 70);
CREATE INDEX ix_user_stats_xp ON game.user_stats (total_xp DESC, user_id);

-- Append-only XP ledger. Partitioned by the learner's LOCAL date so that the
-- idempotency key can be unique per partition and the daily cap is evaluated
-- on the same day boundary the learner sees.
CREATE TABLE game.xp_ledger (
    id              uuid NOT NULL DEFAULT util.uuid_v7(),
    local_date      date NOT NULL,
    occurred_at     timestamptz NOT NULL DEFAULT now(),
    user_id         uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    amount          integer NOT NULL CHECK (amount <> 0),
    requested_amount integer NOT NULL,            -- before the daily cap
    source          ref.xp_source NOT NULL,
    source_ref      uuid,
    idempotency_key text NOT NULL CHECK (char_length(idempotency_key) <= 200),  -- e.g. 'quiz:<attempt_id>'
    metadata        jsonb,
    PRIMARY KEY (id, local_date),
    CONSTRAINT uq_xp_ledger_idempotency UNIQUE (user_id, idempotency_key, local_date),
    CONSTRAINT ck_xp_ledger_negative_sources CHECK (amount > 0 OR source IN ('admin_adjustment', 'reversal'))
) PARTITION BY RANGE (local_date);
CREATE INDEX ix_xp_ledger_user ON game.xp_ledger (user_id, local_date);
CREATE INDEX ix_xp_ledger_source ON game.xp_ledger (source, local_date);

-- Compacted history kept after ledger partitions expire.
CREATE TABLE game.xp_monthly_rollup (
    user_id  uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    month    date NOT NULL CHECK (extract(day FROM month) = 1),
    source   ref.xp_source NOT NULL,
    amount   bigint NOT NULL,
    events   integer NOT NULL CHECK (events >= 0),
    PRIMARY KEY (user_id, month, source)
);

-- Per learner per local day: daily XP cap, streak calendar, activity heatmap.
CREATE TABLE game.daily_activity (
    user_id             uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    activity_date       date NOT NULL,
    xp_earned           integer  NOT NULL DEFAULT 0 CHECK (xp_earned >= 0),
    xp_capped           integer  NOT NULL DEFAULT 0 CHECK (xp_capped >= 0),   -- XP refused by the cap
    lessons_completed   smallint NOT NULL DEFAULT 0,
    quizzes_completed   smallint NOT NULL DEFAULT 0,
    code_passes         smallint NOT NULL DEFAULT 0,
    flashcards_reviewed smallint NOT NULL DEFAULT 0,
    challenges_completed smallint NOT NULL DEFAULT 0,
    goal_met            boolean  NOT NULL DEFAULT false,
    streak_freeze_used  boolean  NOT NULL DEFAULT false,
    updated_at          timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, activity_date)
) PARTITION BY RANGE (activity_date);

-- -----------------------------------------------------------------------------
-- Daily challenges
-- -----------------------------------------------------------------------------

CREATE TABLE game.challenges (
    id               uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    challenge_date   date NOT NULL,
    kind             ref.challenge_kind NOT NULL,
    difficulty       ref.difficulty_level NOT NULL,
    audience_persona ref.learner_persona,          -- NULL = everyone
    concept_id       uuid REFERENCES curriculum.concepts (id) ON DELETE SET NULL,
    title_i18n       jsonb NOT NULL CHECK (title_i18n ? 'en'),
    prompt_i18n      jsonb NOT NULL CHECK (prompt_i18n ? 'en'),
    payload          jsonb NOT NULL DEFAULT '{}',
    assessment_id    uuid REFERENCES curriculum.assessments (id) ON DELETE SET NULL,
    exercise_id      uuid REFERENCES curriculum.coding_exercises (id) ON DELETE SET NULL,
    asset_id         uuid REFERENCES knowledge.assets (id) ON DELETE SET NULL,
    xp_reward        integer NOT NULL DEFAULT 50 CHECK (xp_reward BETWEEN 0 AND 1000),
    badge_id         smallint REFERENCES game.badges (id) ON DELETE SET NULL,
    generated_by     text NOT NULL DEFAULT 'llm' CHECK (generated_by IN ('llm', 'admin', 'rotation')),
    status           ref.content_status NOT NULL DEFAULT 'draft',
    opens_at         timestamptz NOT NULL,
    closes_at        timestamptz NOT NULL,
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_challenges_window CHECK (closes_at > opens_at)
);
CREATE UNIQUE INDEX ux_challenges_slot ON game.challenges
    (challenge_date, kind, difficulty, audience_persona) NULLS NOT DISTINCT;
CREATE INDEX ix_challenges_open ON game.challenges (opens_at, closes_at) WHERE status = 'published';

CREATE TABLE game.challenge_participations (
    challenge_id uuid NOT NULL REFERENCES game.challenges (id) ON DELETE CASCADE,
    user_id      uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    status       text NOT NULL DEFAULT 'started' CHECK (status IN ('started', 'completed', 'failed', 'expired')),
    score        numeric(6,2) CHECK (score BETWEEN 0 AND 100),
    attempt_ref  uuid,          -- quiz attempt or code submission id
    started_at   timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    xp_awarded   integer NOT NULL DEFAULT 0 CHECK (xp_awarded >= 0),
    PRIMARY KEY (challenge_id, user_id),
    CONSTRAINT ck_participations_completed CHECK ((status = 'completed') = (completed_at IS NOT NULL))
);
CREATE INDEX ix_participations_user ON game.challenge_participations (user_id, started_at DESC);

-- -----------------------------------------------------------------------------
-- Leaderboards. Live ranks are served from Redis sorted sets; these tables hold
-- the periodically materialised standings (and closed-period history).
-- A refresh builds a new board in status 'building', then flips it to 'live'
-- and marks the previous one 'superseded', so readers never see a half-built
-- ranking. Friends ranking is computed on read: friends ∩ global board.
-- -----------------------------------------------------------------------------

CREATE TABLE game.leaderboards (
    id                uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    scope             ref.leaderboard_scope  NOT NULL,
    scope_key         text NOT NULL DEFAULT '',   -- '' for global, ISO country, or region name
    period            ref.leaderboard_period NOT NULL,
    period_start      date NOT NULL,
    period_end        date,                        -- NULL for all_time
    metric            ref.leaderboard_metric NOT NULL,
    status            text NOT NULL DEFAULT 'building' CHECK (status IN ('building', 'live', 'closed', 'superseded')),
    participant_count integer NOT NULL DEFAULT 0,
    computed_at       timestamptz,
    created_at        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_leaderboards_scope_key CHECK ((scope = 'global') = (scope_key = '')),
    CONSTRAINT ck_leaderboards_period CHECK ((period = 'all_time') = (period_end IS NULL))
);
CREATE UNIQUE INDEX ux_leaderboards_current ON game.leaderboards (scope, scope_key, period, period_start, metric)
    WHERE status IN ('live', 'closed');
CREATE INDEX ix_leaderboards_cleanup ON game.leaderboards (created_at) WHERE status = 'superseded';

CREATE TABLE game.leaderboard_entries (
    leaderboard_id uuid NOT NULL REFERENCES game.leaderboards (id) ON DELETE CASCADE,
    user_id        uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    rank           integer NOT NULL CHECK (rank >= 1),
    score          numeric(14,2) NOT NULL,
    percentile     numeric(5,2) NOT NULL CHECK (percentile BETWEEN 0 AND 100),
    previous_rank  integer,
    PRIMARY KEY (leaderboard_id, user_id)
);
CREATE INDEX ix_leaderboard_entries_rank ON game.leaderboard_entries (leaderboard_id, rank);
CREATE INDEX ix_leaderboard_entries_user ON game.leaderboard_entries (user_id);

-- Canonical pair ordering stores each friendship once.
CREATE TABLE game.friendships (
    user_low_id  uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    user_high_id uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    requested_by uuid NOT NULL,
    status       text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'blocked')),
    requested_at timestamptz NOT NULL DEFAULT now(),
    responded_at timestamptz,
    PRIMARY KEY (user_low_id, user_high_id),
    CONSTRAINT ck_friendships_order CHECK (user_low_id < user_high_id),
    CONSTRAINT ck_friendships_requester CHECK (requested_by IN (user_low_id, user_high_id))
);
CREATE INDEX ix_friendships_high ON game.friendships (user_high_id, status);

CREATE OR REPLACE VIEW game.v_friends AS
SELECT user_low_id AS user_id, user_high_id AS friend_id, responded_at AS since
FROM game.friendships WHERE status = 'accepted'
UNION ALL
SELECT user_high_id, user_low_id, responded_at
FROM game.friendships WHERE status = 'accepted';

-- -----------------------------------------------------------------------------
-- Cross-schema foreign keys deferred from 05_learning.sql
-- -----------------------------------------------------------------------------

ALTER TABLE learning.quizzes
    ADD CONSTRAINT fk_quizzes_challenge
    FOREIGN KEY (challenge_id) REFERENCES game.challenges (id) ON DELETE SET NULL;

ALTER TABLE learning.code_submissions
    ADD CONSTRAINT fk_code_submissions_challenge
    FOREIGN KEY (challenge_id) REFERENCES game.challenges (id) ON DELETE SET NULL;
