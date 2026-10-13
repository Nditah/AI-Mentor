-- Smoke tests for the target schema. Run by backend/db/verify.sh against a
-- freshly built database. Every block raises on failure.
\set ON_ERROR_STOP on

-- Fixtures --------------------------------------------------------------------
INSERT INTO identity.users (id, clerk_id, email, display_name, handle) VALUES
    ('00000000-0000-7000-8000-000000000001', 'clerk_a', 'ada@example.com',  'Ada',  'ada'),
    ('00000000-0000-7000-8000-000000000002', 'clerk_b', 'alan@example.com', 'Alan', 'alan');
INSERT INTO identity.user_profiles (user_id, country_code, persona) VALUES
    ('00000000-0000-7000-8000-000000000001', 'NG', 'robotics_engineer'),
    ('00000000-0000-7000-8000-000000000002', 'GB', 'student');
INSERT INTO identity.learning_preferences (user_id, teaching_style) VALUES
    ('00000000-0000-7000-8000-000000000001', 'mathematical');
INSERT INTO identity.tutor_avatars (user_id, voice_accent, personality) VALUES
    ('00000000-0000-7000-8000-000000000001', 'nigerian', 'socratic');
INSERT INTO game.user_stats (user_id) VALUES
    ('00000000-0000-7000-8000-000000000001'), ('00000000-0000-7000-8000-000000000002');

-- uuid_v7 is time-ordered and version 7 -------------------------------------
DO $$
DECLARE a uuid := util.uuid_v7(); b uuid;
BEGIN
    PERFORM pg_sleep(0.002);
    b := util.uuid_v7();
    ASSERT substring(a::text, 15, 1) = '7', 'uuid version nibble must be 7';
    ASSERT a < b, 'uuid_v7 must sort by creation time';
END $$;

-- Taxonomy paths are maintained and cascade on move --------------------------
DO $$
DECLARE ai uuid; ml uuid; rl uuid; mdp uuid;
BEGIN
    INSERT INTO curriculum.taxonomy_nodes (slug, name) VALUES ('artificial_intelligence', 'AI') RETURNING id INTO ai;
    INSERT INTO curriculum.taxonomy_nodes (parent_id, slug, name) VALUES (ai, 'machine_learning', 'ML') RETURNING id INTO ml;
    INSERT INTO curriculum.taxonomy_nodes (parent_id, slug, name) VALUES (ai, 'reinforcement_learning', 'RL') RETURNING id INTO rl;
    INSERT INTO curriculum.taxonomy_nodes (parent_id, slug, name) VALUES (rl, 'mdp', 'MDP') RETURNING id INTO mdp;
    ASSERT (SELECT path::text FROM curriculum.taxonomy_nodes WHERE id = mdp) = 'artificial_intelligence.reinforcement_learning.mdp';

    UPDATE curriculum.taxonomy_nodes SET parent_id = ml WHERE id = rl;
    ASSERT (SELECT path::text FROM curriculum.taxonomy_nodes WHERE id = mdp)
           = 'artificial_intelligence.machine_learning.reinforcement_learning.mdp', 'descendant path must cascade';

    BEGIN
        UPDATE curriculum.taxonomy_nodes SET parent_id = mdp WHERE id = rl;
        RAISE EXCEPTION 'moving a node under its descendant must fail';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    UPDATE curriculum.taxonomy_nodes SET parent_id = ai WHERE id = rl;
END $$;

-- Concept graph rejects prerequisite cycles ----------------------------------
DO $$
DECLARE node uuid := (SELECT id FROM curriculum.taxonomy_nodes WHERE slug = 'mdp');
        mdp uuid; bellman uuid; ql uuid;
