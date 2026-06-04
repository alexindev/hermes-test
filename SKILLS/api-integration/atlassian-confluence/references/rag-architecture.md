# RAG Architecture for Confluence Semantic Search

## Overview

Full semantic search pipeline over Confluence pages using pgvector for vector storage and an LLM for answer synthesis.

```
                          ┌─────────────────────┐
                          │   Confluence API     │
                          │ (mcp-atlassian/CQL)  │
                          └──────────┬──────────┘
                                     │ fetch pages
                                     ▼
                          ┌─────────────────────┐
                          │   Chunking Engine    │
                          │ (by heading, token)  │
                          └──────────┬──────────┘
                                     │ text chunks
                                     ▼
                          ┌─────────────────────┐
                          │   Embedding Model    │
                          │ (OpenRouter/local   │
                          │  vLLM)              │
                          └──────────┬──────────┘
                                     │ vectors
                                     ▼
                ┌────────────────────────────┐
                │    PostgreSQL + pgvector    │
                │  - chunks table             │
                │  - vector(1536) column       │
                │  - IVFFlat index             │
                └──────────┬─────────────────┘
                                     ▲
                          ┌──────────┴──────────┐
                          │  Query Pipeline     │
                          └──────────┬──────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
          ▼                          ▼                          ▼
  ┌────────────────┐      ┌──────────────────┐      ┌──────────────────┐
  │ User Query     │      │ Embedding Model  │      │     LLM          │
  │ (natural lang) │─────▶│ (same as index)  │─────▶│ (answer with    │
  └────────────────┘      └──────────────────┘      │  citations)     │
                                                     └──────────────────┘
```

## Database Schema

```sql
-- Requires: CREATE EXTENSION vector;

CREATE TABLE confluence_chunks (
    id            SERIAL PRIMARY KEY,
    page_id       INTEGER NOT NULL,
    page_title    TEXT NOT NULL,
    page_url      TEXT,
    space_key     TEXT,
    chunk_index   INTEGER NOT NULL,
    chunk_text    TEXT NOT NULL,
    embedding     vector(1536),
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON confluence_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX ON confluence_chunks (space_key);
CREATE INDEX ON confluence_chunks (page_id);
```

## Embedding Model Options

| Model | Dims | Cost | Source |
|-------|------|------|--------|
| `text-embedding-3-small` | 1536 | $0.02/1M tokens | OpenRouter / OpenAI |
| `text-embedding-3-large` | 3072 | $0.13/1M tokens | OpenRouter / OpenAI |
| `text-embedding-ada-002` | 1536 | $0.10/1M tokens | OpenRouter / OpenAI |
| Local vLLM embedding | varies | Free | khd-llm-app01 |

## Chunking Strategy

Recommended: heading-based chunking with fallback to token-based.

```
Page content → split by h2/h3 headings → each section = 1 chunk
If section > 1500 chars → recursive split at paragraph boundaries
If paragraph > 1000 chars → split by sentences into 500-1000 char segments
```

Each chunk stores: chunk_text, page_id, page_title (source), chunk_index (ordering), space_key (filter).

## Query Pipeline

```
1. User asks question (natural language)
2. Generate embedding of query
3. Vector search: cosine_similarity(embedding) LIMIT 10-20
4. Optionally filter: WHERE space_key = 'ENG'
5. Re-rank by chunk_index per page (deduplicate, prefer earlier sections)
6. Format context: "Page: X (section Y)\n---\n{chunk_text}"
7. LLM prompt: "Answer based on context. Cite source pages."
```

## Periodic Re-indexing

Use a cronjob to keep the index fresh. Query recently modified pages via CQL:
```
text ~ "" AND lastModified >= startOfDay("-1d") ORDER BY lastModified DESC
```
Fetch changed pages, re-chunk, re-embed, UPSERT into pgvector.

## Pitfalls

- pgvector requires `CREATE EXTENSION vector` with superuser privileges
- text-embedding-3-small is usually sufficient for Confluence pages
- Chunk size sweet spot: 500-1000 chars per chunk
- CQL can still complement semantic search as a pre-filter (space, label)
- Re-indexing must handle deleted pages (mark inactive, don't just insert)
- Using local vLLM for embeddings may produce lower quality than dedicated embedding models