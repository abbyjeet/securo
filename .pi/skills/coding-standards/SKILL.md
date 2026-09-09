---
description: enforces and explains Securo's code style, type conventions, linting rules, and architectural patterns
---

# Coding Standards Skill

## Objective
Enforce and explain Securo's code style, type conventions, linting rules, and architectural patterns. Use this skill when reviewing PRs, writing new code, or answering questions like "why use Decimal instead of float?"

## When to use
- "What linter do we use for Python?"
- "How should I write a SQLAlchemy model here?"
- "Why is there no ruff format in our config?"
- "Show me an example of a proper FastAPI router."

## Knowledge boundaries
This skill covers:
- Backend Python: ruff rules, ty type checking, SQLAlchemy ORM patterns, decimal arithmetic rules
- Frontend TypeScript: ESLint configs, Tailwind CSS usage, React component patterns (lazy loading, providers)
- General conventions: migration numbering, feature flagging strategy, pre-commit hooks

## Response pattern
Start with a brief summary of the project's philosophy ("we review humans, not AI"). Then list each rule as a bullet point with its rationale. Provide a short code example if it illustrates a common pitfall (e.g., using `Decimal` instead of `float` for money). Refer back to the relevant config files (`pyproject.toml`, `.pre-commit-config.yaml`) when explaining tool versions or thresholds.
