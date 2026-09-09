---
description: provides commands for running Securo (starting servers, tests, linting, building)
---

# Commands Skill

## Objective
Provide the exact commands needed to run Securo: starting servers, running tests, linting, building, migrating, and common DevOps tasks. Use this skill when a user asks "how do I..." or needs to run an operation in CI/CD pipelines.

## When to use
- "How do I start the backend?"
- "What's the command for frontend linting?"
- "How do I apply database migrations?"
- "What's the CI command for backend tests?"

## Knowledge boundaries
This skill covers:
- Starting/restarting the stack (Docker Compose)
- Running tests with coverage
- Linting and type checking (ruff, ty)
- Building frontend artifacts
- Managing dependencies (uv sync, lockfile regeneration)
- Alembic migrations
- Environment variable setup

Do NOT provide commands for unsupported platforms or unofficial tools. Stick to the documented workflow in CONTRIBUTING.md and docker-compose.yml.

## Response pattern
Present commands as code blocks with brief explanations of what each flag does. Group by category (start, test, lint, build). Include a note about `mise` as an optional tool for managing Python/Node versions across backend/frontend directories.
