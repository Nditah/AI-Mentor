-- =============================================================================
-- 10 audit
--   row_changes      trigger-captured changes to governed tables (who, what, when)
--   security_events  application-written security log (sign-ins, role changes...)
--   data_access_log  staff access to a learner's personal data
-- All three are RANGE-partitioned monthly. The application role cannot write
-- row_changes directly; the trigger function is SECURITY DEFINER.
-- =============================================================================

CREATE TABLE audit.row_changes (
    id              bigint GENERATED ALWAYS AS IDENTITY,
    changed_at      timestamptz NOT NULL DEFAULT now(),
    txid            bigint NOT NULL DEFAULT txid_current(),
    actor_user_id   uuid,
    actor_role      text,
    request_id      text,
    client_ip       inet,
    operation       char(1) NOT NULL CHECK (operation IN ('I', 'U', 'D')),
    table_schema    text NOT NULL,
    table_name      text NOT NULL,
    record_id       text NOT NULL,
    old_data        jsonb,
    new_data        jsonb,                -- for updates, only the changed columns
    changed_columns text[],
    PRIMARY KEY (id, changed_at)
) PARTITION BY RANGE (changed_at);
CREATE INDEX ix_row_changes_record ON audit.row_changes (table_schema, table_name, record_id, changed_at DESC);
CREATE INDEX ix_row_changes_actor ON audit.row_changes (actor_user_id, changed_at DESC) WHERE actor_user_id IS NOT NULL;

-- Trigger arguments: first = comma-separated primary-key column(s);
-- the rest = columns to redact (large bodies or secrets).
-- Example: EXECUTE FUNCTION audit.capture_row_change('id', 'body_md')
CREATE OR REPLACE FUNCTION audit.capture_row_change() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $$
DECLARE
    v_pk_cols text[] := string_to_array(TG_ARGV[0], ',');
    v_redact  text[] := coalesce(TG_ARGV[1:], '{}') || ARRAY['updated_at', 'search', 'content_tsv'];
    v_old     jsonb;
    v_new     jsonb;
    v_changed text[];
    v_row     jsonb;
    v_record  text;
BEGIN
    -- Bulk backfills may skip auditing, but only when the login is a member of
    -- mentor_owner; the application role cannot switch auditing off.
    IF current_setting('app.skip_audit', true) = 'on'
       AND pg_has_role(session_user, 'mentor_owner', 'MEMBER') THEN
        RETURN NULL;
    END IF;

    IF TG_OP IN ('UPDATE', 'DELETE') THEN v_old := to_jsonb(OLD) - v_redact; END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') THEN v_new := to_jsonb(NEW) - v_redact; END IF;

    IF TG_OP = 'UPDATE' THEN
        SELECT array_agg(n.key ORDER BY n.key) INTO v_changed
        FROM jsonb_each(v_new) n
        WHERE n.value IS DISTINCT FROM v_old -> n.key;
        IF v_changed IS NULL THEN
            RETURN NULL;     -- nothing audited changed (e.g. only updated_at)
        END IF;
        SELECT jsonb_object_agg(n.key, n.value) INTO v_new
        FROM jsonb_each(v_new) n WHERE n.key = ANY (v_changed);
    END IF;

    v_row := CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE to_jsonb(NEW) END;
    SELECT string_agg(v_row ->> col, ',' ORDER BY ord) INTO v_record
    FROM unnest(v_pk_cols) WITH ORDINALITY AS t(col, ord);

    INSERT INTO audit.row_changes (actor_user_id, actor_role, request_id, client_ip, operation,
                                   table_schema, table_name, record_id, old_data, new_data, changed_columns)
    VALUES (nullif(current_setting('app.current_user_id', true), '')::uuid,
            nullif(current_setting('app.user_role', true), ''),
            nullif(current_setting('app.request_id', true), ''),
            nullif(current_setting('app.client_ip', true), '')::inet,
            left(TG_OP, 1), TG_TABLE_SCHEMA, TG_TABLE_NAME, coalesce(v_record, '?'),
            v_old, v_new, v_changed);
    RETURN NULL;
END $$;

CREATE TABLE audit.security_events (
    id            bigint GENERATED ALWAYS AS IDENTITY,
    occurred_at   timestamptz NOT NULL DEFAULT now(),
    event_type    text NOT NULL CHECK (event_type IN (
                      'sign_in', 'sign_in_failed', 'sign_out', 'password_reset', 'mfa_changed',
                      'role_changed', 'account_suspended', 'account_deletion_requested', 'account_erased',
                      'data_export', 'subscription_changed', 'admin_impersonation', 'api_key_created',
                      'rate_limited', 'prompt_injection_blocked', 'sandbox_violation', 'webhook_rejected')),
    severity      text NOT NULL DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'critical')),
    user_id       uuid,                 -- subject
    actor_user_id uuid,                 -- who did it (NULL = system)
    request_id    text,
    ip_hmac       bytea,
    user_agent    text,
    details       jsonb NOT NULL DEFAULT '{}',
    PRIMARY KEY (id, occurred_at)
) PARTITION BY RANGE (occurred_at);
CREATE INDEX ix_security_events_user ON audit.security_events (user_id, occurred_at DESC);
CREATE INDEX ix_security_events_type ON audit.security_events (event_type, occurred_at DESC)
    WHERE severity <> 'info';

CREATE TABLE audit.data_access_log (
    id              bigint GENERATED ALWAYS AS IDENTITY,
    accessed_at     timestamptz NOT NULL DEFAULT now(),
    actor_user_id   uuid NOT NULL,
    subject_user_id uuid NOT NULL,
    resource        text NOT NULL,      -- e.g. 'chat.conversations', 'learning.concept_mastery'
    purpose         text NOT NULL CHECK (purpose IN ('support', 'moderation', 'dsar', 'incident', 'grading_review')),
    request_id      text,
    details         jsonb NOT NULL DEFAULT '{}',
    PRIMARY KEY (id, accessed_at)
) PARTITION BY RANGE (accessed_at);
CREATE INDEX ix_data_access_subject ON audit.data_access_log (subject_user_id, accessed_at DESC);
CREATE INDEX ix_data_access_actor ON audit.data_access_log (actor_user_id, accessed_at DESC);
