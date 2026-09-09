---
description: provides a mental model of Securo's directory layout and explains the purpose of major directories
---

# Structure Skill

## Objective
Provide a mental model of Securo's directory layout, key file locations, and the purpose of major directories. Use this skill when navigating the codebase, locating files, or understanding where to add new features.

## When to use
- "Where are the models?"
- "How is the router organized?"
- "Where do I add a new bank provider?"
- "What's the difference between `migrations/` and `alembic/versions/`?"

## Knowledge boundaries
This skill covers:
- The full directory tree of both `backend/` and `frontend/`
- The purpose of each major subdirectory
- Key files at the repository root (`pyproject.toml`, `docker-compose.yml`, etc.)
- The relationship between SQLAlchemy models, Alembic migrations, and runtime code

Do NOT provide line-level details about specific files. For API route definitions, use the `where-to-look` skill instead.

## Response pattern
Start with a high-level tree view showing only top 3 levels of nesting for readability. Then present a table mapping major directories to their purpose. When asked about a specific file type (e.g., "where are migrations?"), give the direct path without re-listing everything.
