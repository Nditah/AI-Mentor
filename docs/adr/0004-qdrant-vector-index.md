# ADR 0004 — Qdrant as the vector index

- Status: Accepted
- Date: 2026-10-13

## Context

Research uploads are chunked and retrieved by similarity. The brief asked for a vector database. Learners also need a keyless local run, and tests must not depend on a live Qdrant or a paid embedding API.

## Problem

Choose where vectors live, and how the system behaves when Qdrant or an embedding provider is absent.

## Decision

Qdrant holds vectors when `QDRANT_URL` starts with `http`. Production refuses to start otherwise.

Postgres stores the chunk text and an `embeddings` row: provider, model, dimensions, and `qdrant_point_id`. The vector itself is not duplicated in Postgres.

When Qdrant is not configured, retrieval uses a deterministic 64-dimension hash embedding (`hash-v1`) recomputed at query time. That index is a hashing trick over tokens. It is not a semantic model. It keeps tests and the keyless demo on a single code path.

If an embedding API key is set and the provider call fails, embedding raises. The request does not silently mix a hash vector with an OpenAI vector.

Local Compose runs `qdrant/qdrant:v1.13.4`. Shared environments use Qdrant Cloud in the same region as the API. Chunk text in Postgres is sufficient to rebuild the collection.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| pgvector only | One fewer service. Retrieval load and filtering then sit on the primary learner database. |
| Pinecone or Weaviate | Capable products. Qdrant was already the brief, has a local container, and stores points we can rebuild. |
| Always call an embedding API | Breaks offline tests and makes a missing key look like an outage. The curriculum and extractive research path must work with no key. |
| Store the float vector in Postgres as well as Qdrant | Two copies drift. The point id is the link. |

## Trade-off analysis

Separating the index from the system of record makes Qdrant disposable. A bad deploy of the index does not lose the paper text, the quiz history, or the XP ledger.

The hash fallback will rank overlapping tokens, not paraphrases. Demonstrations and CI must not be described as semantic search. Production, where `QDRANT_URL` is HTTP and a provider key is set, uses the provider’s embedding space end to end.

Hash dimension is 64. Provider dimensions differ. The `embeddings.dimensions` column records which space a point belongs to. A change of embedding model is a reindex, not an in-place mix.

## Consequences

- Ingestion writes the chunk, then the embedding metadata, then the point.
- Analysis ranks chunks by cosine similarity and keeps the top four as citations. See ADR 0007.
- A Qdrant outage degrades research. It does not take down the tutor, quizzes, or the lab.
- The weekly snapshot is optional. Rebuild from `document_chunks` is the supported recovery.

## Future considerations

- Reindex as an explicit job when `EMBEDDING_MODEL` changes. Refuse queries that would compare two model names.
- Move to more than one Qdrant node only after the collection no longer fits in one node’s memory.
- Keep the hash path for tests after that reindex exists.
