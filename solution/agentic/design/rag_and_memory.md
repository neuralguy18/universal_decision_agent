# RAG + Memory (Document)

## Overview
The Retriever agent integrates with the MemoryRepository and with a small KB. Flow:

1. **Query expansion**: Use `Retriever.make_query()` to produce a short query from ticket text. In production, this should be a small LLM call that extracts entities & reformulates the user's question into a focused retrieval query.

2. **Memory search**: MemoryRepository.semantic_search(query) calculates an embedding for the query (via `embedding_fn`) and:
   - If Postgres + PGVector available: run SQL vector similarity search (use `<->` or cosine operator) for speed and scalability.
   - Otherwise, fallback to Python-based similarity: loads rows with embeddings (JSON column) and computes cosine similarity in memory (suitable for small datasets / dev).

3. **KB fallback**: if no memory hits or memory not configured, fallback to naive keyword search across `data/external/kb/*.txt` returning top-K text snippets.

4. **Return results**: `Retriever.retrieve()` returns list of docs: `{ source: "memory"|"kb", id, score, text, metadata }`

## How to enable PGVector (recommended for production)
- Use Postgres + PGVector extension.
- In `LongTermMemory` replace `embedding` JSON with `vector` column (PGVector).
- Use SQL query:
  ```sql
  SELECT id, text, metadata_json, 1 - (embedding <#> query_embedding) as score
  FROM long_term_memory
  ORDER BY embedding <-> query_embedding
  LIMIT k;
