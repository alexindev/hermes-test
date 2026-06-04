# PR Review Checklist

Systematic categories for reviewing code before merge. Copy this into any PR review session.

## A. Imports & References
- All imported modules exist (no missing files, no typos)
- No unused imports
- No circular imports
- Router references only defined routers

## B. Type & Schema Correctness
- Model field types match actual DB schema
- Column defaults match DB defaults (Python-side vs server-side)
- Pydantic schemas align with API response shapes
- Foreign keys reference existing tables

## C. Error Handling & Resilience
- HTTP responses check `.ok` before `.json()`
- Network calls have timeout/retry handling
- Database queries handle empty results gracefully
- Frontend shows loading + error states

## D. Performance & Scaling
- Queries use LIMIT/OFFSET or cursor pagination
- No N+1 query patterns
- Large datasets handled with pagination
- Static assets have caching headers

## E. Configuration & Infrastructure
- Secrets not hardcoded (use .env, env vars)
- Docker Compose has healthchecks for dependencies
- Nginx/Apache proxy forwards X-Forwarded-For, X-Real-IP
- .gitignore excludes secrets, node_modules, __pycache__

## F. Documentation Consistency
- README matches actual API endpoints
- Code comments reflect current behavior
- No stale examples or dead links

## Severity Levels
| Level | Impact | Action |
|-------|--------|--------|
| 🔴 Critical | Code won't run / data corruption | Must fix before merge |
| 🟡 Serious | Runtime errors / bad UX | Should fix, document if deferred |
| 🟢 Nice-to-have | Style / optimization | Can defer |
