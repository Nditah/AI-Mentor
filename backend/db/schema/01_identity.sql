-- =============================================================================
-- 01 reference data and identity (user profile model)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Reference data
-- -----------------------------------------------------------------------------

CREATE TABLE ref.languages (
    code        text PRIMARY KEY CHECK (code ~ '^[a-z]{2}(-[A-Z]{2})?$'),   -- BCP 47 subset
    name        text NOT NULL,
    native_name text NOT NULL,
    is_enabled  boolean NOT NULL DEFAULT true,
    is_default  boolean NOT NULL DEFAULT false
);
CREATE UNIQUE INDEX ux_languages_single_default ON ref.languages (is_default) WHERE is_default;

CREATE TABLE ref.countries (
    iso2       char(2) PRIMARY KEY CHECK (iso2 ~ '^[A-Z]{2}$'),
    iso3       char(3) NOT NULL UNIQUE CHECK (iso3 ~ '^[A-Z]{3}$'),
    name       text    NOT NULL,
    region     text    NOT NULL,      -- e.g. 'Africa', 'Europe' (used for regional leaderboards)
    subregion  text
);

CREATE TABLE ref.voice_accents (
    code       text PRIMARY KEY CHECK (code ~ '^[a-z_]+$'),
    name       text NOT NULL,
    locale     text REFERENCES ref.languages (code),
    is_enabled boolean NOT NULL DEFAULT true
);

-- -----------------------------------------------------------------------------
-- Users. Authentication lives in Clerk; this is the local identity record.
-- Hot, frequently-updated counters (XP, streak) live in game.user_stats so that
-- this row stays narrow and rarely updated.
-- -----------------------------------------------------------------------------

CREATE TABLE identity.users (
    id                uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    clerk_id          text NOT NULL UNIQUE,
    email             citext NOT NULL,
    email_verified_at timestamptz,
    display_name      text NOT NULL CHECK (char_length(display_name) BETWEEN 1 AND 120),
    handle            citext UNIQUE CHECK (handle ~ '^[a-z0-9_]{3,30}$'),
    avatar_url        text,
    role              ref.user_role NOT NULL DEFAULT 'student',
    status            ref.account_status NOT NULL DEFAULT 'active',
    last_seen_at      timestamptz,
    deletion_requested_at timestamptz,
    deleted_at        timestamptz,
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_users_deleted_status CHECK ((deleted_at IS NULL) OR status = 'deleted')
);
CREATE UNIQUE INDEX ux_users_email_live ON identity.users (email) WHERE deleted_at IS NULL;
CREATE INDEX ix_users_role ON identity.users (role) WHERE role <> 'student';
CREATE INDEX ix_users_pending_deletion ON identity.users (deletion_requested_at)
    WHERE status = 'pending_deletion';
COMMENT ON COLUMN identity.users.handle IS 'Public name on leaderboards; never the email.';

