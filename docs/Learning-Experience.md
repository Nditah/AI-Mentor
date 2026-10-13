# Learning experience

| Field | Value |
| --- | --- |
| Status | Implemented for the learner journey, Content Studio authoring, and admin metrics |
| Date | 13 October 2026 |
| Code | `backend/app/domain/learn`, `backend/app/services/learn_journey.py`, `apps/learner/app/(learn)` |

A learner does not open a pile of lessons. World lists every learning path. Faculty (AI, Robotics, Data Science) and level (beginner, intermediate, advanced) filter that list; academies are a third filter, not the first click. Opening a path still moves through a course, a module, a lesson, and one topic page at a time. The worked example is RL Foundations: Markov Decision Processes, then States & Actions, then What is a State?

## 1. Learning experience architecture

```text
Faculty                 (AI | Robotics | Data Science — World filter, not a page)
  Academy               (World filter)
    Learning Path       (World lists these. Later paths stay locked until the previous path is 100%)
      Course
        Module
          Lesson
            Topic page     reading, video, exercise, knowledge check, or summary
          Module assessment
        Course assessment
      Learning path completion
```

Catalog tracks that already existed (AI Fundamentals, the concept-level Reinforcement Learning track, Robotics, LLM Engineering) stay. Each of their lessons now has topic pages: Read, Exercise when the markdown has one, and a knowledge check. The new academy is the guided hierarchy on top of that.

Pass mark for checks and assessments is 70% unless an author sets another score. The first pass of a lesson awards lesson XP. A knowledge check awards 5 XP once. An assessment awards its authored XP once. A learning-path assessment also awards the path XP and the matching badge when that badge exists.

## 2. Database schema

Migration `20261013_0003`. New tables:

| Table | Role |
| --- | --- |
| `academies` | Named curriculum |
| `topic_pages` | One screen of a lesson. `origin` is `seed` or `authored` |
| `lesson_resources` | A placement only: lesson, optional page, catalog asset, order, and role (`related`, `further`, `research`). Title, URL, tags, and skills stay on `knowledge_assets` |
| `knowledge_checks` | One check per topic page |
| `knowledge_check_questions` | `mcq`, `true_false`, `fill`, `short`, `order` |
| `knowledge_check_attempts` | Score, pass, answers. The answer key is not returned |
| `assessments` | Exactly one of module, course, or path |
| `assessment_questions` | Same kinds, plus `code` |
| `assessment_attempts` | Score, pass, XP awarded |
| `bookmarks` | Learner and page |
| `page_notes` | Learner notes on a page |
| `page_progress` | `seen` or `completed`, seconds spent |

Columns added to existing tables: `learning_paths.academy_id`, `position`, `xp_reward`, `gated`; `courses.path_id`, `academy_id`, `position`, `pass_score`, `xp_reward`; `modules.slug`, `summary`, `pass_score`; `lessons.summary`, `objectives`.

## 3. Information architecture

Learner App routes:

| Route | Screen |
| --- | --- |
| `/academies` | World: every learning path, filtered by faculty and level |
| `/academies/{slug}` | Learning paths. A gated path is not a link until the previous path is complete |
| `/paths/{slug}` | Courses in the path, path assessment, next path |
| `/courses/{slug}` | Modules and the course assessment |
| `/modules/{slug}` | Lessons and the module assessment |
| `/learn/{lesson}/{page}` | Topic page |
| `/assessments/{id}` | Module, course, or path assessment |

The Learn item in the shell covers academies, paths, courses, modules, lessons, and assessments.

## 4. Content Studio

`/studio/journey` lists academies, paths, and courses. An author adds a topic page to a lesson by slug. A page is one unit in order: reading, video, interactive exercise, knowledge check, or summary. A video or exercise points at a Resource Catalog record. Related papers, datasets, repositories, and links are attached the same way, through `POST /content/journey/resources`, which stores a catalog id rather than a copied URL.

Staff API:

- `GET /api/v1/content/journey`
- `POST /api/v1/content/journey/pages`
- `POST /api/v1/content/journey/pages/reorder`
- `POST /api/v1/content/journey/resources`

Seed-owned pages are refreshed on API start. A page an author edits is marked `authored` and is left alone on the next seed. Reorder must list every page of the lesson once.

