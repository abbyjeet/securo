---
description: surfaces critical context, gotchas, and architectural trade-offs that aren't obvious from code alone
---

# Notes & Gotchas Skill

## Objective
Surface critical context, gotchas, and "why we do it this way" notes that aren't obvious from the code alone. Use this skill when an agent needs to understand edge cases or avoid common mistakes.

## When to use
- "Why don't we enable `AGENTS_ENABLED` by default?"
- "What happens if two migrations land on main at once?"
- "How do OIDC and password auth work together?"

## Knowledge boundaries
This skill covers:
- Architecture decisions with trade-offs (e.g., why the MCP server is modular)
- Zero-cost optional features
- Migration chain validation strategy
- OIDC-only mode behavior for existing users
- Passkey restrictions from WebAuthn spec
- Tesouro Direto cache warmup gating

## Response pattern
Frame each point as a "gotcha" or "why this design decision" so the agent understands the rationale. If something is configurable, mention the env var that controls it.
