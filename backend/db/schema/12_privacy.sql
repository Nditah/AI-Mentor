-- =============================================================================
-- 12 privacy: right-to-erasure procedure
-- Deleting identity.users cascades through every table with a user FK.
-- This function also covers what FKs cannot: the FK-less event stream,
-- analytics facts, audit payloads, and blobs in object storage.
-- Returns the storage URIs the caller must delete from blob storage.
-- Vector points are removed by vector.sync_outbox (enqueued by cascade).
-- =============================================================================

CREATE OR REPLACE FUNCTION identity.erase_user(p_user_id uuid)
RETURNS TABLE (storage_uri text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $$
DECLARE
    v_asset_ids   uuid[];
    v_version_ids uuid[];
    v_file_ids    uuid[];
    v_uris        text[];
BEGIN
    IF NOT EXISTS (SELECT 1 FROM identity.users WHERE id = p_user_id) THEN
        RAISE EXCEPTION 'user % not found', p_user_id USING ERRCODE = 'no_data_found';
    END IF;
    PERFORM set_config('app.context', 'system', true);

    SELECT coalesce(array_agg(DISTINCT a.id), '{}'),
           coalesce(array_agg(DISTINCT v.id) FILTER (WHERE v.id IS NOT NULL), '{}'),
           coalesce(array_agg(DISTINCT v.file_id) FILTER (WHERE v.file_id IS NOT NULL), '{}')
    INTO v_asset_ids, v_version_ids, v_file_ids
    FROM knowledge.assets a
    LEFT JOIN knowledge.asset_versions v ON v.asset_id = a.id
    WHERE a.owner_user_id = p_user_id;

    DELETE FROM activity.events                       WHERE user_id = p_user_id;
    DELETE FROM analytics.fact_user_daily             WHERE user_id = p_user_id;
    DELETE FROM analytics.fact_concept_mastery_daily  WHERE user_id = p_user_id;
    DELETE FROM analytics.dim_user                    WHERE user_id = p_user_id;

    -- Cascades: profile, preferences, conversations and messages, personal
    -- assets and chunks, progress, mastery, quizzes, XP, badges, sessions...
    DELETE FROM identity.users WHERE id = p_user_id;

    SELECT coalesce(array_agg(f.storage_uri), '{}') INTO v_uris
    FROM knowledge.files f
    WHERE f.id = ANY (v_file_ids)
      AND NOT EXISTS (SELECT 1 FROM knowledge.asset_versions v WHERE v.file_id = f.id);
    DELETE FROM knowledge.files f
    WHERE f.id = ANY (v_file_ids)
      AND NOT EXISTS (SELECT 1 FROM knowledge.asset_versions v WHERE v.file_id = f.id);

    -- Audit rows stay as evidence that changes happened, without the personal payload.
    -- This also catches the rows the cascade above just wrote.
    UPDATE audit.row_changes
    SET old_data = NULL, new_data = NULL
    WHERE (table_schema = 'identity'
           AND table_name IN ('users', 'user_profiles', 'learning_preferences')
           AND record_id = p_user_id::text)
       OR (table_schema = 'knowledge' AND table_name = 'assets'
           AND record_id = ANY (SELECT unnest(v_asset_ids)::text))
       OR (table_schema = 'knowledge' AND table_name = 'asset_versions'
           AND record_id = ANY (SELECT unnest(v_version_ids)::text));

    UPDATE audit.security_events
    SET ip_hmac = NULL, user_agent = NULL, details = '{}'
    WHERE user_id = p_user_id;

    INSERT INTO audit.security_events (event_type, severity, user_id, actor_user_id, details)
    VALUES ('account_erased', 'warning', p_user_id, util.current_user_id(),
            jsonb_build_object('files_released', cardinality(v_uris)));

    RETURN QUERY SELECT unnest(v_uris);
END $$;

REVOKE ALL ON FUNCTION identity.erase_user(uuid) FROM PUBLIC;

-- =============================================================================
-- Retention jobs for tables that are not partitioned. Partitioned tables are
-- handled by util.run_partition_maintenance() and the registry.
-- =============================================================================

-- Folds XP ledger months into game.xp_monthly_rollup. Idempotent: each run
-- recomputes whole months still present in the ledger. Run before partition
-- maintenance so a month is compacted before its partition is dropped.
CREATE OR REPLACE FUNCTION game.compact_xp_ledger(p_before date DEFAULT (current_date - interval '24 months')::date)
RETURNS bigint
LANGUAGE plpgsql AS $$
DECLARE
    v_rows bigint;
BEGIN
    INSERT INTO game.xp_monthly_rollup (user_id, month, source, amount, events)
    SELECT user_id, date_trunc('month', local_date)::date, source, sum(amount), count(*)
    FROM game.xp_ledger
    WHERE local_date < date_trunc('month', p_before)::date
    GROUP BY user_id, date_trunc('month', local_date)::date, source
    ON CONFLICT (user_id, month, source)
    DO UPDATE SET amount = EXCLUDED.amount, events = EXCLUDED.events;
    GET DIAGNOSTICS v_rows = ROW_COUNT;
    RETURN v_rows;
END $$;

-- Deletes expired rows in bounded batches to avoid long locks and WAL spikes.
-- Call repeatedly (e.g. every 10 minutes) until it returns 0.
CREATE OR REPLACE FUNCTION util.purge_expired_rows(p_batch integer DEFAULT 5000)
RETURNS TABLE (table_name text, deleted bigint)
LANGUAGE plpgsql AS $$
DECLARE
    v_count bigint;
BEGIN
    PERFORM set_config('app.context', 'system', true);

    table_name := 'chat.conversations (soft-deleted > 30 days)';
    DELETE FROM chat.conversations WHERE id IN (
        SELECT id FROM chat.conversations
        WHERE deleted_at < now() - interval '30 days' LIMIT p_batch);
    GET DIAGNOSTICS v_count = ROW_COUNT; deleted := v_count; RETURN NEXT;

    table_name := 'chat.conversations (no messages for 24 months)';
    DELETE FROM chat.conversations WHERE id IN (
        SELECT id FROM chat.conversations
        WHERE coalesce(last_message_at, created_at) < now() - interval '24 months' LIMIT p_batch);
    GET DIAGNOSTICS v_count = ROW_COUNT; deleted := v_count; RETURN NEXT;

    table_name := 'knowledge.assets (personal, archived > 30 days)';
    DELETE FROM knowledge.assets WHERE id IN (
        SELECT id FROM knowledge.assets
        WHERE scope = 'personal' AND archived_at < now() - interval '30 days' LIMIT p_batch);
    GET DIAGNOSTICS v_count = ROW_COUNT; deleted := v_count; RETURN NEXT;

    table_name := 'learning.quizzes (> 25 months)';
    DELETE FROM learning.quizzes WHERE id IN (
        SELECT id FROM learning.quizzes
        WHERE created_at < now() - interval '25 months' LIMIT p_batch);
    GET DIAGNOSTICS v_count = ROW_COUNT; deleted := v_count; RETURN NEXT;

    table_name := 'analytics.learner_reports (> 25 months)';
    DELETE FROM analytics.learner_reports WHERE id IN (
        SELECT id FROM analytics.learner_reports
        WHERE generated_at < now() - interval '25 months' LIMIT p_batch);
    GET DIAGNOSTICS v_count = ROW_COUNT; deleted := v_count; RETURN NEXT;

    table_name := 'game.leaderboards (superseded > 1 day, closed > 25 months)';
    DELETE FROM game.leaderboards WHERE id IN (
        SELECT id FROM game.leaderboards
        WHERE (status = 'superseded' AND created_at < now() - interval '1 day')
           OR (status = 'closed' AND period_end < current_date - interval '25 months')
        LIMIT 50);   -- each board may cascade to many entries
    GET DIAGNOSTICS v_count = ROW_COUNT; deleted := v_count; RETURN NEXT;

    table_name := 'vector.sync_outbox (done > 7 days)';
    DELETE FROM vector.sync_outbox WHERE id IN (
        SELECT id FROM vector.sync_outbox
        WHERE status = 'done' AND processed_at < now() - interval '7 days' LIMIT p_batch);
    GET DIAGNOSTICS v_count = ROW_COUNT; deleted := v_count; RETURN NEXT;

    table_name := 'knowledge.ingestion_jobs (finished > 180 days)';
    DELETE FROM knowledge.ingestion_jobs WHERE id IN (
        SELECT id FROM knowledge.ingestion_jobs
        WHERE finished_at < now() - interval '180 days' LIMIT p_batch);
    GET DIAGNOSTICS v_count = ROW_COUNT; deleted := v_count; RETURN NEXT;

    table_name := 'identity.webhook_events (> 90 days)';
    DELETE FROM identity.webhook_events WHERE (provider, event_id) IN (
        SELECT provider, event_id FROM identity.webhook_events
        WHERE received_at < now() - interval '90 days' LIMIT p_batch);
    GET DIAGNOSTICS v_count = ROW_COUNT; deleted := v_count; RETURN NEXT;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
        PERFORM cron.schedule('ai-mentor-compact-xp', '0 2 * * *', 'SELECT game.compact_xp_ledger()');
        PERFORM cron.schedule('ai-mentor-purge-expired', '*/10 * * * *', 'SELECT * FROM util.purge_expired_rows()');
    END IF;
END $$;
