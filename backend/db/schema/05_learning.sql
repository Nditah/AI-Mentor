-- =============================================================================
-- 05 learning: enrolments, progress, mastery, quizzes, code, flashcards, plans
--
-- Partitioning (partitions are created in 12_partitions.sql):
--   concept_mastery     HASH (user_id), 16 partitions   current state, no retention
--   mastery_events      RANGE (occurred_at) monthly     evidence log, learning velocity
--   quiz_attempts       RANGE (started_at) monthly
--   question_responses  RANGE (attempt_started_at)      co-partitioned with quiz_attempts
--   code_submissions    RANGE (submitted_at) monthly
--   flashcard_reviews   RANGE (reviewed_at) monthly
--   recommendations     RANGE (generated_at) monthly
-- Primary keys on partitioned tables must include the partition key.
-- =============================================================================

CREATE TABLE learning.enrollments (
    id               uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    user_id          uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    path_id          uuid NOT NULL REFERENCES curriculum.learning_paths (id) ON DELETE RESTRICT,
    status           text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'dropped')),
    source           text NOT NULL DEFAULT 'self' CHECK (source IN ('onboarding', 'self', 'recommendation', 'admin')),
    progress_pct     numeric(5,2) NOT NULL DEFAULT 0 CHECK (progress_pct BETWEEN 0 AND 100),
    current_item_id  uuid REFERENCES curriculum.learning_path_items (id) ON DELETE SET NULL,
    started_at       timestamptz NOT NULL DEFAULT now(),
    last_activity_at timestamptz,
    completed_at     timestamptz,
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_enrollments_user_path UNIQUE (user_id, path_id),
    CONSTRAINT ck_enrollments_completed CHECK ((status = 'completed') = (completed_at IS NOT NULL))
);
CREATE INDEX ix_enrollments_path_status ON learning.enrollments (path_id, status);

CREATE TABLE learning.lesson_progress (
    user_id            uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    lesson_id          uuid NOT NULL REFERENCES curriculum.lessons (id) ON DELETE CASCADE,
    status             ref.progress_status NOT NULL DEFAULT 'in_progress',
    last_locale        text REFERENCES ref.languages (code),
    last_teaching_style ref.teaching_style,
    started_at         timestamptz NOT NULL DEFAULT now(),
    completed_at       timestamptz,
    time_spent_seconds integer NOT NULL DEFAULT 0 CHECK (time_spent_seconds >= 0),
    visits             integer NOT NULL DEFAULT 1 CHECK (visits >= 0),
    last_position      jsonb,
    updated_at         timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, lesson_id),
    CONSTRAINT ck_lesson_progress_completed CHECK ((status = 'completed') = (completed_at IS NOT NULL))
) WITH (fillfactor = 85);
CREATE INDEX ix_lesson_progress_lesson ON learning.lesson_progress (lesson_id, status);
CREATE INDEX ix_lesson_progress_user_recent ON learning.lesson_progress (user_id, updated_at DESC);

-- Current mastery per (learner, concept). One row per pair; updated in place.
CREATE TABLE learning.concept_mastery (
    user_id          uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    concept_id       uuid NOT NULL REFERENCES curriculum.concepts (id) ON DELETE CASCADE,
    score            numeric(5,2) NOT NULL DEFAULT 0 CHECK (score BETWEEN 0 AND 100),
    confidence       numeric(4,3) NOT NULL DEFAULT 0 CHECK (confidence BETWEEN 0 AND 1),
    evidence_count   integer NOT NULL DEFAULT 0 CHECK (evidence_count >= 0),
    correct_count    integer NOT NULL DEFAULT 0 CHECK (correct_count >= 0),
    band             text GENERATED ALWAYS AS (
                         CASE WHEN score >= 85 THEN 'mastered'
                              WHEN score >= 70 THEN 'strong'
                              WHEN score >= 40 THEN 'developing'
                              ELSE 'weak' END) STORED,
    first_seen_at    timestamptz NOT NULL DEFAULT now(),
    last_evidence_at timestamptz,
    next_review_at   timestamptz,        -- retention check scheduling (forgetting curve)
    updated_at       timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, concept_id),
    CONSTRAINT ck_mastery_counts CHECK (correct_count <= evidence_count)
) PARTITION BY HASH (user_id);
CREATE INDEX ix_concept_mastery_concept ON learning.concept_mastery (concept_id, score);
CREATE INDEX ix_concept_mastery_review ON learning.concept_mastery (user_id, next_review_at)
    WHERE next_review_at IS NOT NULL;

