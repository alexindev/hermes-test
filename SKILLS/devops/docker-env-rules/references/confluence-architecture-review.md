# Confluence Architecture Review Patterns

## Session 2026-06-03: AI Helper Architecture Review

### Page inspected
- **Title:** "AI Helper - Архитектура АС - целевая" (pageId=231594712)
- **Space:** AIS (Артефакты АС)
- **Version:** 5, template v3.0

### Findings
- Only section 3.1 (component diagram) has real content — PlantUML with Ollama, n8n, pgvector, VK Teams integrations
- Section 4 ("Сетевая связность") is completely missing — page jumps from section 3 to section 5
- All other sections are empty template tables with no data filled in
- `pageapproval` macro present but no approvers named, no comments, no labels
- Date updated field is blank

### Red flags for architecture reviews
1. Empty template tables with placeholder text like "Пример: bus_object_id_1_client" still present
2. Missing section numbering (jumps from 3 to 5)
3. No approvers named in approval macro — only role titles
4. No comments on the page
5. Blank metadata fields (date, version)

### MCP limitation
Confluence pages >50KB get truncated by `mcp_atlassian_confluence_get_page`. Use browser tool or raw HTML fetch (`convert_to_markdown=false`) for full content.
