# ADR 0007 — RAG architecture

- Status: Accepted (amended 2026-10-13)
- Date: 2026-10-13

## Context

Learners upload a PDF, DOCX, Markdown, or text file and ask questions about that file. The product also needs summarisation, equation extraction, critique, gap finding, and suggestions for future work. A fluent model will invent those sections if it is allowed to answer from memory.

## Problem

Design retrieval so that a paper analysis stays inside the uploaded document, and so that a missing model does not become a fabricated review.

## Decision

Ingestion is synchronous in the API process:

1. Reject files over 10 MB.
2. Parse PDF, DOCX, Markdown, or plain text. Scanned pages are not OCR’d.
3. Chunk at 800 characters with 120 characters of overlap.
4. Store each chunk in Postgres with a citation label such as `[1]`.
5. Embed the chunk and store the point in Qdrant, or record `hash-v1` when Qdrant is absent. See ADR 0004.

Analysis embeds the question, ranks the document’s chunks by cosine similarity, and keeps four excerpts. The research agent may write a summary, critique, gaps, and future work. Critique, gaps, and future work are kept only when `grounded()` finds a supplied citation label in the model text. Otherwise those fields are null.

With no usable model output, the mode is `extractive`: the summary is quoted excerpts, equations are `$...$` and `$$...$$` spans from the file, and the response includes `limitations_of_this_pass`. Chat does not analyse a paper that was not uploaded. The orchestrator tells the learner to use the research page.

Document text is fenced before it is placed beside instructions. The security prompt is composed into the model call.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| Let the model answer from parametric memory and “use the PDF as context” | The model still fills gaps. The product would ship invented critiques. |
| A single vector store with no chunk text in Postgres | Recovery and citations would depend on Qdrant payloads. Postgres is the copy learners can be quoted from. |
| A background OCR and embedding pipeline on day one | There is no worker. Scanned PDFs are an explicit non-goal until a queue exists. |
| One shared corpus for every learner | Papers are private. Queries filter to the caller’s document. |

## Trade-off analysis

Grounding trades completeness for honesty. An extractive pass looks sparse. It does not attribute a methodology flaw the PDF never stated. Research-question grades elsewhere are capped at 0.70 for the same reason: an open critique is not a fully automatic mark.

Synchronous ingestion is simple and transactional with the chunk rows. A large PDF occupies a request worker. The 10 MB cap and, later, a Front Door concurrency limit are the controls. See ADR 0006.

Hash retrieval finds lexical overlap. Production semantic ranking requires the HTTP Qdrant URL and a successful provider embedding. Mixing those spaces is a hard error.

Top-four excerpts can miss a claim that sits in chunk five. The citation label still tells the learner which passage was used. Raising the count is a product change, not a silent expansion.

## Consequences

- `POST /api/v1/research/documents` and `POST /api/v1/research/analyze` are the only analysis path.
- Equations outside dollar delimiters are not returned as equations.
- A Qdrant or model failure leaves the file in Postgres. Extractive mode still answers.
- Uploaded text is untrusted. It cannot override the security prompt by being retrieved.

## Future considerations

- Add a queue and OCR only after the API replica is no longer the parser.
- Re-embed when the embedding model changes. See ADR 0004.
- Show the learner which excerpt was dropped because it lacked a citation, so “withheld” is inspectable.

## Amendment — 2026-10-13 hardening

This replaces the parts of the decision above that no longer hold.

- Chunk labels are `#1`, `#2`, …; library citations in tutor replies are `[S1]`…`[S6]`.
- At ingestion, all chunks are embedded in one batched call and upserted to `learner_docs_v1` with the owner and document id. If indexing fails the document is stored with status `unindexed`.
- Analysis embeds the question once and searches with the owner-and-document filter; results are re-checked against the document in Postgres. If the index is unavailable, analysis uses the document's opening passages and says so.
- The curated library is retrievable: a published asset is chunked and indexed in `knowledge_v1`, filtered to `status = published`, and removed from the index when archived or returned to draft. Direct-mode tutor replies list up to six passages scoring at least 0.30, at most three per asset.
- Uploads are limited to 10 an hour per learner.
- Ingestion is still synchronous in the request (Security-Compliance SEC-13). That remains the main open item.
