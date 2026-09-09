---
description: points directly to the correct files and directories for a given task or domain
---

# Where To Look Skill

## Objective
Point directly to the correct files and directories for a given task or domain. Use this skill when an agent needs to find code quickly without scanning the entire repo.

## When to use
- "Where are the transaction models?"
- "How do I add a new bank sync provider?"
- "Where's the dashboard page component?"
- "Where are the AI agents' MCP tools defined?"

## Knowledge boundaries
This skill covers:
- Direct paths to specific files and directories
- Mapping between user-facing concepts (e.g., "budgets") and their implementation locations (`app/services/budget_service.py`)
- The structure of the optional AI agents feature, including both the API side (`api/agents/` routers) and the MCP server side (`mcp_server/`)

Do NOT provide line-level details. For that, use the `coding-standards` skill or search directly in source files.

## Response pattern
Start with a short sentence naming the file and its purpose. Include the relative path from `/home/abhijit/git/securo`. If relevant, mention adjacent related files (e.g., "the schema lives next to this model"). Group answers by domain when multiple locations are possible (e.g., "two places handle bank sync: `api/connections.py` and `services/bank_sync_service.py`").