BEGIN
    INSERT INTO curriculum.concepts (slug, taxonomy_node_id, name, difficulty, status)
        VALUES ('mdp', node, 'Markov decision process', 'intermediate', 'published') RETURNING id INTO mdp;
    INSERT INTO curriculum.concepts (slug, taxonomy_node_id, name, difficulty, status)
        VALUES ('bellman_equation', node, 'Bellman equation', 'intermediate', 'published') RETURNING id INTO bellman;
    INSERT INTO curriculum.concepts (slug, taxonomy_node_id, name, difficulty, status)
        VALUES ('q_learning', node, 'Q-learning', 'advanced', 'published') RETURNING id INTO ql;
    INSERT INTO curriculum.concept_relations (from_concept_id, to_concept_id, relation_type) VALUES
        (bellman, mdp, 'prerequisite'), (ql, bellman, 'prerequisite');
    BEGIN
        INSERT INTO curriculum.concept_relations (from_concept_id, to_concept_id, relation_type)
            VALUES (mdp, ql, 'prerequisite');
        RAISE EXCEPTION 'cycle mdp -> q_learning -> bellman -> mdp must be rejected';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    -- non-prerequisite edges may point back
    INSERT INTO curriculum.concept_relations (from_concept_id, to_concept_id, relation_type) VALUES (mdp, ql, 'related');
END $$;

-- Curriculum: deferrable reorder, one published body per locale/style, one path target
DO $$
DECLARE c uuid; m uuid; l1 uuid; l2 uuid; p uuid;
BEGIN
    INSERT INTO curriculum.courses (slug, title) VALUES ('rl-101', 'RL 101') RETURNING id INTO c;
    INSERT INTO curriculum.modules (course_id, title, position) VALUES (c, 'Foundations', 0) RETURNING id INTO m;
    INSERT INTO curriculum.lessons (module_id, slug, position, primary_concept_id)
        VALUES (m, 'what-is-an-mdp', 0, (SELECT id FROM curriculum.concepts WHERE slug = 'mdp')) RETURNING id INTO l1;
    INSERT INTO curriculum.lessons (module_id, slug, position) VALUES (m, 'bellman', 1) RETURNING id INTO l2;

    SET CONSTRAINTS curriculum.uq_lessons_position DEFERRED;
    UPDATE curriculum.lessons SET position = 1 WHERE id = l1;
    UPDATE curriculum.lessons SET position = 0 WHERE id = l2;
    SET CONSTRAINTS curriculum.uq_lessons_position IMMEDIATE;

    INSERT INTO curriculum.lesson_contents (lesson_id, locale, teaching_style, version, title, body_md, status)
        VALUES (l1, 'en', 'mixed', 1, 'What is an MDP', '...', 'published'),
               (l1, 'fr', 'mixed', 1, 'Qu''est-ce qu''un MDP', '...', 'published');
    BEGIN
        INSERT INTO curriculum.lesson_contents (lesson_id, locale, teaching_style, version, title, body_md, status)
            VALUES (l1, 'en', 'mixed', 2, 'v2', '...', 'published');
        RAISE EXCEPTION 'two published bodies for the same locale/style must fail';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;

    INSERT INTO curriculum.learning_paths (slug, title) VALUES ('reinforcement-learning', 'RL') RETURNING id INTO p;
    INSERT INTO curriculum.learning_path_items (path_id, position, lesson_id) VALUES (p, 0, l1);
    BEGIN
        INSERT INTO curriculum.learning_path_items (path_id, position, lesson_id, course_id) VALUES (p, 1, l2, c);
        RAISE EXCEPTION 'path item with two targets must fail';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
END $$;

