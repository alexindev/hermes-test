# mcp-atlassian Confluence Tools Reference

Source: `sooperset/mcp-atlassian` (PyPI), docs at https://mcp-atlassian.soomiles.com

## Confluence Tools (19 tools)

### Search & Discovery
| Tool | Params | Description |
|------|--------|-------------|
| `confluence_search` | query (CQL string), limit, cursor, expand | Search pages, blogs, comments by CQL |
| `confluence_search_user` | query (string), limit | Find users by name/email |
| `confluence_get_page` | page_id (int), expand | Get full page content (storage or view format) |
| `confluence_get_page_children` | page_id (int), depth (all/root), limit | Get child page tree |
| `confluence_get_page_history` | page_id (int), limit | Version history |
| `confluence_get_page_diff` | page_id (int), version_from (int), version_to (int) | Diff between two versions |

### Content Management
| Tool | Params | Description |
|------|--------|-------------|
| `confluence_create_page` | space_key (str), title (str), body (str), parent_id (int, opt) | Create new page |
| `confluence_update_page` | page_id (int), title (str), body (str), version (int) | Update existing page |
| `confluence_delete_page` | page_id (int) | Delete page |
| `confluence_move_page` | page_id (int), target_page_id (int), position (str: append/before/after) | Move/reparent page |

### Comments
| Tool | Params | Description |
|------|--------|-------------|
| `confluence_get_comments` | page_id (int), limit | List comments on a page |
| `confluence_add_comment` | page_id (int), body (str) | Add inline comment |
| `confluence_reply_to_comment` | comment_id (str), body (str) | Reply to existing comment |

### Labels & Analytics
| Tool | Params | Description |
|------|--------|-------------|
| `confluence_get_labels` | page_id (int) | List labels on a page |
| `confluence_add_label` | page_id (int), name (str) | Add label to page |
| `confluence_get_page_views` | page_id (int) | Page view analytics |

### Attachments
| Tool | Params | Description |
|------|--------|-------------|
| `confluence_get_attachments` | page_id (int), limit | List attachments |
| `confluence_upload_attachment` | page_id (int), file_path (str), comment (str, opt) | Upload single file |
| `confluence_upload_attachments` | page_id (int), file_paths (list[str]) | Upload multiple files |
| `confluence_download_attachment` | attachment_id (str), output_dir (str) | Download attachment |
| `confluence_download_content_attachments` | page_id (int), output_dir (str) | Download all page attachments |
| `confluence_delete_attachment` | attachment_id (str) | Delete attachment |
| `confluence_get_page_images` | page_id (int) | Get inline images |

### Toolset Groups
- `confluence_pages` — search, get_page, get_page_children, create, update, delete, move, diff, history
- `confluence_comments` — get_comments, add_comment, reply_to_comment
- `confluence_labels` — get_labels, add_label
- `confluence_users` — search_user
- `confluence_analytics` — get_page_views
- `confluence_attachments` — upload, download, list, delete, get_images