-- Every mastery change with its cause. Source of learning-velocity analytics.
CREATE TABLE learning.mastery_events (
    id           uuid NOT NULL DEFAULT util.uuid_v7(),
    occurred_at  timestamptz NOT NULL DEFAULT now(),
    user_id      uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    concept_id   uuid NOT NULL REFERENCES curriculum.concepts (id) ON DELETE CASCADE,
    source       text NOT NULL CHECK (source IN ('quiz', 'code', 'lesson', 'flashcard', 'tutor_check',
                     'challenge', 'onboarding', 'decay', 'admin')),
    source_ref   uuid,
    score_before numeric(5,2) NOT NULL CHECK (score_before BETWEEN 0 AND 100),
    score_after  numeric(5,2) NOT NULL CHECK (score_after BETWEEN 0 AND 100),
    delta        numeric(6,2) GENERATED ALWAYS AS (score_after - score_before) STORED,
    PRIMARY KEY (id, occurred_at)
) PARTITION BY RANGE (occurred_at);
CREATE INDEX ix_mastery_events_user ON learning.mastery_events (user_id, occurred_at);
CREATE INDEX ix_mastery_events_concept ON learning.mastery_events (concept_id, occurred_at);

-- -----------------------------------------------------------------------------
-- Quizzes. A quiz is a generated instance for one learner. Each item stores a
-- snapshot of exactly what the learner saw (translated, possibly LLM-generated),
-- so results stay reproducible after bank questions are edited.
-- -----------------------------------------------------------------------------

CREATE TABLE learning.quizzes (
    id                uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    user_id           uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    assessment_id     uuid REFERENCES curriculum.assessments (id) ON DELETE SET NULL,
    concept_id        uuid REFERENCES curriculum.concepts (id) ON DELETE SET NULL,
    challenge_id      uuid,                    -- FK added in 07_gamification.sql
    difficulty        ref.difficulty_level NOT NULL,
    locale            text NOT NULL DEFAULT 'en' REFERENCES ref.languages (code),
    generated_by      text NOT NULL CHECK (generated_by IN ('bank', 'llm', 'adaptive', 'assessment')),
    llm_invocation_id uuid,
    created_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_quizzes_user ON learning.quizzes (user_id, created_at DESC);

CREATE TABLE learning.quiz_items (
    quiz_id           uuid NOT NULL REFERENCES learning.quizzes (id) ON DELETE CASCADE,
    position          smallint NOT NULL CHECK (position >= 0),
    question_id       uuid REFERENCES curriculum.questions (id) ON DELETE SET NULL,
    concept_id        uuid REFERENCES curriculum.concepts (id) ON DELETE SET NULL,
    kind              ref.question_kind NOT NULL,
    difficulty        ref.difficulty_level NOT NULL,
    points            numeric(6,2) NOT NULL DEFAULT 1 CHECK (points > 0),
    question_snapshot jsonb NOT NULL CHECK (jsonb_typeof(question_snapshot) = 'object'),
    PRIMARY KEY (quiz_id, position)
);
CREATE INDEX ix_quiz_items_question ON learning.quiz_items (question_id) WHERE question_id IS NOT NULL;

CREATE TABLE learning.quiz_attempts (
    id               uuid NOT NULL DEFAULT util.uuid_v7(),
    started_at       timestamptz NOT NULL DEFAULT now(),
    quiz_id          uuid NOT NULL REFERENCES learning.quizzes (id) ON DELETE CASCADE,
    user_id          uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    status           text NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'submitted', 'abandoned', 'expired')),
    submitted_at     timestamptz,
    score            numeric(8,2) CHECK (score >= 0),
    max_score        numeric(8,2) CHECK (max_score > 0),
    score_pct        numeric(5,2) GENERATED ALWAYS AS (
                         CASE WHEN max_score > 0 THEN round(100 * score / max_score, 2) END) STORED,
    duration_seconds integer CHECK (duration_seconds >= 0),
    xp_awarded       integer NOT NULL DEFAULT 0 CHECK (xp_awarded >= 0),
    PRIMARY KEY (id, started_at),
    CONSTRAINT ck_quiz_attempts_submitted CHECK ((status = 'submitted') = (submitted_at IS NOT NULL)),
    CONSTRAINT ck_quiz_attempts_score CHECK (score IS NULL OR max_score IS NULL OR score <= max_score)
) PARTITION BY RANGE (started_at);
CREATE INDEX ix_quiz_attempts_user ON learning.quiz_attempts (user_id, started_at DESC);
CREATE INDEX ix_quiz_attempts_quiz ON learning.quiz_attempts (quiz_id);