-- Knowledge workflow: drafts only, legal transitions, all logged; vector outbox
DO $$
DECLARE f uuid; a uuid; v uuid; ch uuid; col smallint;
BEGIN
    INSERT INTO knowledge.files (storage_provider, storage_uri, mime_type, byte_size, sha256)
        VALUES ('azure_blob', 'blob://library/sutton-barto.pdf', 'application/pdf', 1000, sha256('x'))
        RETURNING id INTO f;
    INSERT INTO knowledge.assets (scope, slug, kind, title)
        VALUES ('curated', 'sutton-barto', 'book', 'Reinforcement Learning: An Introduction') RETURNING id INTO a;

    BEGIN
        INSERT INTO knowledge.asset_versions (asset_id, version_no, file_id, status) VALUES (a, 1, f, 'published');
        RAISE EXCEPTION 'curated version created as published must fail';
    EXCEPTION WHEN check_violation THEN NULL;
    END;

    INSERT INTO knowledge.asset_versions (asset_id, version_no, file_id) VALUES (a, 1, f) RETURNING id INTO v;
    BEGIN
        UPDATE knowledge.asset_versions SET status = 'published' WHERE id = v;
        RAISE EXCEPTION 'draft -> published must fail';
    EXCEPTION WHEN check_violation THEN NULL;
    END;

    PERFORM set_config('app.workflow_comment', 'looks good', true);
    UPDATE knowledge.asset_versions SET status = 'review'    WHERE id = v;
    UPDATE knowledge.asset_versions SET status = 'approved'  WHERE id = v;
    UPDATE knowledge.asset_versions SET status = 'published' WHERE id = v;
    UPDATE knowledge.assets SET status = 'published', current_version_id = v WHERE id = a;

    ASSERT (SELECT count(*) FROM knowledge.workflow_transitions WHERE asset_version_id = v) = 4,
           'creation + 3 transitions must be logged';
    ASSERT (SELECT published_at IS NOT NULL AND approved_at IS NOT NULL FROM knowledge.asset_versions WHERE id = v);

    INSERT INTO knowledge.chunks (asset_version_id, ordinal, content, token_count, content_hash, citation_label)
        VALUES (v, 0, 'The Bellman equation relates the value of a state to its successors.', 14, sha256('c0'), '[SB 3.5]')
        RETURNING id INTO ch;
    ASSERT (SELECT owner_user_id IS NULL FROM knowledge.chunks WHERE id = ch), 'curated chunk has no owner';
    ASSERT (SELECT count(*) FROM knowledge.chunks WHERE content_tsv @@ to_tsquery('simple', 'bellman')) = 1;

    SELECT id INTO col FROM vector.collections WHERE alias = 'knowledge_curated' AND status = 'active';
    INSERT INTO vector.chunk_embeddings (chunk_id, collection_id, content_hash, status, embedded_at)
        VALUES (ch, col, sha256('c0'), 'indexed', now());

    UPDATE knowledge.assets SET status = 'archived', archived_at = now() WHERE id = a;
    ASSERT (SELECT count(*) FROM vector.sync_outbox WHERE point_id = ch AND operation = 'set_payload') = 1,
           'archiving must enqueue a payload update';

    DELETE FROM knowledge.chunks WHERE id = ch;
    ASSERT (SELECT count(*) FROM vector.sync_outbox WHERE point_id = ch AND operation = 'delete') = 1,
           'deleting a chunk must enqueue a Qdrant delete';
END $$;

-- Chat: partitioned messages, co-partitioned citations, counters --------------
DO $$
DECLARE conv uuid; m1 uuid; t timestamptz := now();
BEGIN
    INSERT INTO chat.conversations (user_id, title) VALUES ('00000000-0000-7000-8000-000000000001', 'Bellman')
        RETURNING id INTO conv;
    INSERT INTO chat.messages (conversation_id, user_id, role, content, created_at)
        VALUES (conv, '00000000-0000-7000-8000-000000000001', 'user', 'What is the Bellman equation?', t);
    INSERT INTO chat.messages (conversation_id, user_id, role, content, grounded, created_at)
        VALUES (conv, '00000000-0000-7000-8000-000000000001', 'assistant', 'Before I answer: what is a value function?', true, t)
        RETURNING id INTO m1;
    INSERT INTO chat.message_citations (message_id, message_created_at, rank, citation_label) VALUES (m1, t, 1, '[SB 3.5]');
    INSERT INTO chat.message_feedback (message_id, message_created_at, user_id, rating)
        VALUES (m1, t, '00000000-0000-7000-8000-000000000001', 1);
    ASSERT (SELECT message_count FROM chat.conversations WHERE id = conv) = 2;
    ASSERT (SELECT count(*) FROM ONLY chat.messages) = 0, 'rows live in partitions, not the parent';
    ASSERT (SELECT count(*) FROM chat.messages_default) = 0, 'current month must not hit the default partition';
END $$;

-- Quiz attempt + responses (co-partitioned FK) ---------------------------------
DO $$
DECLARE q uuid; at uuid; st timestamptz := now();
        u uuid := '00000000-0000-7000-8000-000000000001';
        mdp uuid := (SELECT id FROM curriculum.concepts WHERE slug = 'mdp');
