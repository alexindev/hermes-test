# Large Confluence Page Handling

## Problem
Confluence pages >100KB are truncated by MCP tools (`confluence_get_page`, `confluence_get_page_history`). Content cuts off mid-section, making full analysis impossible.

## Detection

Signs a page was truncated:
- Content ends abruptly in the middle of a sentence or table
- Expected sections (e.g., section 4) are missing while 3 and 5 exist
- `read_file` on saved output shows "truncated" flag or content is cut at ~108KB
- Section headers found via regex don't match expected document structure

## Strategies

### Strategy 1: Browser (most reliable)
Navigate to the page in browser, then use `browser_snapshot(full=true)` or `browser_vision`.
- Pros: Gets full page content
- Cons: Requires login, slower, needs browser CDP connection

```bash
browser_navigate("https://wiki.ucb.local/pages/viewpage.action?pageId=<ID>")
browser_snapshot(full=true)
```

### Strategy 2: Read Saved File
MCP saves full responses to `/tmp/hermes-results/`. Use `read_file` to access them.
- Pros: Already has full content
- Cons: Need to know the filename from the tool call

### Strategy 3: Version Diff
Use `confluence_get_page_diff` between versions to understand changes without reading full content.
- Pros: Lightweight, focused
- Cons: Only shows differences, not full picture

### Strategy 4: Child Pages
Break up content by navigating to child pages (`confluence_get_page_children`).
- Pros: Each child is smaller
- Cons: Not all docs use child pages

### Strategy 5: Extract Specific Sections
Use Python to parse the raw HTML/content and extract only needed sections.
- Pros: Targeted, avoids loading everything
- Cons: Requires scripting

## Architecture Review Pattern

When reviewing Confluence architecture documents:

1. **Check section completeness** — list all section headers, verify no gaps
2. **Scan tables for data vs placeholders** — empty rows, "Пример:", "incomplete" markers
3. **Verify approval status** — check for `pageapproval` macro, comments, labels
4. **Look for version metadata** — date updated, version number consistency
5. **Cross-reference attachments** — diagrams, images that may contain real content

### Template Indicators (document is NOT filled)
- All table cells empty: `|  |  |  |  |`
- Placeholder IDs: "bus_object_id_1_client", "Пример: Клиент"
- Dropdown options listed as text: "32 incomplete Планируется..."
- Section exists but nothing below it
- Date fields blank despite version being set
- `allapprovaltrue` macro with zero comments

### Real Content Indicators (document IS filled)
- Tables have populated rows with actual data
- PlantUML / Mermaid diagrams with real components
- Specific IPs, FQDNs, port numbers in network tables
- Named approvers in comments
- Labels like "approved", "reviewed" on page