-- Per-question answers: the core assessment fact. Denormalised (user, concept,
-- difficulty, kind) so analytics never joins back to the bank.
CREATE TABLE learning.question_responses (
    id                 uuid NOT NULL DEFAULT util.uuid_v7(),
    attempt_id         uuid NOT NULL,
    attempt_started_at timestamptz NOT NULL,
    position           smallint NOT NULL CHECK (position >= 0),
    user_id            uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    question_id        uuid REFERENCES curriculum.questions (id) ON DELETE SET NULL,
    concept_id         uuid REFERENCES curriculum.concepts (id) ON DELETE SET NULL,
    kind               ref.question_kind NOT NULL,
    difficulty         ref.difficulty_level NOT NULL,
    response           jsonb NOT NULL,
    is_correct         boolean,
    score              numeric(6,2) NOT NULL DEFAULT 0 CHECK (score >= 0),
    max_score          numeric(6,2) NOT NULL DEFAULT 1 CHECK (max_score > 0),
    latency_ms         integer CHECK (latency_ms >= 0),
    hints_used         smallint NOT NULL DEFAULT 0 CHECK (hints_used >= 0),
    answered_at        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (id, attempt_started_at),
    CONSTRAINT uq_question_responses_position UNIQUE (attempt_id, attempt_started_at, position),
    CONSTRAINT fk_question_responses_attempt FOREIGN KEY (attempt_id, attempt_started_at)
        REFERENCES learning.quiz_attempts (id, started_at) ON DELETE CASCADE
) PARTITION BY RANGE (attempt_started_at);
CREATE INDEX ix_question_responses_user ON learning.question_responses (user_id, answered_at);
CREATE INDEX ix_question_responses_concept ON learning.question_responses (concept_id, answered_at);
CREATE INDEX ix_question_responses_question ON learning.question_responses (question_id) WHERE question_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- Coding lab
-- -----------------------------------------------------------------------------

CREATE TABLE learning.code_submissions (
    id             uuid NOT NULL DEFAULT util.uuid_v7(),
    submitted_at   timestamptz NOT NULL DEFAULT now(),
    user_id        uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    exercise_id    uuid REFERENCES curriculum.coding_exercises (id) ON DELETE SET NULL,
    challenge_id   uuid,                       -- FK added in 07_gamification.sql
    language       text NOT NULL DEFAULT 'python',
    code           text NOT NULL CHECK (octet_length(code) <= 262144),
    code_sha256    bytea NOT NULL CHECK (octet_length(code_sha256) = 32),
    status         ref.submission_status NOT NULL DEFAULT 'queued',
    tests_passed   smallint CHECK (tests_passed >= 0),
    tests_total    smallint CHECK (tests_total >= 0),
    runtime_ms     integer CHECK (runtime_ms >= 0),
    peak_memory_kb integer CHECK (peak_memory_kb >= 0),
    stdout         text CHECK (octet_length(stdout) <= 65536),
    stderr         text CHECK (octet_length(stderr) <= 65536),
    review_md      text,
    review_model   text,
    xp_awarded     integer NOT NULL DEFAULT 0 CHECK (xp_awarded >= 0),
    finished_at    timestamptz,
    PRIMARY KEY (id, submitted_at),
    CONSTRAINT ck_code_submissions_tests CHECK (tests_passed IS NULL OR tests_total IS NULL OR tests_passed <= tests_total)
) PARTITION BY RANGE (submitted_at);
CREATE INDEX ix_code_submissions_user ON learning.code_submissions (user_id, submitted_at DESC);
CREATE INDEX ix_code_submissions_exercise ON learning.code_submissions (exercise_id, status, submitted_at)
    WHERE exercise_id IS NOT NULL;