BEGIN
    INSERT INTO learning.quizzes (user_id, concept_id, difficulty, generated_by) VALUES (u, mdp, 'intermediate', 'llm')
        RETURNING id INTO q;
    INSERT INTO learning.quiz_items (quiz_id, position, concept_id, kind, difficulty, question_snapshot)
        VALUES (q, 0, mdp, 'mcq', 'intermediate', '{"prompt": "An MDP is defined by?"}');
    INSERT INTO learning.quiz_attempts (id, started_at, quiz_id, user_id) VALUES (util.uuid_v7(), st, q, u)
        RETURNING id INTO at;
    INSERT INTO learning.question_responses (attempt_id, attempt_started_at, position, user_id, concept_id, kind, difficulty,
                                             response, is_correct, score)
        VALUES (at, st, 0, u, mdp, 'mcq', 'intermediate', '{"choice": 2}', true, 1);
    UPDATE learning.quiz_attempts SET status = 'submitted', submitted_at = now(), score = 1, max_score = 1
        WHERE id = at AND started_at = st;
    ASSERT (SELECT score_pct FROM learning.quiz_attempts WHERE id = at) = 100;

    INSERT INTO learning.concept_mastery (user_id, concept_id, score, evidence_count, correct_count)
        VALUES (u, mdp, 72, 3, 3);
    ASSERT (SELECT band FROM learning.concept_mastery WHERE user_id = u AND concept_id = mdp) = 'strong';
    ASSERT (SELECT classification FROM analytics.v_learner_strengths WHERE user_id = u) = 'strength';
END $$;

-- XP ledger idempotency --------------------------------------------------------
DO $$
DECLARE u uuid := '00000000-0000-7000-8000-000000000001';
BEGIN
    INSERT INTO game.xp_ledger (local_date, user_id, amount, requested_amount, source, idempotency_key)
        VALUES (current_date, u, 50, 50, 'quiz', 'quiz:abc');
    BEGIN
        INSERT INTO game.xp_ledger (local_date, user_id, amount, requested_amount, source, idempotency_key)
            VALUES (current_date, u, 50, 50, 'quiz', 'quiz:abc');
        RAISE EXCEPTION 'duplicate XP award must fail';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;
    BEGIN
        INSERT INTO game.xp_ledger (local_date, user_id, amount, requested_amount, source, idempotency_key)
            VALUES (current_date, u, -10, -10, 'quiz', 'quiz:neg');
        RAISE EXCEPTION 'negative XP outside adjustments must fail';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
END $$;

-- Audit captures governed tables, only changed columns, no personal identifiers
DO $$
BEGIN
    ASSERT NOT EXISTS (SELECT 1 FROM audit.row_changes
                       WHERE table_name = 'users' AND (new_data ? 'email' OR new_data ? 'display_name')),
           'personal identifiers must be redacted from audit rows';
    PERFORM set_config('app.current_user_id', '00000000-0000-7000-8000-000000000002', true);
    UPDATE identity.users SET role = 'instructor', display_name = 'Ada L.'
        WHERE id = '00000000-0000-7000-8000-000000000001';
    ASSERT (SELECT changed_columns FROM audit.row_changes
            WHERE table_name = 'users' AND operation = 'U'
              AND record_id = '00000000-0000-7000-8000-000000000001') = ARRAY['role'];
    ASSERT (SELECT actor_user_id FROM audit.row_changes WHERE table_name = 'users' AND operation = 'U')
           = '00000000-0000-7000-8000-000000000002';
    -- changes to redacted columns only, or no-op updates, write nothing
    UPDATE identity.users SET display_name = 'Ada Lovelace' WHERE id = '00000000-0000-7000-8000-000000000001';
    UPDATE identity.users SET role = 'instructor' WHERE id = '00000000-0000-7000-8000-000000000001';
    ASSERT (SELECT count(*) FROM audit.row_changes WHERE table_name = 'users' AND operation = 'U') = 1;
    PERFORM set_config('app.current_user_id', '', true);
END $$;

-- Audit bypass works for owner logins only ---------------------------------
DO $$
BEGIN
    PERFORM set_config('app.skip_audit', 'on', true);
    UPDATE identity.users SET status = 'suspended' WHERE id = '00000000-0000-7000-8000-000000000002';
    ASSERT NOT EXISTS (SELECT 1 FROM audit.row_changes WHERE table_name = 'users' AND operation = 'U'
                       AND record_id = '00000000-0000-7000-8000-000000000002'), 'owner backfill skips audit';
    PERFORM set_config('app.skip_audit', '', true);
