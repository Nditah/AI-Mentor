-- =============================================================================
-- 15 reference seed data (idempotent). Curriculum content is seeded by the
-- application from backend/app/domain/catalog.py, not here.
-- =============================================================================

INSERT INTO ref.languages (code, name, native_name, is_default) VALUES
    ('en', 'English', 'English', true),
    ('fr', 'French',  'Français', false),
    ('es', 'Spanish', 'Español', false)
ON CONFLICT (code) DO NOTHING;

-- Load the full ISO 3166-1 list in production; these cover tests and launch markets.
INSERT INTO ref.countries (iso2, iso3, name, region, subregion) VALUES
    ('GB', 'GBR', 'United Kingdom', 'Europe',   'Northern Europe'),
    ('FR', 'FRA', 'France',         'Europe',   'Western Europe'),
    ('ES', 'ESP', 'Spain',          'Europe',   'Southern Europe'),
    ('NG', 'NGA', 'Nigeria',        'Africa',   'Western Africa'),
    ('US', 'USA', 'United States',  'Americas', 'Northern America'),
    ('MX', 'MEX', 'Mexico',         'Americas', 'Central America'),
    ('CA', 'CAN', 'Canada',         'Americas', 'Northern America'),
    ('IN', 'IND', 'India',          'Asia',     'Southern Asia')
ON CONFLICT (iso2) DO NOTHING;

INSERT INTO ref.voice_accents (code, name, locale) VALUES
    ('british',  'British',  'en'),
    ('american', 'American', 'en'),
    ('nigerian', 'Nigerian', 'en'),
    ('french',   'French',   'fr'),
    ('spanish',  'Spanish',  'es')
ON CONFLICT (code) DO NOTHING;

INSERT INTO game.titles (slug, name_i18n, min_level, sort_order) VALUES
    ('ai_apprentice',           '{"en": "AI Apprentice", "fr": "Apprenti IA", "es": "Aprendiz de IA"}',             1,  10),
    ('data_scientist',          '{"en": "Data Scientist", "fr": "Data Scientist", "es": "Científico de Datos"}',     5,  20),
    ('rl_explorer',             '{"en": "RL Explorer", "fr": "Explorateur RL", "es": "Explorador de RL"}',          10, 30),
    ('robotics_engineer',       '{"en": "Robotics Engineer", "fr": "Ingénieur Robotique", "es": "Ingeniero de Robótica"}', 15, 40),
    ('ai_researcher',           '{"en": "AI Researcher", "fr": "Chercheur IA", "es": "Investigador de IA"}',        25, 50),
    ('ai_master',               '{"en": "AI Master", "fr": "Maître IA", "es": "Maestro de IA"}',                    40, 60),
    ('grandmaster_ai_engineer', '{"en": "Grandmaster AI Engineer", "fr": "Grand Maître Ingénieur IA", "es": "Gran Maestro Ingeniero de IA"}', 60, 70)
ON CONFLICT (slug) DO NOTHING;

-- Slugs match backend/app/domain/gamification.py evaluate_badges().
INSERT INTO game.badges (slug, name_i18n, category, tier, xp_reward, criteria) VALUES
    ('first_steps',  '{"en": "First Steps"}',   'learning',  'bronze', 20,  '{"lessons_completed": 1}'),
    ('streak_3',     '{"en": "On a Roll"}',     'streak',    'bronze', 20,  '{"streak_days": 3}'),
    ('week_streak',  '{"en": "Week Streak"}',   'streak',    'silver', 50,  '{"streak_days": 7}'),
    ('perfect_quiz', '{"en": "Perfect Quiz"}',  'learning',  'silver', 30,  '{"perfect_quiz": true}'),
    ('mastery',      '{"en": "Mastery"}',       'mastery',   'gold',   75,  '{"max_mastery": 80}'),
    ('reviewer',     '{"en": "Reviewer"}',      'research',  'bronze', 25,  '{"analyses": 1}'),
    ('shipped_code', '{"en": "Shipped Code"}',  'coding',    'bronze', 25,  '{"code_passes": 1}')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO activity.event_types (name, category, description) VALUES
    ('auth.signed_in',                 'auth',         'User signed in'),
    ('onboarding.started',             'onboarding',   'Onboarding assessment started'),
    ('onboarding.completed',           'onboarding',   'Onboarding assessment completed'),
    ('lesson.viewed',                  'learning',     'Lesson opened'),
    ('lesson.completed',               'learning',     'Lesson marked complete'),
    ('path.enrolled',                  'learning',     'Learner enrolled in a learning path'),
    ('quiz.started',                   'assessment',   'Quiz attempt started'),
    ('quiz.submitted',                 'assessment',   'Quiz attempt submitted'),
    ('code.run',                       'coding',       'Code executed in the lab'),
    ('code.submitted',                 'coding',       'Code submitted for grading'),
    ('tutor.message_sent',             'tutor',        'Learner sent a tutor message'),
    ('tutor.style_changed',            'settings',     'Teaching style changed'),
    ('settings.locale_changed',        'settings',     'Interface language changed'),
    ('flashcard.reviewed',             'learning',     'Flashcard reviewed'),
    ('challenge.started',              'gamification', 'Daily challenge started'),
    ('challenge.completed',            'gamification', 'Daily challenge completed'),
    ('gamification.level_up',          'gamification', 'Learner reached a new level'),
    ('gamification.badge_earned',      'gamification', 'Badge awarded'),
    ('knowledge.asset_viewed',         'knowledge',    'Library resource opened'),
    ('knowledge.search_performed',     'knowledge',    'Library or concept search'),
    ('research.document_uploaded',     'research',     'Learner uploaded a paper'),
    ('navigation.recommendation_clicked', 'navigation', 'Recommendation clicked'),
    ('billing.checkout_started',       'billing',      'Stripe checkout started')
ON CONFLICT (name) DO NOTHING;

INSERT INTO vector.embedding_models (provider, model, revision, dimensions, distance, max_input_tokens)
VALUES ('openai', 'text-embedding-3-small', '1', 1536, 'cosine', 8191)
ON CONFLICT (provider, model, revision) DO NOTHING;

INSERT INTO vector.collections (name, alias, purpose, embedding_model_id, status, multitenant, activated_at)
SELECT c.name, c.alias, c.purpose, m.id, 'active', c.multitenant, now()
FROM (VALUES
    ('knowledge_curated__te3s_v1',  'knowledge_curated',  'curated_knowledge',  false),
    ('personal_documents__te3s_v1', 'personal_documents', 'personal_documents', true),
    ('concepts__te3s_v1',           'concepts',           'concepts',           false),
    ('questions__te3s_v1',          'questions',          'questions',          false)
) AS c(name, alias, purpose, multitenant)
CROSS JOIN vector.embedding_models m
WHERE m.provider = 'openai' AND m.model = 'text-embedding-3-small' AND m.revision = '1'
ON CONFLICT (name) DO NOTHING;
