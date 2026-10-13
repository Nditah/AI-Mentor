-- =============================================================================
-- AI Mentor target schema — 00 bootstrap
-- Extensions, schemas, shared enum types, and utility functions.
-- Requires PostgreSQL 16+. On Azure Database for PostgreSQL Flexible Server,
-- allow-list pgcrypto, citext, pg_trgm, ltree (and pg_cron for maintenance)
-- in the `azure.extensions` server parameter first.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS ltree;

-- Group roles (NOLOGIN); privileges are granted in 14_security.sql.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mentor_owner')    THEN CREATE ROLE mentor_owner NOLOGIN;    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mentor_app')      THEN CREATE ROLE mentor_app NOLOGIN;      END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mentor_worker')   THEN CREATE ROLE mentor_worker NOLOGIN;   END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mentor_readonly') THEN CREATE ROLE mentor_readonly NOLOGIN; END IF;
END $$;

CREATE SCHEMA IF NOT EXISTS util;        -- helper functions, partition registry
CREATE SCHEMA IF NOT EXISTS ref;         -- reference data and shared enum types
CREATE SCHEMA IF NOT EXISTS identity;    -- users, profiles, preferences, billing, consent
CREATE SCHEMA IF NOT EXISTS curriculum;  -- taxonomy, concept graph, paths, lessons, question bank
CREATE SCHEMA IF NOT EXISTS knowledge;   -- curated and personal knowledge assets, chunks, workflow
CREATE SCHEMA IF NOT EXISTS vector;      -- embedding models, Qdrant collections, sync outbox
CREATE SCHEMA IF NOT EXISTS learning;    -- enrolments, progress, mastery, quizzes, code, flashcards
CREATE SCHEMA IF NOT EXISTS chat;        -- conversations, messages, citations, feedback
CREATE SCHEMA IF NOT EXISTS game;        -- XP ledger, stats, badges, titles, challenges, leaderboards
CREATE SCHEMA IF NOT EXISTS activity;    -- sessions, product events, LLM invocations
CREATE SCHEMA IF NOT EXISTS analytics;   -- dimensions, daily facts, aggregates, reports
CREATE SCHEMA IF NOT EXISTS audit;       -- row-change log, security events, data-access log

-- -----------------------------------------------------------------------------
-- Shared enum types. Enums are used for small, closed sets that the code
-- branches on. Admin-managed vocabularies (badges, tags, accents, countries)
-- are lookup tables instead, so they can change without a migration.
-- -----------------------------------------------------------------------------

CREATE TYPE ref.user_role            AS ENUM ('student', 'instructor', 'admin');
CREATE TYPE ref.account_status       AS ENUM ('active', 'suspended', 'pending_deletion', 'deleted');
CREATE TYPE ref.learner_persona      AS ENUM ('student', 'professional', 'researcher', 'entrepreneur',
                                              'data_analyst', 'robotics_engineer', 'career_switcher', 'enthusiast');
CREATE TYPE ref.difficulty_level     AS ENUM ('beginner', 'intermediate', 'advanced', 'expert', 'researcher', 'phd');
CREATE TYPE ref.skill_band           AS ENUM ('none', 'beginner', 'intermediate', 'advanced', 'expert');
CREATE TYPE ref.teaching_style       AS ENUM ('simple', 'storytelling', 'visual', 'mathematical',
                                              'research', 'industry', 'mixed');
CREATE TYPE ref.tutor_personality    AS ENUM ('friendly', 'professional', 'academic', 'motivational',
                                              'strict_coach', 'socratic');
CREATE TYPE ref.learning_pace        AS ENUM ('slow', 'moderate', 'fast', 'intensive');
CREATE TYPE ref.math_depth           AS ENUM ('none', 'light', 'moderate', 'formal', 'full_proofs');
CREATE TYPE ref.breadth_preference   AS ENUM ('survey', 'specialist', 'balanced');
CREATE TYPE ref.age_appearance       AS ENUM ('young_adult', 'adult', 'senior_expert');
CREATE TYPE ref.gender_presentation  AS ENUM ('male', 'female', 'neutral');
CREATE TYPE ref.subscription_tier    AS ENUM ('free', 'pro', 'research');
CREATE TYPE ref.subscription_status  AS ENUM ('trialing', 'active', 'past_due', 'canceled', 'incomplete', 'unpaid');