END $$;

SET SESSION AUTHORIZATION mentor_app;
DO $$
BEGIN
    PERFORM set_config('app.skip_audit', 'on', true);
    UPDATE identity.users SET status = 'active' WHERE id = '00000000-0000-7000-8000-000000000002';
    PERFORM set_config('app.skip_audit', '', true);
END $$;
RESET SESSION AUTHORIZATION;
DO $$
BEGIN
    ASSERT EXISTS (SELECT 1 FROM audit.row_changes WHERE table_name = 'users' AND operation = 'U'
                   AND record_id = '00000000-0000-7000-8000-000000000002'), 'the app cannot switch auditing off';
END $$;

-- RLS: the app role only sees the current learner's chat -----------------------
SET SESSION AUTHORIZATION mentor_app;
DO $$
BEGIN
    PERFORM set_config('app.current_user_id', '00000000-0000-7000-8000-000000000002', true);
    ASSERT (SELECT count(*) FROM chat.messages) = 0, 'another learner must not see Ada''s messages';
    PERFORM set_config('app.current_user_id', '00000000-0000-7000-8000-000000000001', true);
    ASSERT (SELECT count(*) FROM chat.messages) = 2, 'Ada must see her own messages';
    BEGIN
        INSERT INTO chat.conversations (user_id) VALUES ('00000000-0000-7000-8000-000000000002');
        RAISE EXCEPTION 'writing another learner''s conversation must fail';
    EXCEPTION WHEN insufficient_privilege THEN NULL;
    END;
    BEGIN
        INSERT INTO audit.row_changes (operation, table_schema, table_name, record_id) VALUES ('I', 'x', 'y', 'z');
        RAISE EXCEPTION 'app must not write audit rows directly';
    EXCEPTION WHEN insufficient_privilege THEN NULL;
    END;
    PERFORM set_config('app.current_user_id', '', true);
END $$;
RESET SESSION AUTHORIZATION;

-- Retention: drop an old month across co-partitioned tables ------------------
DO $$
DECLARE conv uuid; m uuid; t timestamptz := '2024-01-15 12:00:00+00'; dropped text[];
BEGIN
    PERFORM util.create_time_partitions('chat.messages', 'month', '2024-01-01', 1);
    PERFORM util.create_time_partitions('chat.message_citations', 'month', '2024-01-01', 1);
    PERFORM util.create_time_partitions('chat.message_feedback', 'month', '2024-01-01', 1);
    SELECT id INTO conv FROM chat.conversations LIMIT 1;
    INSERT INTO chat.messages (conversation_id, user_id, role, content, created_at)
        VALUES (conv, '00000000-0000-7000-8000-000000000001', 'assistant', 'old', t) RETURNING id INTO m;
    INSERT INTO chat.message_citations (message_id, message_created_at, rank, citation_label) VALUES (m, t, 1, 'old');

    BEGIN
        PERFORM util.drop_time_partitions_before('chat.messages', '2024-02-01');
        RAISE EXCEPTION 'dropping messages before citations must be blocked by the FK';
    EXCEPTION WHEN foreign_key_violation THEN NULL;
    END;

    SELECT array_agg(x) INTO dropped FROM (
        SELECT util.drop_time_partitions_before('chat.message_citations', '2024-02-01') AS x
        UNION ALL SELECT util.drop_time_partitions_before('chat.message_feedback', '2024-02-01')
        UNION ALL SELECT util.drop_time_partitions_before('chat.messages', '2024-02-01')) s;
    ASSERT cardinality(dropped) = 3, format('expected 3 dropped partitions, got %s', dropped);
    ASSERT (SELECT count(*) FROM chat.messages WHERE created_at < '2024-02-01') = 0;
    ASSERT (SELECT count(*) FROM chat.messages) = 2, 'current partitions untouched';
END $$;

-- Maintenance is idempotent and partitions cover the future -------------------
DO $$
BEGIN
    ASSERT (SELECT sum(created) FROM util.run_partition_maintenance()) = 0, 'second run must create nothing';
    ASSERT NOT EXISTS (SELECT 1 FROM util.v_partition_health
                       WHERE covered_until < now() + ('1 ' || grain)::interval),
           'every registered table must have partitions at least one period ahead';
