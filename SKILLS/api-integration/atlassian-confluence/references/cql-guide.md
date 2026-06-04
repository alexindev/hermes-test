# CQL (Confluence Query Language) Cheatsheet

CQL is Confluence's native search query language. Used with `confluence_search(query="...")`.

## Basic Syntax

```
field OPERATOR value [AND|OR field OPERATOR value ...]
```

## Text Search

| Pattern | Example | Description |
|---------|---------|-------------|
| `text~"phrase"` | `text~"onboarding guide"` | Full-text search (title + body + attachments) |
| `title~"word"` | `title~"deployment"` | Search in title only |
| `text~"word1 word2"` | | Multiple words (OR by default) |
| `text~"exact phrase"` | `text~"API rate limits"` | Exact phrase in quotes |

## Space & Type Filters

| Pattern | Example | Description |
|---------|---------|-------------|
| `space=KEY` | `space=ENG` | Pages in specific space |
| `space="My Space"` | | Space by name (with spaces) |
| `type=page` | `type=page` | Only pages (not blogs) |
| `type=blogpost` | | Only blog posts |

## Labels

| Pattern | Description |
|---------|-------------|
| `label=documentation` | Pages with label |
| `label="in progress"` | Label with space |
| `label IN (docs,archived)` | Multiple labels (OR) |

## Temporal Filters

| Pattern | Examples |
|---------|----------|
| `lastModified>=2025-01-01` | Modified after date |
| `lastModified<=2025-06-01` | Modified before date |
| `created=startOfDay("-7d")` | Created in last 7 days |
| `lastModified=startOfMonth()` | This month |
| `lastModified=endOfYear("-1y")` | Same time last year |

## Contributors

| Pattern | Description |
|---------|-------------|
| `creator=currentUser()` | Created by me |
| `contributor=currentUser()` | Any contribution by me |
| `contributor="john.doe@co.com"` | Specific user |
| `lastModifier=currentUser()` | Last edited by me |
| `creator IN ("user1","user2")` | Multiple creators |

## Combining Conditions

```
text~"deployment" AND space=OPS AND lastModified>=2025-01-01
label=documentation AND (space=ENG OR space=DEVOPS)
text~"API" AND contributor=currentUser()
```

## Ordering

```
text~"deployment" ORDER BY lastModified DESC
title~"guide" ORDER BY created ASC
```

## Common Patterns

| Use Case | CQL |
|----------|-----|
| Recent docs in a space | `space=ENG AND lastModified>=startOfMonth() ORDER BY lastModified DESC` |
| My recent edits | `contributor=currentUser() AND lastModified>=startOfDay("-14d")` |
| Pages by label | `label=howto AND type=page` |
| Stale pages | `lastModified<=startOfYear("-1y") AND space=ENG` |
| Cross-space search | `text~"deployment" AND type=page ORDER BY lastModified DESC` |

## Limits

- CQL is **keyword-based**, not semantic
- Max results typically 25-50 per page (pagination via `limit` + `cursor` params)
- Only searches indexed content (new pages may have indexing delay)