CREATE TABLE identity.user_profiles (
    user_id                     uuid PRIMARY KEY REFERENCES identity.users (id) ON DELETE CASCADE,
    country_code                char(2) REFERENCES ref.countries (iso2),
    region_code                 text CHECK (region_code ~ '^[A-Z]{2}-[A-Z0-9]{1,3}$'),  -- ISO 3166-2
    timezone                    text NOT NULL DEFAULT 'UTC',
    preferred_locale            text NOT NULL DEFAULT 'en' REFERENCES ref.languages (code),
    persona                     ref.learner_persona,
    education_level             text CHECK (education_level IN
                                    ('secondary', 'undergraduate', 'postgraduate', 'doctorate', 'self_taught', 'other')),
    professional_experience_years smallint CHECK (professional_experience_years BETWEEN 0 AND 70),
    industry_sector             text,
    career_goal                 text CHECK (char_length(career_goal) <= 1000),
    bio                         text CHECK (char_length(bio) <= 2000),
    show_on_leaderboards        boolean NOT NULL DEFAULT true,
    is_profile_public           boolean NOT NULL DEFAULT false,
    onboarding_completed_at     timestamptz,
    created_at                  timestamptz NOT NULL DEFAULT now(),
    updated_at                  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_user_profiles_country ON identity.user_profiles (country_code, region_code);
CREATE INDEX ix_user_profiles_persona ON identity.user_profiles (persona);

-- How the tutor teaches. Changeable at any time; history is in audit.row_changes.
CREATE TABLE identity.learning_preferences (
    user_id                uuid PRIMARY KEY REFERENCES identity.users (id) ON DELETE CASCADE,
    teaching_style         ref.teaching_style     NOT NULL DEFAULT 'mixed',
    pace                   ref.learning_pace      NOT NULL DEFAULT 'moderate',
    technical_depth        ref.difficulty_level   NOT NULL DEFAULT 'beginner',
    math_depth             ref.math_depth         NOT NULL DEFAULT 'light',
    breadth                ref.breadth_preference NOT NULL DEFAULT 'balanced',
    preferred_difficulty   ref.difficulty_level   NOT NULL DEFAULT 'beginner',
    programming_experience ref.skill_band         NOT NULL DEFAULT 'none',
    math_comfort           ref.skill_band         NOT NULL DEFAULT 'beginner',
    weekly_study_minutes   integer  NOT NULL DEFAULT 180 CHECK (weekly_study_minutes BETWEEN 0 AND 10080),
    daily_goal_xp          smallint NOT NULL DEFAULT 50  CHECK (daily_goal_xp BETWEEN 0 AND 400),
    study_days_mask        smallint NOT NULL DEFAULT 127 CHECK (study_days_mask BETWEEN 0 AND 127), -- bit 0 = Monday
    reminder_local_time    time,
    created_at             timestamptz NOT NULL DEFAULT now(),
    updated_at             timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE identity.tutor_avatars (
    user_id             uuid PRIMARY KEY REFERENCES identity.users (id) ON DELETE CASCADE,
    display_name        text NOT NULL DEFAULT 'Mentor' CHECK (char_length(display_name) BETWEEN 1 AND 40),
    age_appearance      ref.age_appearance      NOT NULL DEFAULT 'adult',
    gender_presentation ref.gender_presentation NOT NULL DEFAULT 'neutral',
    voice_accent        text NOT NULL DEFAULT 'british' REFERENCES ref.voice_accents (code),
    personality         ref.tutor_personality   NOT NULL DEFAULT 'socratic',
    tts_voice_id        text,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

-- Retakes are allowed; the latest completed row is authoritative.
CREATE TABLE identity.onboarding_assessments (
    id                   uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    user_id              uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    questionnaire_version smallint NOT NULL,
    responses            jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(responses) = 'object'),
    knowledge_level      ref.difficulty_level,
    initial_skill_score  numeric(5,2) CHECK (initial_skill_score BETWEEN 0 AND 100),
    assigned_persona     ref.learner_persona,
    recommended_path_id  uuid,            -- FK added in 02_curriculum.sql
    started_at           timestamptz NOT NULL DEFAULT now(),
    completed_at         timestamptz,
    CONSTRAINT ck_onboarding_completion CHECK (completed_at IS NULL OR completed_at >= started_at)
);
CREATE INDEX ix_onboarding_user_latest ON identity.onboarding_assessments (user_id, completed_at DESC NULLS LAST);

CREATE TABLE identity.user_interests (
    user_id          uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    taxonomy_node_id uuid NOT NULL,       -- FK added in 02_curriculum.sql
    kind             text NOT NULL CHECK (kind IN ('topic', 'research_interest', 'career_interest')),
    weight           numeric(3,2) NOT NULL DEFAULT 1.00 CHECK (weight BETWEEN 0 AND 1),
    created_at       timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, taxonomy_node_id, kind)
);
CREATE INDEX ix_user_interests_node ON identity.user_interests (taxonomy_node_id);

CREATE TABLE identity.subscriptions (
    id                       uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    user_id                  uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    provider                 text NOT NULL DEFAULT 'stripe' CHECK (provider IN ('stripe', 'manual')),
    provider_customer_id     text NOT NULL,
    provider_subscription_id text UNIQUE,
    tier                     ref.subscription_tier   NOT NULL,
    status                   ref.subscription_status NOT NULL,
    current_period_start     timestamptz,
    current_period_end       timestamptz,
    cancel_at                timestamptz,
    canceled_at              timestamptz,
    created_at               timestamptz NOT NULL DEFAULT now(),
    updated_at               timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_subscription_period CHECK (current_period_end IS NULL OR current_period_end > current_period_start)
);
CREATE UNIQUE INDEX ux_subscriptions_one_live ON identity.subscriptions (user_id)
    WHERE status IN ('trialing', 'active', 'past_due');
CREATE INDEX ix_subscriptions_customer ON identity.subscriptions (provider, provider_customer_id);
COMMENT ON TABLE identity.subscriptions IS
    'Billing history, kept as tax law requires. Erasure detaches it from the user (SET NULL); Stripe ids remain.';

-- Append-only consent ledger; latest row per (user, consent_type) wins.
CREATE TABLE identity.consents (
    id            uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    user_id       uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    consent_type  text NOT NULL CHECK (consent_type IN
                      ('terms', 'privacy', 'marketing_email', 'product_analytics', 'research_data', 'voice_recording')),
    policy_version text NOT NULL,
    granted       boolean NOT NULL,
    recorded_at   timestamptz NOT NULL DEFAULT now(),
    source        text NOT NULL DEFAULT 'web'
);
CREATE INDEX ix_consents_latest ON identity.consents (user_id, consent_type, recorded_at DESC);

-- subject_user_id has no FK on purpose: it must survive erasure so completed
-- erasures can be replayed after a point-in-time restore.
CREATE TABLE identity.data_subject_requests (
    id            uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    subject_user_id uuid,
    subject_email citext NOT NULL,
    kind          text NOT NULL CHECK (kind IN ('export', 'erasure', 'rectification', 'restriction')),
    status        text NOT NULL DEFAULT 'received' CHECK (status IN ('received', 'in_progress', 'completed', 'rejected')),
    requested_at  timestamptz NOT NULL DEFAULT now(),
    due_at        timestamptz NOT NULL DEFAULT now() + interval '30 days',
    completed_at  timestamptz,
    handled_by    uuid REFERENCES identity.users (id) ON DELETE SET NULL,
    artifact_uri  text,
    notes         text
);
CREATE INDEX ix_dsr_open ON identity.data_subject_requests (due_at) WHERE status IN ('received', 'in_progress');
CREATE INDEX ix_dsr_erasures ON identity.data_subject_requests (completed_at)
    WHERE kind = 'erasure' AND status = 'completed';

-- Idempotency for Clerk and Stripe webhooks.
CREATE TABLE identity.webhook_events (
    provider     text NOT NULL CHECK (provider IN ('clerk', 'stripe')),
    event_id     text NOT NULL,
    event_type   text NOT NULL,
    payload      jsonb NOT NULL,
    received_at  timestamptz NOT NULL DEFAULT now(),
    processed_at timestamptz,
    error        text,
    PRIMARY KEY (provider, event_id)
);
CREATE INDEX ix_webhook_events_received ON identity.webhook_events (received_at);