END $$;

-- Retention jobs: XP compaction and batched purge of non-partitioned tables ---
DO $$
DECLARE u uuid := '00000000-0000-7000-8000-000000000002'; conv uuid;
BEGIN
    INSERT INTO game.xp_ledger (local_date, user_id, amount, requested_amount, source, idempotency_key) VALUES
        ('2023-03-04', u, 40, 40, 'lesson', 'lesson:1'),
        ('2023-03-09', u, 25, 25, 'lesson', 'lesson:2');
    PERFORM game.compact_xp_ledger(current_date);
    PERFORM game.compact_xp_ledger(current_date);   -- idempotent
    ASSERT (SELECT amount FROM game.xp_monthly_rollup
            WHERE user_id = u AND month = '2023-03-01' AND source = 'lesson') = 65;

    INSERT INTO chat.conversations (user_id, deleted_at) VALUES (u, now() - interval '31 days') RETURNING id INTO conv;
    PERFORM * FROM util.purge_expired_rows();
    ASSERT NOT EXISTS (SELECT 1 FROM chat.conversations WHERE id = conv), 'soft-deleted conversation must be purged';
END $$;

-- Erasure removes the learner everywhere and releases personal files ----------
DO $$
DECLARE u uuid := '00000000-0000-7000-8000-000000000001'; f uuid; a uuid; v uuid; ch uuid; uris text[];
BEGIN
    INSERT INTO knowledge.files (storage_provider, storage_uri, mime_type, byte_size, sha256, uploaded_by)
        VALUES ('azure_blob', 'blob://personal/ada/paper.pdf', 'application/pdf', 10, sha256('p'), u) RETURNING id INTO f;
    INSERT INTO knowledge.assets (scope, owner_user_id, kind, title, status)
        VALUES ('personal', u, 'research_paper', 'My draft', 'published') RETURNING id INTO a;
    INSERT INTO knowledge.asset_versions (asset_id, version_no, file_id, status) VALUES (a, 1, f, 'published') RETURNING id INTO v;
    INSERT INTO knowledge.chunks (asset_version_id, ordinal, content, token_count, content_hash, citation_label)
        VALUES (v, 0, 'private text', 2, sha256('p0'), '[p1]') RETURNING id INTO ch;
    ASSERT (SELECT owner_user_id FROM knowledge.chunks WHERE id = ch) = u, 'personal chunk owner must be filled';
    INSERT INTO vector.chunk_embeddings (chunk_id, collection_id, content_hash, status)
        VALUES (ch, (SELECT id FROM vector.collections WHERE alias = 'personal_documents'), sha256('p0'), 'indexed');
    INSERT INTO activity.events (id, occurred_at, user_id, event_name) VALUES (util.uuid_v7(), now(), u, 'lesson.viewed');

    SELECT array_agg(storage_uri) INTO uris FROM identity.erase_user(u);

    ASSERT uris = ARRAY['blob://personal/ada/paper.pdf'], format('unexpected uris %s', uris);
    ASSERT NOT EXISTS (SELECT 1 FROM identity.users WHERE id = u);
    ASSERT NOT EXISTS (SELECT 1 FROM chat.messages WHERE user_id = u);
    ASSERT NOT EXISTS (SELECT 1 FROM learning.question_responses WHERE user_id = u);
    ASSERT NOT EXISTS (SELECT 1 FROM game.xp_ledger WHERE user_id = u);
    ASSERT NOT EXISTS (SELECT 1 FROM activity.events WHERE user_id = u);
    ASSERT NOT EXISTS (SELECT 1 FROM knowledge.files WHERE id = f);
    ASSERT EXISTS (SELECT 1 FROM vector.sync_outbox WHERE point_id = ch AND operation = 'delete'),
           'personal vectors must be queued for deletion';
    ASSERT NOT EXISTS (SELECT 1 FROM audit.row_changes
                       WHERE table_schema = 'identity' AND record_id = u::text
                         AND (old_data IS NOT NULL OR new_data IS NOT NULL)),
           'audit payloads for the erased learner must be redacted';
    ASSERT EXISTS (SELECT 1 FROM audit.security_events WHERE event_type = 'account_erased' AND user_id = u);
END $$;

SELECT 'smoke tests passed' AS result;
