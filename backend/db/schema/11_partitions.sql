-- =============================================================================
-- 12 partitions and retention registry
-- The registry is the executable form of docs/database/data-retention.md.
-- drop_order: tables that reference a partitioned parent drop first
-- (citations/feedback before messages, responses before attempts).
-- archive_before_drop = true detaches only; the archiver exports the detached
-- table to Parquet in object storage and then drops it.
-- =============================================================================

-- Hash partitions for current mastery (no retention; spreads vacuum and index size).
DO $$
BEGIN
    FOR i IN 0 .. 15 LOOP
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS learning.concept_mastery_h%s PARTITION OF learning.concept_mastery
             FOR VALUES WITH (MODULUS 16, REMAINDER %s)', lpad(i::text, 2, '0'), i);
    END LOOP;
END $$;

INSERT INTO util.partition_registry (parent_table, grain, premake, retention, drop_order, archive_before_drop, notes) VALUES
    -- chat: 24 months rolling (Security-Compliance.md §11.5)
    ('chat.message_citations',            'month', 3, interval '24 months', 10, false, 'co-partitioned with chat.messages'),
    ('chat.message_feedback',             'month', 3, interval '24 months', 10, false, 'co-partitioned with chat.messages'),
    ('chat.messages',                     'month', 3, interval '24 months', 20, false, 'emptied conversations purged by util.purge_expired_rows'),
    -- learning evidence
    ('learning.question_responses',       'month', 3, interval '25 months', 10, true,  'co-partitioned with quiz_attempts'),
    ('learning.quiz_attempts',            'month', 3, interval '25 months', 20, true,  NULL),
    ('learning.mastery_events',           'month', 3, interval '25 months', 20, true,  'velocity history kept in analytics facts'),
    ('learning.code_submissions',         'month', 3, interval '12 months', 20, false, 'best solution kept in exercise_completions'),
    ('learning.flashcard_reviews',        'month', 3, interval '13 months', 20, false, 'card state kept on learning.flashcards'),
    ('learning.recommendations',          'month', 3, interval '13 months', 20, true,  NULL),
    -- gamification
    ('game.xp_ledger',                    'month', 3, interval '25 months', 20, false, 'compacted into game.xp_monthly_rollup first'),
    ('game.daily_activity',               'month', 3, interval '25 months', 20, false, NULL),
    -- activity
    ('activity.events',                   'day',  14, interval '90 days',   20, true,  'full history in the warehouse'),
    ('activity.sessions',                 'month', 3, interval '13 months', 20, true,  NULL),
    ('activity.llm_invocations',          'month', 3, interval '13 months', 20, true,  NULL),
    -- analytics facts
    ('analytics.fact_user_daily',         'month', 3, interval '25 months', 20, false, 'user-level ceiling; aggregates kept'),
    ('analytics.fact_concept_mastery_daily', 'month', 3, interval '25 months', 20, false, 'user-level ceiling; aggregates kept'),
    -- audit: AL-5 in Security-Compliance.md (admin actions 2 years, other security events 1 year)
    ('audit.row_changes',                 'month', 3, interval '2 years',   30, true,  'governed-table changes are admin actions'),
    ('audit.data_access_log',             'month', 3, interval '2 years',   30, true,  'staff access is an admin action'),
    ('audit.security_events',             'month', 3, interval '1 year',    30, true,  NULL);

-- Initial partitions: previous period through `premake` periods ahead, plus a
-- default partition on each parent.
SELECT * FROM util.run_partition_maintenance();

SELECT util.ensure_default_partition(parent_table) FROM util.partition_registry;

-- CONCURRENTLY needs a populated view, so do the first refresh here.
REFRESH MATERIALIZED VIEW analytics.mv_concept_difficulty_30d;
REFRESH MATERIALIZED VIEW analytics.mv_content_engagement_30d;

-- Schedule daily maintenance when pg_cron is available (Azure: enable the
-- extension and set cron.database_name to this database).
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'pg_cron') THEN
        BEGIN
            CREATE EXTENSION IF NOT EXISTS pg_cron;
            PERFORM cron.schedule('ai-mentor-partition-maintenance', '15 2 * * *',
                                  'SELECT * FROM util.run_partition_maintenance()');
            PERFORM cron.schedule('ai-mentor-refresh-analytics-mvs', '30 3 * * *',
                                  'REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_concept_difficulty_30d;
                                   REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_content_engagement_30d;');
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'pg_cron not scheduled (%). Run util.run_partition_maintenance() from an external scheduler.', SQLERRM;
        END;
    END IF;
END $$;
