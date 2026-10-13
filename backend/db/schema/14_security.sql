-- =============================================================================
-- 11 roles, privileges, and row-level security
--
-- Group roles (NOLOGIN). Real login users are granted membership:
--   mentor_owner     owns all objects; used only by migrations
--   mentor_app       the API: DML on application tables, no DDL, no audit writes
--   mentor_worker    background jobs (ingestion, rollups, retention, outbox)
--   mentor_readonly  BI / analysts: analytics schema plus curriculum metadata
--
-- RLS is defence in depth for learner-private data (chat, personal documents,
-- research analyses). The API sets, per transaction:
--   SET LOCAL app.current_user_id = '<uuid>'; SET LOCAL app.user_role = 'student';
-- Workers set SET LOCAL app.context = 'system' instead.
-- =============================================================================

-- The group roles themselves are created in 00_bootstrap.sql.

DO $$
DECLARE
    s text;
    app_schemas text[] := ARRAY['ref', 'identity', 'curriculum', 'knowledge', 'vector',
                                'learning', 'chat', 'game', 'activity', 'analytics'];
BEGIN
    FOREACH s IN ARRAY app_schemas || ARRAY['util', 'audit'] LOOP
        EXECUTE format('GRANT USAGE ON SCHEMA %I TO mentor_app, mentor_worker', s);
    END LOOP;

    FOREACH s IN ARRAY app_schemas LOOP
        EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA %I TO mentor_app, mentor_worker', s);
        EXECUTE format('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA %I TO mentor_app, mentor_worker', s);
        EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE mentor_owner IN SCHEMA %I
                        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mentor_app, mentor_worker', s);
        EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE mentor_owner IN SCHEMA %I
                        GRANT USAGE, SELECT ON SEQUENCES TO mentor_app, mentor_worker', s);
    END LOOP;

    FOREACH s IN ARRAY ARRAY['ref', 'curriculum', 'analytics'] LOOP
        EXECUTE format('GRANT USAGE ON SCHEMA %I TO mentor_readonly', s);
        EXECUTE format('GRANT SELECT ON ALL TABLES IN SCHEMA %I TO mentor_readonly', s);
        EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE mentor_owner IN SCHEMA %I
                        GRANT SELECT ON TABLES TO mentor_readonly', s);
    END LOOP;
END $$;

-- Reference catalogs are read-only for the API.
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ref FROM mentor_app;

-- Audit: the API may append security and data-access events, never edit them.
GRANT INSERT ON audit.security_events, audit.data_access_log TO mentor_app, mentor_worker;
GRANT SELECT ON ALL TABLES IN SCHEMA audit TO mentor_worker;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA util TO mentor_app, mentor_worker;
REVOKE ALL ON FUNCTION audit.capture_row_change() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION identity.erase_user(uuid) TO mentor_worker;

-- Partition maintenance runs as the owner (DDL), never as the app.
REVOKE EXECUTE ON FUNCTION util.run_partition_maintenance(date),
                           util.create_time_partitions(regclass, text, date, integer),
                           util.drop_time_partitions_before(regclass, date, boolean)
    FROM PUBLIC, mentor_app, mentor_worker;
REVOKE EXECUTE ON FUNCTION util.purge_expired_rows(integer) FROM PUBLIC, mentor_app;
GRANT EXECUTE ON FUNCTION util.purge_expired_rows(integer), game.compact_xp_ledger(date) TO mentor_worker;

-- -----------------------------------------------------------------------------
-- Row-level security
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION util.can_access_user_row(p_owner uuid) RETURNS boolean
LANGUAGE sql STABLE PARALLEL SAFE AS $$
    SELECT util.is_system_context() OR p_owner = util.current_user_id()
$$;

ALTER TABLE chat.conversations ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_conversations_owner ON chat.conversations
    USING (util.can_access_user_row(user_id))
    WITH CHECK (util.can_access_user_row(user_id));

ALTER TABLE chat.messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_messages_owner ON chat.messages
    USING (util.can_access_user_row(user_id))
    WITH CHECK (util.can_access_user_row(user_id));

ALTER TABLE chat.message_feedback ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_message_feedback_owner ON chat.message_feedback
    USING (util.can_access_user_row(user_id))
    WITH CHECK (util.can_access_user_row(user_id));

-- Curated assets are readable by everyone once published; staff see all
-- curated assets; personal assets only by their owner.
ALTER TABLE knowledge.assets ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_assets_read ON knowledge.assets FOR SELECT
    USING (
        (scope = 'curated' AND (status = 'published' OR util.current_user_role() IN ('instructor', 'admin')))
        OR util.can_access_user_row(owner_user_id));
CREATE POLICY p_assets_write_personal ON knowledge.assets FOR ALL
    USING (scope = 'personal' AND util.can_access_user_row(owner_user_id))
    WITH CHECK (scope = 'personal' AND util.can_access_user_row(owner_user_id));
CREATE POLICY p_assets_write_curated ON knowledge.assets FOR ALL
    USING (scope = 'curated' AND (util.current_user_role() IN ('instructor', 'admin') OR util.is_system_context()))
    WITH CHECK (scope = 'curated' AND (util.current_user_role() IN ('instructor', 'admin') OR util.is_system_context()));

ALTER TABLE knowledge.chunks ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_chunks_read ON knowledge.chunks
    USING (owner_user_id IS NULL OR util.can_access_user_row(owner_user_id))
    WITH CHECK (owner_user_id IS NULL OR util.can_access_user_row(owner_user_id));

ALTER TABLE knowledge.document_analyses ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_document_analyses_owner ON knowledge.document_analyses
    USING (util.can_access_user_row(user_id))
    WITH CHECK (util.can_access_user_row(user_id));