-- Survives submission retention: the best passing solution per exercise.
CREATE TABLE learning.exercise_completions (
    user_id            uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    exercise_id        uuid NOT NULL REFERENCES curriculum.coding_exercises (id) ON DELETE CASCADE,
    first_passed_at    timestamptz NOT NULL,
    best_submission_id uuid NOT NULL,
    best_code          text NOT NULL,
    best_runtime_ms    integer,
    attempts           integer NOT NULL DEFAULT 1 CHECK (attempts > 0),
    updated_at         timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, exercise_id)
);
CREATE INDEX ix_exercise_completions_exercise ON learning.exercise_completions (exercise_id);

-- -----------------------------------------------------------------------------
-- Flashcards (SM-2 spaced repetition)
-- -----------------------------------------------------------------------------

CREATE TABLE learning.flashcards (
    id               uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    user_id          uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    concept_id       uuid REFERENCES curriculum.concepts (id) ON DELETE SET NULL,
    deck             text NOT NULL DEFAULT 'core' CHECK (char_length(deck) BETWEEN 1 AND 80),
    front            text NOT NULL CHECK (char_length(front) <= 4000),
    back             text NOT NULL CHECK (char_length(back) <= 8000),
    locale           text NOT NULL DEFAULT 'en' REFERENCES ref.languages (code),
    source           text NOT NULL DEFAULT 'generated' CHECK (source IN ('generated', 'manual', 'system', 'artifact')),
    ease_factor      numeric(4,2) NOT NULL DEFAULT 2.50 CHECK (ease_factor >= 1.30),
    interval_days    integer NOT NULL DEFAULT 0 CHECK (interval_days >= 0),
    repetitions      integer NOT NULL DEFAULT 0 CHECK (repetitions >= 0),
    lapses           integer NOT NULL DEFAULT 0 CHECK (lapses >= 0),
    next_review_at   timestamptz NOT NULL DEFAULT now(),
    last_reviewed_at timestamptz,
    suspended        boolean NOT NULL DEFAULT false,
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now()
) WITH (fillfactor = 85);
CREATE INDEX ix_flashcards_due ON learning.flashcards (user_id, next_review_at) WHERE NOT suspended;

CREATE TABLE learning.flashcard_reviews (
    id              uuid NOT NULL DEFAULT util.uuid_v7(),
    reviewed_at     timestamptz NOT NULL DEFAULT now(),
    flashcard_id    uuid NOT NULL REFERENCES learning.flashcards (id) ON DELETE CASCADE,
    user_id         uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    rating          smallint NOT NULL CHECK (rating BETWEEN 0 AND 5),
    ease_before     numeric(4,2) NOT NULL,
    ease_after      numeric(4,2) NOT NULL,
    interval_before integer NOT NULL,
    interval_after  integer NOT NULL,
    response_ms     integer CHECK (response_ms >= 0),
    PRIMARY KEY (id, reviewed_at)
) PARTITION BY RANGE (reviewed_at);
CREATE INDEX ix_flashcard_reviews_user ON learning.flashcard_reviews (user_id, reviewed_at);
CREATE INDEX ix_flashcard_reviews_card ON learning.flashcard_reviews (flashcard_id);