CREATE TYPE ref.content_status       AS ENUM ('draft', 'review', 'approved', 'published', 'archived');
CREATE TYPE ref.concept_relation     AS ENUM ('prerequisite', 'related', 'extends', 'part_of', 'applies_to');
CREATE TYPE ref.question_kind        AS ENUM ('mcq', 'multi_select', 'true_false', 'fill_blank', 'short_answer',
                                              'coding', 'derivation', 'research_critique');
CREATE TYPE ref.asset_kind           AS ENUM ('pdf', 'research_paper', 'book', 'lecture_notes', 'slides',
                                              'document', 'markdown', 'website', 'video', 'repository',
                                              'code_sample', 'dataset', 'image', 'audio');
CREATE TYPE ref.asset_scope          AS ENUM ('curated', 'personal');
CREATE TYPE ref.ingestion_stage      AS ENUM ('parse', 'extract_metadata', 'chunk', 'embed', 'index', 'link');
CREATE TYPE ref.job_status           AS ENUM ('queued', 'running', 'succeeded', 'failed', 'cancelled');
CREATE TYPE ref.artifact_kind        AS ENUM ('lesson_notes', 'flashcards', 'quiz', 'coding_exercise',
                                              'project_idea', 'study_guide', 'concept_map', 'translation');

CREATE TYPE ref.progress_status      AS ENUM ('not_started', 'in_progress', 'completed');
CREATE TYPE ref.submission_status    AS ENUM ('queued', 'running', 'passed', 'failed', 'error', 'timeout', 'rejected');
CREATE TYPE ref.agent_kind           AS ENUM ('tutor', 'quiz', 'planner', 'coding', 'research', 'career', 'system');
CREATE TYPE ref.message_role         AS ENUM ('system', 'user', 'assistant', 'tool');

CREATE TYPE ref.xp_source            AS ENUM ('lesson', 'quiz', 'code', 'flashcard', 'challenge', 'badge',
                                              'streak', 'project', 'research', 'community', 'admin_adjustment',
                                              'reversal');
CREATE TYPE ref.challenge_kind       AS ENUM ('quiz', 'coding', 'research', 'debugging', 'robotics', 'lesson');
CREATE TYPE ref.leaderboard_scope    AS ENUM ('global', 'country', 'region');
CREATE TYPE ref.leaderboard_period   AS ENUM ('daily', 'weekly', 'monthly', 'all_time');
CREATE TYPE ref.leaderboard_metric   AS ENUM ('xp', 'challenges', 'quiz_performance', 'projects',
                                              'research', 'community', 'composite');

-- -----------------------------------------------------------------------------
-- Utility functions
-- -----------------------------------------------------------------------------

-- Time-ordered UUIDs keep B-tree inserts append-mostly (unlike random v4).
-- On PostgreSQL 18+, replace the body with `SELECT uuidv7()`.
CREATE OR REPLACE FUNCTION util.uuid_v7() RETURNS uuid
LANGUAGE plpgsql VOLATILE PARALLEL SAFE AS $$
DECLARE
    v_bytes bytea;
BEGIN
    v_bytes := substring(int8send((extract(epoch FROM clock_timestamp()) * 1000)::bigint) FROM 3)
               || gen_random_bytes(10);
    v_bytes := set_byte(v_bytes, 6, (b'0111' || get_byte(v_bytes, 6)::bit(4))::bit(8)::int);
    v_bytes := set_byte(v_bytes, 8, (b'10' || get_byte(v_bytes, 8)::bit(6))::bit(8)::int);
    RETURN encode(v_bytes, 'hex')::uuid;
END $$;

CREATE OR REPLACE FUNCTION util.set_updated_at() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END $$;

