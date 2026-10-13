# Developer documentation standards

These rules cover comments and reference docs for the AI Mentor API and studio. Write for the next person who has to change a teaching rule, a route, or a screen.

Two tools generate reference HTML from source:

| Language | Tool | Style in source |
| --- | --- | --- |
| Python | Sphinx with `sphinx.ext.napoleon` and `sphinx.ext.autodoc` | Google-style docstrings |
| TypeScript | TypeDoc | TSDoc (`/** ... */`) |

Hand-written docs stay in `docs/`. The HTTP contract is [openapi.yaml](openapi.yaml). The narrative API guide is [API.md](API.md). The system description is [Architecture.md](Architecture.md).

## Contents

1. [Python docstring standards](#1-python-docstring-standards)
2. [TypeScript documentation standards](#2-typescript-documentation-standards)
3. [API documentation standards](#3-api-documentation-standards)
4. [Class documentation templates](#4-class-documentation-templates)
5. [Module documentation templates](#5-module-documentation-templates)
6. [Architecture documentation standards](#6-architecture-documentation-standards)
7. [Code comment standards](#7-code-comment-standards)
8. [Examples](#8-examples)

## What to document

Document a symbol when a reader cannot recover the rule from the type signature and the name.

| Write a docstring or TSDoc block | Leave it undocumented |
| --- | --- |
| Every public module in `backend/app` | Tests, migrations, and generated files |
| Public functions in `domain`, `services`, `agents`, and `repositories` | Private helpers whose body is the whole explanation |
| Public classes, dataclasses, and exceptions | Pydantic fields that already carry `Field(description=...)` |
| Exported functions, classes, and hooks in `apps/*/lib` and `apps/*/components` | JSX that names the control it renders |
| A route, in [openapi.yaml](openapi.yaml), whenever the HTTP shape changes | A restatement of the parameter types |

The first sentence is the summary. It stands alone in the Sphinx or TypeDoc index. Keep it to one line, about 100 characters, and end it with a period.

## 1. Python docstring standards

Use Google-style docstrings. Napoleon turns them into Sphinx field lists (`:param:`, `:returns:`, `:raises:`). Do not write the reStructuredText fields by hand.

A docstring is a triple-quoted string. Public functions and classes use `"""`. One-line module summaries use the same quotes on a single line.

### Summary and body

1. Summary sentence: what the callable guarantees, in the present tense.
2. Blank line.
3. Body: the rule a caller would get wrong. Include weights, caps, identity boundaries, and ordering.
4. Blank line.
5. `Args`, `Returns`, `Yields`, `Raises`, and `Examples`, in that order. Omit a section that would be empty.

Types live in the annotations. The `Args` text adds the constraint the annotation cannot say: units, ranges, ownership, or which side of a relationship the value is.

### Sections

| Section | Use |
| --- | --- |
| `Args` | One parameter per line, `name: explanation`. Skip `self` and `cls`. |
| `Returns` | What the value means, including sentinel values such as `None` when every provider failed. |
| `Yields` | For generators and context managers, what the caller receives inside the block. |
| `Raises` | Exceptions the caller is expected to handle. Name the type, then the condition. |
| `Examples` | One short, valid snippet. The pytest suite remains the proof. |

Document `ValueError`, `ClientError`, and `SandboxPolicyError` when this function raises them. Do not list `Exception` from a broad `except`.

### Attributes and constants

Classes that store state use an `Attributes` section for public attributes. A module constant with a non-obvious meaning gets a one-line docstring on the assignment only when the name is insufficient. Prefer a short comment above the constant when a docstring would not be picked up by autodoc (see [Code comment standards](#7-code-comment-standards)).

### Sphinx build

Place this next to a future `docs/conf.py` when a Sphinx build is added. The docstring style above matches it.

```python
import os
import sys

sys.path.insert(0, os.path.abspath("../backend"))

project = "AI Mentor"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_use_rtype = True
autodoc_typehints = "description"
autoclass_content = "class"
```

`autodoc_typehints = "description"` prints the annotation once. Do not copy the type into the `Args` line.

### Canonical function

```python
def score_evidence(evidence: Evidence) -> int:
    """Renormalize mastery over the evidence that exists.

    Lessons count after the learner has engaged and the concept has a lesson.
    Projects count after an attempt, so an untouched lab does not lower the score.

    Args:
        evidence: Quiz ratios, lesson counts, project attempts, and recall.

    Returns:
        An integer from 0 through 100.
    """
```

## 2. TypeScript documentation standards

Use TSDoc on exported symbols. TypeDoc reads `/** ... */` and ignores `//` and `/* ... */`.

### Tags

| Tag | Use |
| --- | --- |
| First line | Summary sentence, same rule as Python. |
| `@remarks` | The rule behind the summary: auth header, caching, or a status the type hides. |
| `@typeParam` | A generic parameter, by name. |
| `@param` | `name - constraint`. Skip it when the identifier and the type are the whole story. |
| `@returns` | The value's meaning. Omit it on components that return JSX and have an obvious summary. |
| `@throws` | `{@link ApiError}` or another exported error, plus the condition. |
| `@defaultValue` | A default the signature does not show. |
| `@deprecated` | What to call instead. |
| `@see` | A related symbol or a `docs/` page. |
| `@example` | A fenced snippet. Keep it compilable. |

Do not restate TypeScript types in prose. `@param path - The path string` adds nothing. `@param path - Must start with /api/v1` does.

Props interfaces are documented on the component, not on every prop, unless a prop has a unit or a sentinel (`null` means "no conversation yet").

### TypeDoc build

```json
{
  "$schema": "https://typedoc.org/schema.json",
  "entryPoints": ["apps/learner/lib", "apps/learner/components", "apps/learner/stores"],
  "entryPointStrategy": "expand",
  "exclude": ["**/*.test.ts", "**/*.test.tsx"],
  "tsconfig": "apps/learner/tsconfig.json",
  "excludePrivate": true,
  "excludeInternal": true
}
```

Mark a symbol `@internal` when it is exported only for tests. TypeDoc will drop it.

### Canonical function

```ts
/**
 * Calls one API path and returns the JSON body.
 *
 * @remarks
 * In development, sends `X-Dev-User-Id` from the studio store when
 * `NEXT_PUBLIC_DEV_AUTH` is `true`. Sets `Content-Type: application/json`
 * for string bodies.
 *
 * @typeParam T - Expected JSON body.
 * @param path - Absolute API path, starting with `/api/v1` or `/health`.
 * @param init - Fetch options. Defaults to `GET` with no body.
 * @returns The parsed JSON body.
 * @throws {@link ApiError} When the status is not OK. `message` is the `detail` string.
 */
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  // ...
}
```

## 3. API documentation standards

[openapi.yaml](openapi.yaml) is the contract frontend and backend share. [API.md](API.md) is the short reading guide: auth, which routes are public, and the shapes people mix up. A generated `GET /openapi.json` from the running process describes live routes only. When the two differ, `openapi.yaml` is the one to edit, and the handler is the one to implement.

### On every operation

| Field | Required content |
| --- | --- |
| `operationId` | Stable camelCase name. Do not rename it once a client ships. |
| `summary` | One sentence, under 80 characters. |
| `description` | Who may call it, what is persisted, and the domain rules. |
| `x-implementation` | `live` only when a handler exists. Otherwise `contract`. |
| `x-required-role` | `public`, `student`, `instructor`, or `admin`. |
| `x-rate-limit-tier` | `exempt`, `standard` (60/min), `ai` (20/min), or `upload` (10/hour). |
| Parameters and body | JSON Schema bounds: `minLength`, `maxLength`, `enum`, `format`. |
| Responses | Every status the handler returns. Errors use the shared `application/problem+json` responses (`Problem`, `ValidationProblem`). |
| Security | `security: []` on public routes and webhooks. Inherited Clerk bearer otherwise. |

Validation that Pydantic rejects is `422`. A rule the handler decides is `400` with a finished sentence in `detail`. Use `404` when the row is missing or belongs to someone else, so existence of another user's row is not leaked.

### Handler docstrings

A route function may carry a one-line docstring. That line must match the OpenAPI `summary`. The long rules stay in `openapi.yaml`, so they are not maintained twice. Request and response models use Pydantic `Field` for bounds the schema must enforce.

```python
class ChatIn(BaseModel):
    """One tutor turn."""

    message: str = Field(min_length=1, max_length=8000)
    conversation_id: uuid.UUID | None = None
    mode: Literal["socratic", "direct"] = "socratic"
```

### Narrative guide

`API.md` stays short. Update it when a route is added, when auth changes, or when a response field is easy to misuse (answer keys, citation fields, dev auth). Do not paste full schemas into `API.md`. Link the operation in `openapi.yaml` by path.

Webhook sections name the signature header, the secret variable, and the event types the handler acts on. Other event types are acknowledged and ignored, and the doc says so.

### Operation sketch

```yaml
/api/v1/chat:
  post:
    tags: [Chat]
    operationId: postChat
    summary: Send a tutor turn.
    description: |
      Appends the learner message and one assistant reply. Omitting
      `conversation_id` starts a conversation.

      Rules:
      - `message` is trimmed, length 1–8000, and rejected when it is only
        a prompt-injection phrase.
      - `conversation_id`, when set, must belong to the caller.
    x-implementation: live
    x-required-role: student
    x-rate-limit-tier: ai
```

## 4. Class documentation templates

Copy the section headings. Delete any heading that does not apply.

### Python class

```python
class ProviderRouter:
    """Chooses a configured model provider and returns its text.

    Providers run in a fixed order: OpenAI, Anthropic, then Gemini.
    A provider that raises or returns blank text is skipped. When every
    provider fails, callers receive None and use the catalog text.

    Attributes:
        settings: Process settings. API keys decide which providers run.
    """

    def __init__(self, settings: Settings) -> None:
        """Store settings. No network call is made here.

        Args:
            settings: Loaded process settings.
        """
        self.settings = settings

    def complete(
        self,
        *,
        system: str,
        messages: list[tuple[str, str]],
        max_tokens: int = 700,
    ) -> str | None:
        """Ask the first working provider for a completion.

        Args:
            system: Instructions for this turn, already including the security prompt.
            messages: Role and text pairs, oldest first. Roles are `user` or `assistant`.
            max_tokens: Upper bound passed through to the provider.

        Returns:
            Stripped text, or None when no provider returned text.
        """
```

`__init__` needs a docstring only when construction has a rule (no I/O, a default that matters). A dataclass with a class docstring does not need an `__init__` docstring.

### Python dataclass

```python
@dataclass(frozen=True)
class Evidence:
    """Counts and ratios that feed one concept's mastery score.

    Attributes:
        quiz_scores: Ratios from 0 through 1, oldest last. Empty when none exist.
        lessons_completed: 0 or 1 for the concept's single lesson.
        lessons_available: 1 when the catalog has a lesson for this concept.
        projects_passed: Submissions whose status is `ok`.
        projects_attempted: Submissions stored for this concept, including failures.
        recall: Mean flashcard ease signal, or None when the learner has no cards.
    """

    quiz_scores: tuple[float, ...] = ()
    lessons_completed: int = 0
    lessons_available: int = 0
    projects_passed: int = 0
    projects_attempted: int = 0
    recall: float | None = None
```

### Python exception

```python
class ClientError(Exception):
    """A domain failure the API turns into an HTTP response.

    Attributes:
        message: Sentence returned as JSON `detail`.
        status_code: HTTP status. Defaults to 400.
    """

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
```

### TypeScript class

```ts
/**
 * Failure from an API response that was not OK.
 */
export class ApiError extends Error {
  /**
   * HTTP status from the response.
   */
  readonly status: number;

  /**
   * @param status - HTTP status.
   * @param message - API `detail`, or the status text when the body is not JSON.
   */
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}
```

Document the class and any field whose name is ambiguous. The constructor is documented when its arguments are not obvious from the class summary.

## 5. Module documentation templates

Every Python module under `backend/app` starts with a module docstring before imports. Say what the module owns, and the boundary it refuses to cross.

### Python module

```python
"""Socratic policy.

The model may phrase a later turn. Stages 0 and 1 are scripted from the
catalog, so a chatty model cannot dump the definition on the opening turn.
"""

from __future__ import annotations
```

A one-liner is enough when the name and the sentence match:

```python
"""Pure teaching, scoring, and safety rules. No database or network imports."""
```

### Python package

`__init__.py` documents the package, not the file layout.

```python
"""HTTP adapters.

Routes validate bodies and call MentorEngine. They do not grade, score, or
choose a teaching stage.
"""
```

Re-exports get an `__all__` list. Each re-exported name keeps the docstring from its defining module. Do not copy that docstring into `__init__.py`.

### TypeScript module

A file-level TSDoc block sits above the imports when the file has a rule that no single export owns. Page files use this when the screen's data contract matters.

```ts
/**
 * Tutor studio.
 *
 * @remarks
 * Posts to `/api/v1/chat`. Socratic is the initial mode. The conversation id
 * from the first reply is sent on later turns. Notes stay in the studio store
 * and are not sent to the API.
 */
```

A file that only exports well-named functions does not need a file-level block. Each export still follows [section 2](#2-typescript-documentation-standards).

## 6. Architecture documentation standards

[Architecture.md](Architecture.md) describes the system as it runs. Product intent stays in [Requirements.md](Requirements.md) and [Admin.md](Admin.md). Route tables stay in [API.md](API.md).

### Required shape

Keep these sections, in this order, when you edit the architecture doc:

1. One paragraph: what kind of system this is (a modular monolith, one deployable API).
2. A Mermaid flowchart of the request path from browser to database.
3. A layer table: directory, responsibility, and what that layer must not import.
4. Teaching policy: stages, grading, mastery weights, XP, and level formula.
5. Identity: who proves the user, where the role is stored, and how dev auth behaves.
6. Retrieval and code execution: limits a caller can trip.
7. A short "current boundaries" section: queues, OCR, and other work this process does not do.
8. One sequence diagram for the main tutor turn.

### Diagrams

Use Mermaid fences (` ```mermaid `). One diagram, one path. Name participants with the words used in the layer table (`Learner App`, `API`, `Engine`, `Policy`). Do not draw a service that is not a process. "Studio" in architecture diagrams means Content Studio only.

Update the diagram in the same change as the dependency it shows. A new agent class does not need a new box. A new datastore does.

### Decisions

Record a decision in `Architecture.md` when it changes where code lives or how a request is served. Write it as the current rule:

> Roles are stored on `users.role`. A Clerk token updates that role only when the token carries a role claim.

Add a dated note at the bottom of `Architecture.md` only for a decision that is easy to undo and costly to misunderstand. Include the date, the choice, and the constraint that made it. Do not keep a second decision log.

### Platform documents

Target-state documents for the five-application ecosystem live in [platform/](platform/README.md). They follow three extra rules:

1. Names come from [platform/README.md](platform/README.md): applications, roles, scopes, permissions, content states, modules, events, schemas, API roots, and release labels. Change a name there first, then in the documents that use it, in the same pull request.
2. Every platform document opens with a metadata table and a **Change record** table with the columns Area, What changed, Why, Impacted systems, and Implementation implications.
3. Every platform document has a **Relationship to v1 documents** section saying which v1 sections it retains, amends, or supersedes. The superseded v1 document carries a one-paragraph amendment notice under its title.

`Architecture.md`, `API.md`, `Database.md`, and `Security.md` keep describing the running code. Do not copy target-state text into them.

### Layer rules worth repeating

| Layer | May import | May not import |
| --- | --- | --- |
| `app/domain` | The standard library and other domain modules | FastAPI, SQLAlchemy, HTTP clients, `app.services` |
| `app/api` | Pydantic, domain types, the engine | SQL text, prompt strings |
| `app/services` | Domain, repositories, providers | React or studio code |
| Learner App (`apps/learner`) | The API over HTTP | Python modules, the database. It must not render Instructor, Institution, Admin, or Content Studio routes |

When a change breaks one of these rows, update the table in the same pull request.

## 7. Code comment standards

Comments are for invariants the language cannot express. Docstrings and TSDoc explain the public contract. Comments explain a local constraint.

### Write a comment when

- A literal is a limit from a product rule (`10 * 1024 * 1024`, daily XP cap, three-second timeout).
- A branch exists because of a security or privacy rule.
- A call looks redundant and is required (signature verify before parse, user id in the query so another learner's row 404s).
- A workaround depends on a library behavior, with the version or the reason.

### Leave the line uncommented when

- The comment repeats the function name or the type.
- The comment describes the ticket instead of the behavior.
- The code is commented out. Delete it. Git has the history.

```python
# 10 MiB matches the research upload cap documented on POST /research/documents.
raw = file.file.read(10 * 1024 * 1024 + 1)
```

```ts
// Dev auth is a header, never a role. Production builds leave this unset.
if (process.env.NEXT_PUBLIC_DEV_AUTH === "true" && devUser) {
  headers.set("X-Dev-User-Id", devUser);
}
```

### Markers

| Marker | Meaning |
| --- | --- |
| `TODO:` | Work this tree still needs, in one sentence, with the condition that makes it done. |
| `SECURITY:` | A control a refactor must not drop. |

```python
# TODO: share the rate limit across API replicas before running more than one instance.
```

```python
# SECURITY: user id is part of the predicate so a guessed id returns 404.
found = engine.repo.conversation(conversation_id, user.id)
```

Do not use `FIXME`, `XXX`, or an author name in the marker. Do not comment out a secret, a key, or a learner's real text as an example.

### Prompts

Prompt files in `backend/app/prompts/` are product copy, not code comments. A change to a prompt that alters a teaching stage is described in the domain docstring that loads it, and in `Architecture.md` when the stage rule changes.

## 8. Examples

The templates above cover the common function, class, dataclass, exception, and module. The rest of this section is the remaining structures in the forms Sphinx and TypeDoc accept.

### Python function that raises

```python
def build_turn(
    message: str,
    history: list[HistoryTurn],
    mode: str,
    sticky_slug: str | None = None,
) -> TurnPlan:
    """Choose the socratic stage and the catalog text for this turn.

    Stage is the number of assistant messages already stored. The concept
    is the one named in `message`, otherwise `sticky_slug` from earlier turns.

    Args:
        message: Learner text, already screened.
        history: Prior turns, oldest first. Only the caller decides the window.
        mode: `socratic` or `direct`.
        sticky_slug: Concept from the previous turn, if any.

    Returns:
        The stage, concept, system note, and fallback paragraph.

    Raises:
        ValueError: If `mode` is not `socratic` or `direct`.
    """
```

### Python context manager

```python
@contextmanager
def session_scope() -> Iterator[Session]:
    """Yield a session and commit it if the block returns.

    Yields:
        An open SQLAlchemy session bound to the process engine.

    Raises:
        Exception: Re-raises any exception from the block after rollback.
    """
```

### Python constant

```python
# Mastery at or above this score is the strength band on the dashboard.
STRENGTH_AT = 75

# Scores at or above this value and below STRENGTH_AT are developing.
GAP_BELOW = 60
```

Constants used by autodoc as public aliases may use an attribute docstring instead:

```python
XP_PER_LEVEL: int = 250
"""XP required to advance one level. Level is `1 + xp // XP_PER_LEVEL`."""
```

### Pydantic request model

```python
class GradeIn(BaseModel):
    """Answers for one owned quiz.

    At most 20 answers. Duplicate question ids are ignored by the grader.
    """

    answers: list[AnswerIn] = Field(min_length=1, max_length=20)


class AnswerIn(BaseModel):
    """One response. The answer key is not accepted from the client."""

    question_id: uuid.UUID
    response: str = Field(max_length=20000)
```

### FastAPI route

```python
@router.post("/quiz/{quiz_id}/grade")
def grade_quiz(
    quiz_id: uuid.UUID,
    body: GradeIn,
    user: User = Depends(_user),
    engine: MentorEngine = Depends(_engine),
) -> dict:
    """Grade a quiz the caller owns."""
    return engine.grade_quiz(user, quiz_id, [item.model_dump() for item in body.answers])
```

The matching contract text, statuses, and the note that explanations appear only in this response belong in `openapi.yaml` under `operationId: gradeQuiz`.

### TypeScript type alias and interface

```ts
/**
 * One rendered tutor turn. `user` rows are local until the server echoes them.
 */
export type Turn = {
  role: "user" | "assistant";
  content: string;
};

/**
 * JSON body of `POST /api/v1/chat`.
 */
export interface ChatReply {
  /** Server id to send on the next turn. */
  conversation_id: string;
  /** `socratic` or `direct`, as applied by the server. */
  mode: "socratic" | "direct";
  /** Assistant messages that existed before this reply. */
  stage: number;
  /** Catalog concept detected for this turn, if any. */
  concept_slug: string | null;
  reply: {
    id: string;
    role: "assistant";
    content: string;
  };
}
```

Use `interface` for an object the server owns and that other types extend. Use `type` for a union, a tuple, or a small local shape.

### React component

```tsx
/**
 * Socratic or direct tutor for the signed-in learner.
 *
 * @remarks
 * The first successful reply stores `conversation_id` and invalidates the
 * dashboard query. Empty drafts are not sent.
 */
export function TutorPanel(): JSX.Element {
  // ...
}
```

Page components in `apps/*/app` may use the file-level block from [section 5](#5-module-documentation-templates) instead of repeating it on the default export.

### Hook

```ts
/**
 * Selected dev user and the notes scratchpad.
 *
 * @remarks
 * Notes are local UI state. They are not part of the chat request body.
 *
 * @returns The store slice used by studio pages.
 */
export function useStudioNotes(): {
  notes: string;
  setNotes: (notes: string) => void;
} {
  const notes = useStudio((state) => state.notes);
  const setNotes = useStudio((state) => state.setNotes);
  return { notes, setNotes };
}
```

### OpenAPI error

Pair each domain failure sentence with the status the handler uses.

```yaml
"404":
  description: The conversation does not exist for this caller.
  content:
    application/json:
      schema:
        $ref: "#/components/schemas/Error"
      example:
        detail: Conversation not found.
```

`Error` is `{ "detail": string }` and `additionalProperties: false`. A new `detail` sentence is added to the operation description when the client must branch on it.

### Architecture layer row

When a new directory is added under `backend/app` or `apps/`, add one row to the layer table in `Architecture.md`:

```markdown
| `app/repositories` | Queries. Routes do not write SQL. | FastAPI response models |
```

### Review checklist

- The summary sentence is true without the rest of the docstring.
- Args text states a constraint the type does not.
- Raised errors match the `raise` statements.
- A changed route updates `openapi.yaml` and, if the guide would mislead, `API.md`.
- A changed layer or teaching weight updates `Architecture.md`.
- Comments explain a limit, a security predicate, or a non-obvious requirement.
- Examples compile, and they contain no secrets and no real learner data.