## 5. User stories

- As a learner I open World and see every learning path. Faculty and level filter the list; academies are a filter, not the first page.
- As a learner I open Reinforcement Learning Academy and see RL Foundations, Deep RL, Policy Optimization, and Advanced RL. Only RL Foundations is open.
- As a learner I open RL Foundations, then Markov Decision Processes, then States & Actions, then What is a State?
- As a learner I move Previous and Next through introduction, formal definition, a real example, the mathematical form, a visualization, a summary, and a knowledge check.
- As a learner I see immediate feedback on a check, and I cannot mark that page complete until I pass.
- As a learner I bookmark a page and keep notes on it.
- As a learner I take the module assessment, then the course assessment, then the path assessment. Passing the path awards XP and the path badge and opens the next path.
- As an author I add a page and a resource and preview the lesson in the Learner App.
- As an admin I see completed lessons, drop-off pages, assessment pass rates, course and path completion, and time on lesson.

## 6. APIs

All `/api/v1/learn/*` routes require a signed-in learner. Answer keys stay on the server.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/learn/world` | Paths with faculty, level, and academy filters. Default is unfiltered |
| GET | `/learn/academies` | Academy cards (Settings goal picker). Not the World list |
| GET | `/learn/academies/{slug}` | Paths, locked when gated |
| GET | `/learn/paths/{slug}` | Courses, assessment, next path. 409 if the path is still locked |
| GET | `/learn/courses/{slug}` | Modules |
| GET | `/learn/modules/{slug}` | Lessons and the first page link |
| GET | `/learn/lessons/{lesson}/pages/{page}` | The reading screen, outline, objectives, resources, notes, bookmark, progress |
| GET | `/learn/continue` | Resume the last unfinished page, or the start of What is a State? |
| POST | `/learn/pages/{id}/complete` | `{ "seconds": 0 }` records time and completion. 409 if the knowledge check is not passed |
| POST | `/learn/pages/{id}/bookmark` | Toggles a bookmark |
| PUT | `/learn/pages/{id}/notes` | `{ "body": "..." }` |
| POST | `/learn/checks/{id}` | `{ "answers": [{ "question_id", "response" }] }` returns score, pass, and an explanation per item |
| GET | `/learn/assessments/{id}` | Questions without keys |
| POST | `/learn/assessments/{id}` | Grades the attempt |
| GET | `/admin/learning` | Admin only |

`GET /learning-paths` remains the flat catalog list.

## 7. UI

The topic page is three columns from the `lg` breakpoint, stacked on a phone.

- Left, sticky: module lesson list and the pages of the current lesson.
- Centre: breadcrumb, page count, estimated minutes, lesson progress, markdown, the check when this page is one, Previous and Next.
- Right, sticky: path, course, module, and lesson progress; objectives; related resources, further reading, and recommended research; notes.

Dark mode uses the existing slate tokens. Progress meters expose `role="meter"`. The breadcrumb marks the current page with `aria-current="page"`.

## 8. Navigation flow

```text
Dashboard "Continue" or Learn
  → World (all paths; Faculty and Level filters)
    → Learning path
      → Course
        → Module
          → Lesson page 1
            → Next → … → Knowledge check
              → Lesson complete
                → Module assessment (70%)
                  → Course assessment
                    → Path assessment
                      → Badge, XP, next path unlocks
```

## 9. Progress

Tracked at academy, path, course, module, lesson, and topic page. A lesson percent is completed pages over pages. A module, course, path, and academy percent is the mean of the level below. Time on a page is the seconds the client sends when the learner moves on. XP and assessment scores are on the attempt and on the learner's XP ledger.

## 10. Authoring workflow

1. Open Content Studio → Journey.
2. Add a topic page to a lesson slug, or add an http(s) resource.
3. Reorder pages with `POST /content/journey/pages/reorder` when the sequence should change.
4. Preview `/learn/{lesson}/{page}` in the Learner App.
5. A knowledge-check page needs questions. The seed writes them. An empty check returns 422 until questions exist. Adding question editing in the form is the next authoring step; the API and tables already store the questions.

Apply the schema with `make migrate` on PostgreSQL. Development SQLite creates the tables on API start and seeds the academy in the same step.