-- Request context. The API sets these with SET LOCAL at the start of each
-- transaction; RLS policies and audit triggers read them.
CREATE OR REPLACE FUNCTION util.current_user_id() RETURNS uuid
LANGUAGE sql STABLE PARALLEL SAFE AS $$
    SELECT nullif(current_setting('app.current_user_id', true), '')::uuid
$$;

CREATE OR REPLACE FUNCTION util.current_user_role() RETURNS text
LANGUAGE sql STABLE PARALLEL SAFE AS $$
    SELECT nullif(current_setting('app.user_role', true), '')
$$;

CREATE OR REPLACE FUNCTION util.is_system_context() RETURNS boolean
LANGUAGE sql STABLE PARALLEL SAFE AS $$
    SELECT coalesce(current_setting('app.context', true), '') = 'system'
$$;

-- -----------------------------------------------------------------------------
-- Partition management. Range partitions are named <table>_pYYYY_MM (month)
-- or <table>_pYYYY_MM_DD (day). Bounds are always UTC.
-- -----------------------------------------------------------------------------

CREATE TABLE util.partition_registry (
    parent_table      regclass PRIMARY KEY,
    grain             text     NOT NULL CHECK (grain IN ('day', 'month')),
    premake           integer  NOT NULL DEFAULT 3 CHECK (premake BETWEEN 1 AND 400),
    retention         interval,                       -- NULL keeps partitions forever
    drop_order        smallint NOT NULL DEFAULT 100,  -- referencing tables drop first
    archive_before_drop boolean NOT NULL DEFAULT false,
    notes             text
);
COMMENT ON TABLE util.partition_registry IS
    'Drives util.run_partition_maintenance(): partitions created ahead and dropped after retention.';

CREATE OR REPLACE FUNCTION util.partition_key_type(p_parent regclass) RETURNS text
LANGUAGE sql STABLE AS $$
    SELECT format_type(a.atttypid, a.atttypmod)
    FROM pg_partitioned_table pt
    JOIN pg_attribute a ON a.attrelid = pt.partrelid AND a.attnum = pt.partattrs[0]
    WHERE pt.partrelid = p_parent
$$;

CREATE OR REPLACE FUNCTION util.create_time_partitions(
    p_parent  regclass,
    p_grain   text,
    p_from    date,
    p_periods integer
) RETURNS integer
LANGUAGE plpgsql AS $$
DECLARE
    v_schema  text;
    v_table   text;
    v_keytype text := util.partition_key_type(p_parent);
    v_step    interval;
    v_start   date;
    v_end     date;
    v_name    text;
    v_lo      text;
    v_hi      text;
    v_created integer := 0;
BEGIN
    IF p_grain NOT IN ('day', 'month') THEN
        RAISE EXCEPTION 'grain must be day or month, got %', p_grain;
    END IF;
    IF v_keytype IS NULL THEN
        RAISE EXCEPTION '% is not a partitioned table', p_parent;
    END IF;

    SELECT n.nspname, c.relname INTO v_schema, v_table
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.oid = p_parent;

    v_step  := ('1 ' || p_grain)::interval;
    v_start := date_trunc(p_grain, p_from)::date;

    FOR i IN 1 .. p_periods LOOP
        v_end  := (v_start + v_step)::date;
        v_name := v_table || '_p' || to_char(v_start, CASE p_grain WHEN 'month' THEN 'YYYY_MM' ELSE 'YYYY_MM_DD' END);
        IF v_keytype = 'timestamp with time zone' THEN
            v_lo := v_start::text || ' 00:00:00+00';
            v_hi := v_end::text   || ' 00:00:00+00';
        ELSE
            v_lo := v_start::text;
            v_hi := v_end::text;
        END IF;

        IF to_regclass(format('%I.%I', v_schema, v_name)) IS NULL THEN
            EXECUTE format('CREATE TABLE %I.%I PARTITION OF %s FOR VALUES FROM (%L) TO (%L)',
                           v_schema, v_name, p_parent, v_lo, v_hi);
            v_created := v_created + 1;
        END IF;
        v_start := v_end;
    END LOOP;
    RETURN v_created;
END $$;