-- -----------------------------------------------------------------------------
-- Study plans
-- -----------------------------------------------------------------------------

CREATE TABLE learning.study_plans (
    id             uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    user_id        uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    enrollment_id  uuid REFERENCES learning.enrollments (id) ON DELETE SET NULL,
    title          text NOT NULL,
    goal           text NOT NULL,
    status         text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived', 'superseded')),
    starts_on      date NOT NULL,
    ends_on        date,
    weekly_minutes integer CHECK (weekly_minutes BETWEEN 0 AND 10080),
    generated_by   text NOT NULL DEFAULT 'planner' CHECK (generated_by IN ('planner', 'user', 'instructor')),
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_study_plans_dates CHECK (ends_on IS NULL OR ends_on >= starts_on)
);
CREATE INDEX ix_study_plans_user ON learning.study_plans (user_id, status);

CREATE TABLE learning.study_plan_items (
    id                uuid PRIMARY KEY DEFAULT util.uuid_v7(),
    plan_id           uuid NOT NULL REFERENCES learning.study_plans (id) ON DELETE CASCADE,
    position          integer NOT NULL CHECK (position >= 0),
    scheduled_for     date NOT NULL,
    title             text NOT NULL,
    lesson_id         uuid REFERENCES curriculum.lessons (id) ON DELETE SET NULL,
    concept_id        uuid REFERENCES curriculum.concepts (id) ON DELETE SET NULL,
    assessment_id     uuid REFERENCES curriculum.assessments (id) ON DELETE SET NULL,
    exercise_id       uuid REFERENCES curriculum.coding_exercises (id) ON DELETE SET NULL,
    asset_id          uuid REFERENCES knowledge.assets (id) ON DELETE SET NULL,
    estimated_minutes integer CHECK (estimated_minutes > 0),
    status            text NOT NULL DEFAULT 'planned' CHECK (status IN ('planned', 'done', 'skipped', 'rescheduled')),
    completed_at      timestamptz,
    CONSTRAINT uq_study_plan_items_position UNIQUE (plan_id, position) DEFERRABLE INITIALLY IMMEDIATE,
    CONSTRAINT ck_study_plan_items_target CHECK (
        num_nonnulls(lesson_id, concept_id, assessment_id, exercise_id, asset_id) <= 1)
);
CREATE INDEX ix_study_plan_items_schedule ON learning.study_plan_items (plan_id, scheduled_for);

-- -----------------------------------------------------------------------------
-- Recommendations served to learners, with outcome. Feeds the "resource
-- effectiveness" analytics and offline evaluation of the recommender.
-- -----------------------------------------------------------------------------

CREATE TABLE learning.recommendations (
    id            uuid NOT NULL DEFAULT util.uuid_v7(),
    generated_at  timestamptz NOT NULL DEFAULT now(),
    user_id       uuid NOT NULL REFERENCES identity.users (id) ON DELETE CASCADE,
    target_type   text NOT NULL CHECK (target_type IN ('lesson', 'concept', 'asset', 'assessment', 'exercise', 'path', 'challenge')),
    target_id     uuid NOT NULL,
    concept_id    uuid,
    reason        text NOT NULL CHECK (reason IN ('weak_prerequisite', 'next_in_path', 'review_due', 'career_goal',
                      'style_match', 'remediation', 'popular', 'challenge')),
    score         real NOT NULL,
    rank          smallint NOT NULL CHECK (rank >= 1),
    surface       text NOT NULL CHECK (surface IN ('dashboard', 'chat', 'post_quiz', 'email', 'study_plan')),
    model_version text NOT NULL,
    served_at     timestamptz,
    clicked_at    timestamptz,
    completed_at  timestamptz,
    dismissed_at  timestamptz,
    PRIMARY KEY (id, generated_at)
) PARTITION BY RANGE (generated_at);
CREATE INDEX ix_recommendations_user ON learning.recommendations (user_id, generated_at DESC);
CREATE INDEX ix_recommendations_target ON learning.recommendations (target_type, target_id, generated_at);
