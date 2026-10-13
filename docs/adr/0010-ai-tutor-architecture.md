# ADR 0010 — AI tutor architecture

- Status: Accepted
- Date: 2026-10-13

## Context

AI Mentor has to act as a tutor, a Socratic teacher, a quiz author, a research assistant, a coding mentor, a study planner, and a career coach. The brief asked for a multi-agent system. It also asked the tutor not to hand over the answer on the first turn. “Teach me Reinforcement Learning” must open with “What do you think an agent does in an environment?”

## Problem

Decide how model calls, teaching policy, and specialist behaviours share one learner without letting a chatty model skip the pedagogy.

## Decision

The mentor engine is the use-case layer. Specialists are classes, not services:

| Agent | Owns | Does not own |
| --- | --- | --- |
| Tutor | Wording of a turn inside a `TurnPlan` | The decision to ask or to explain |
| Quiz | An optional `COACH:` note | The answer key and the grade |
| Research | A critique that must cite a chunk | The right to analyse an unuploaded paper |
| Coding | A narration of review notes | Execution. The sandbox runs the file |
| Planner | A prose explanation of a plan | The concept order |
| Career | A prose explanation of role matches | The match score |

`app/domain/socratic.py` builds the plan. Socratic stages 0 and 1 use the catalog’s scripted fallback, so a model cannot dump the answer on the opening turns. Direct mode, and socratic stage 3 and later, may include the full account. Later wording may come from a model. The provider router tries OpenAI, then Anthropic, then Gemini. A failure falls through. With no key, the scripted curriculum is the reply.

`app/agents/orchestrator.py` classifies intent. Career, plan, and quiz intents call the engine. Code and research intents return a pointer to the lab or the research page. Anything else is a socratic chat. Chat does not execute pasted code.

Prompts live in `backend/app/prompts`. The security prompt is composed into model calls. User text is length-limited and screened. A message that is only an injection attempt is rejected. A lesson question that mentions injection in passing is still allowed.

Grading is deterministic. Research questions are capped at 0.70. The lab runs only after an AST allowlist and then as `python -I` with a three-second timeout.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| One unconstrained chat prompt for every job | The model would answer immediately, invent quiz keys, and run or pretend to run code. |
| A framework that plans its own tool calls | Harder to test, and the tools include “grade” and “execute.” Those stay behind policies. |
| Microservices per agent | Rejected in ADR 0002. They would split the learner record. |
| Streaming the model token-by-token on the first turn | The first turn is a fixed question. Streaming it adds failure modes before the policy has spoken. |

## Trade-off analysis

Scripted openings are less flexible and more trustworthy. A learner who wants the answer immediately can switch to direct mode. The policy looks for phrases such as “just tell me” and can advance, but the default remains a question.

Fall-through across providers raises availability and can change voice between turns. The pedagogical content of the early stages does not depend on which provider answered.

Keeping specialists in-process makes an orchestration test a function call. It also means a slow model call holds an API worker. Timeouts and the AI rate limit are the present controls.

The coding agent narrates notes the deterministic reviewer already produced. If the model is down, the notes still return. The research agent is held to the same standard by ADR 0007.

## Consequences

- New tutor behaviour starts as a domain rule with a unit test, then a prompt change.
- `POST /api/v1/chat` returns `mode`, `stage`, `concept_slug`, and the reply.
- `POST /api/v1/agents/run` is a router, not a second tutor with weaker rules.
- Provider keys are optional. Teaching still happens.
- Langfuse receives traces only when both keys are set, and a Langfuse failure does not fail the turn.

## Future considerations

- Stream tokens after stage 2, with the policy string still fixed for stages 0 and 1.
- Add tools only by name, with the engine performing the side effect. The model does not receive a database handle or a shell.
- Evaluate tutor quality with a fixed set of openings, including the reinforcement-learning opener, on every prompt change.