-- The default partition catches rows outside any range so writes never fail.
-- It should stay empty; util.v_partition_health reports when it does not.
CREATE OR REPLACE FUNCTION util.ensure_default_partition(p_parent regclass) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
    v_schema text;
    v_table  text;
BEGIN
    SELECT n.nspname, c.relname INTO v_schema, v_table
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.oid = p_parent;
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I.%I PARTITION OF %s DEFAULT',
                   v_schema, v_table || '_default', p_parent);
END $$;

-- Detaches and drops range partitions whose upper bound is <= p_before.
CREATE OR REPLACE FUNCTION util.drop_time_partitions_before(
    p_parent      regclass,
    p_before      date,
    p_detach_only boolean DEFAULT false
) RETURNS SETOF text
LANGUAGE plpgsql AS $$
DECLARE
    r       record;
    v_upper text;
BEGIN
    FOR r IN
        SELECT c.oid::regclass AS part, pg_get_expr(c.relpartbound, c.oid) AS bound
        FROM pg_inherits i
        JOIN pg_class c ON c.oid = i.inhrelid
        WHERE i.inhparent = p_parent
        ORDER BY c.relname
    LOOP
        CONTINUE WHEN r.bound = 'DEFAULT';
        v_upper := (regexp_match(r.bound, 'TO \(''([^'']+)''\)'))[1];
        CONTINUE WHEN v_upper IS NULL;
        IF v_upper::timestamptz <= (p_before::text || ' 00:00:00+00')::timestamptz THEN
            EXECUTE format('ALTER TABLE %s DETACH PARTITION %s', p_parent, r.part);
            IF NOT p_detach_only THEN
                EXECUTE format('DROP TABLE %s', r.part);
            END IF;
            RETURN NEXT r.part::text;
        END IF;
    END LOOP;
END $$;

-- Creates future partitions and enforces retention for every registered table.
-- Schedule daily (pg_cron, Azure Automation, or a Kubernetes CronJob).
CREATE OR REPLACE FUNCTION util.run_partition_maintenance(p_today date DEFAULT current_date)
RETURNS TABLE (parent_table regclass, created integer, dropped text[])
LANGUAGE plpgsql AS $$
DECLARE
    r       util.partition_registry%ROWTYPE;
    v_cut   date;
BEGIN
    FOR r IN SELECT pr.* FROM util.partition_registry pr ORDER BY pr.drop_order, pr.parent_table::text LOOP
        parent_table := r.parent_table;
        created := util.create_time_partitions(
            r.parent_table, r.grain,
            (date_trunc(r.grain, p_today) - ('1 ' || r.grain)::interval)::date,
            r.premake + 2);
        dropped := '{}';
        IF r.retention IS NOT NULL THEN
            v_cut := date_trunc(r.grain, p_today - r.retention)::date;
            SELECT coalesce(array_agg(d), '{}') INTO dropped
            FROM util.drop_time_partitions_before(r.parent_table, v_cut, r.archive_before_drop) AS d;
        END IF;
        RETURN NEXT;
    END LOOP;
END $$;

CREATE OR REPLACE VIEW util.v_partition_health AS
SELECT
    reg.parent_table,
    reg.grain,
    reg.retention,
    count(c.oid) FILTER (WHERE pg_get_expr(c.relpartbound, c.oid) <> 'DEFAULT') AS range_partitions,
    max((regexp_match(pg_get_expr(c.relpartbound, c.oid), 'TO \(''([^'']+)''\)'))[1]::timestamptz)
        AS covered_until,
    max(c.reltuples) FILTER (WHERE pg_get_expr(c.relpartbound, c.oid) = 'DEFAULT') AS default_rows_estimate
FROM util.partition_registry reg
LEFT JOIN pg_inherits i ON i.inhparent = reg.parent_table
LEFT JOIN pg_class c ON c.oid = i.inhrelid
GROUP BY reg.parent_table, reg.grain, reg.retention;
COMMENT ON VIEW util.v_partition_health IS
    'Alert when covered_until < now() + 1 grain, or default_rows_estimate > 0.';
