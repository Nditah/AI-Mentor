-- =============================================================================
-- 13 generic triggers: updated_at maintenance and audit capture
-- =============================================================================

-- updated_at on every table (or partitioned parent) that has the column.
DO $$
DECLARE
    r record;
BEGIN
    FOR r IN
        SELECT n.nspname, c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'updated_at' AND NOT a.attisdropped
        WHERE c.relkind IN ('r', 'p')
          AND NOT c.relispartition
          AND n.nspname IN ('identity', 'curriculum', 'knowledge', 'vector', 'learning',
                            'chat', 'game', 'activity', 'analytics')
    LOOP
        EXECUTE format('CREATE TRIGGER trg_%s_updated_at BEFORE UPDATE ON %I.%I
                        FOR EACH ROW EXECUTE FUNCTION util.set_updated_at()',
                       r.relname, r.nspname, r.relname);
    END LOOP;
END $$;

-- Audit capture on governed tables: identity, curriculum, curated knowledge,
-- vector configuration, and gamification catalogs. High-volume learner tables
-- are not audited row-by-row; they are append-only ledgers already.
-- Redacted columns: personal identifiers (audit rows carry internal ids only,
-- Security-Compliance.md AL-4), secrets, and large bodies kept by versioning.
DO $$
DECLARE
    t record;
BEGIN
    FOR t IN SELECT * FROM (VALUES
        ('identity',   'users',                 'id',                       ARRAY['clerk_id', 'email', 'display_name', 'handle', 'avatar_url']),
        ('identity',   'user_profiles',         'user_id',                  ARRAY['region_code', 'career_goal', 'bio']),
        ('identity',   'learning_preferences',  'user_id',                  ARRAY[]::text[]),
        ('identity',   'subscriptions',         'id',                       ARRAY['provider_customer_id', 'provider_subscription_id']),
        ('curriculum', 'taxonomy_nodes',        'id',                       ARRAY[]::text[]),
        ('curriculum', 'concepts',              'id',                       ARRAY[]::text[]),
        ('curriculum', 'concept_relations',     'from_concept_id,to_concept_id,relation_type', ARRAY[]::text[]),
        ('curriculum', 'courses',               'id',                       ARRAY[]::text[]),
        ('curriculum', 'modules',               'id',                       ARRAY[]::text[]),
        ('curriculum', 'lessons',               'id',                       ARRAY[]::text[]),
        ('curriculum', 'lesson_contents',       'id',                       ARRAY['body_md']),
        ('curriculum', 'learning_paths',        'id',                       ARRAY[]::text[]),
        ('curriculum', 'learning_path_items',   'id',                       ARRAY[]::text[]),
        ('curriculum', 'questions',             'id',                       ARRAY['answer_key']),
        ('curriculum', 'assessments',           'id',                       ARRAY[]::text[]),
        ('curriculum', 'assessment_questions',  'assessment_id,question_id', ARRAY[]::text[]),
        ('curriculum', 'coding_exercises',      'id',                       ARRAY['reference_solution']),
        ('knowledge',  'assets',                'id',                       ARRAY[]::text[]),
        ('knowledge',  'asset_versions',        'id',                       ARRAY[]::text[]),
        ('knowledge',  'asset_concepts',        'asset_id,concept_id',      ARRAY[]::text[]),
        ('knowledge',  'generated_artifacts',   'id',                       ARRAY['payload']),
        ('vector',     'embedding_models',      'id',                       ARRAY[]::text[]),
        ('vector',     'collections',           'id',                       ARRAY['point_count', 'reconciled_at']),
        ('game',       'badges',                'id',                       ARRAY[]::text[]),
        ('game',       'titles',                'id',                       ARRAY[]::text[]),
        ('game',       'challenges',            'id',                       ARRAY[]::text[])
    ) AS v(schema_name, table_name, pk_cols, redact_cols)
    LOOP
        EXECUTE format('CREATE TRIGGER trg_%s_audit AFTER INSERT OR UPDATE OR DELETE ON %I.%I
                        FOR EACH ROW EXECUTE FUNCTION audit.capture_row_change(%s)',
                       t.table_name, t.schema_name, t.table_name,
                       (SELECT string_agg(quote_literal(a), ', ')
                        FROM unnest(ARRAY[t.pk_cols] || t.redact_cols) AS a));
    END LOOP;
END $$;
