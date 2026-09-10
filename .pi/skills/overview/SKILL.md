---
title: Overview — Project Mission, Tech Stack & Key Features
description: "High-level overview of Securo: a self-hosted privacy-first personal finance manager. Covers mission statement, key features (bank sync, multi-currency, budgets, goals, envelope budgeting, AI agents), tech stack (Python FastAPI + React TypeScript), directory layout mental model, and design principles (type safety everywhere, minimal coupling, zero-cost optional features)."
---

# Securo — Project Overview

## What is Securo?

Securo is a **self-hosted, privacy-first personal finance manager** that gives you full control over your financial data without surrendering it to third parties.

### Core Philosophy

> "Your money belongs to you. Your financial data should never be scraped, sold, or used against you."

Unlike consumer apps (YNAB, Mint, Rocket Money) that monetize by selling user data, Securo runs entirely on your own infrastructure — whether that's a home server, NAS, or cloud VPS of your choosing.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Bank Sync** | Connect to Brazilian banks (Pluggy), European PSD2 banks (Enable Banking), US/international banks (SimpleFIN). Transactions flow directly from bank → Securo; you never type numbers manually. |
| **Multi-Currency** | Track spending in USD, EUR, BRL, JPY, or any other currency with automatic conversion and exchange rate history. |
| **Budgets & Goals** | Set monthly budgets per category, track progress visually, and set savings goals with milestone tracking. |
| **Envelope Budgeting** | Allocate a fixed amount to each spending "envelope" at the start of the month; when it's gone, you stop spending in that envelope until next month. |
| **AI Agents (optional)** | Natural language queries like "Show me my coffee spending last month" or "Why did I overspend on groceries?" — powered by MCP tool-use agents. |
| **Self-Hosted** | Full control over your data, complete transparency about what runs on your server, no mandatory cloud sync required. |

---

## Tech Stack

### Backend (Python 3.11+)

- **Framework:** FastAPI (async, type-safe, auto-generated OpenAPI docs)
- **Database:** PostgreSQL 16+ with `pgvector` extension for AI embeddings
- **ORM:** SQLAlchemy 2.x (asyncpg driver)
- **Background tasks:** Celery + Redis queue
- **Validation:** Pydantic v2
- **Linting:** Ruff, Ty (type checker)

### Frontend (React 19 + TypeScript)

- **Build tool:** Vite 8
- **Styling:** Tailwind CSS v4 + utility-first classes
- **State management:** React Query for server state, TanStack Query hooks (`useQuery`, `useMutation`)
- **Routing:** React Router DOM with lazy-loaded route components
- **Forms:** React Hook Form + Zod schemas for validation
- **UI primitives:** Radix UI under the hood; shadcn-like reusable components

### Infrastructure

| Component | Technology |
|-----------|-----------|
| Database | PostgreSQL 16+ (with `pgvector`) |
| Cache / Queue | Redis |
| Web Server | Uvicorn + Gunicorn (for WSGI/ASGI apps) |
| Containerization | Docker Compose for local dev; production compose with no volumes exposed |

---

## Directory Layout (Mental Model)

```
securo/
├── backend/          # FastAPI server
│   ├── alembic/     # Database migrations
│   ├── app/api/    # HTTP routes, one file per domain
│   ├── app/models/# SQLAlchemy ORM models
│   ├── app/schemas/# Pydantic request/response models
│   ├── app/services/# Business logic (no HTTP concerns)
│   └── app/tasks/  # Celery job definitions
├── frontend/        # Vite React app
│   └── src/
│       ├── pages/  # Route-level components (lazy-loaded)
│       └── lib/    # Shared utilities, API client types
└── docker-compose.yml  # Full stack for local development
```

**Rule of thumb:** If you need to change a database column → `app/models/*.py` + new Alembic migration. If you need to add an HTTP endpoint → `app/api/*.py`. If you're building a UI feature → `frontend/src/pages/*` or `frontend/src/components/ui/*`.

---

## How to Get Started Locally

```bash
cd /home/abhijit/git/securo
docker compose up --build
```

This spins up PostgreSQL, Redis, the backend API server, and the frontend dev server (with hot-reload). Then open http://localhost:5173 in your browser.

---

## Design Principles

- **Type safety everywhere:** TypeScript on the frontend, Pydantic + type hints on the backend. Type errors are caught at build time or type-check time.
- **Minimal coupling:** Each API router file is independent; each service function has a single responsibility. Migrations are versioned and chained so they can't conflict.
- **Zero-cost optional features:** AI agents, bank sync providers, and other expensive-to-run services are gated behind environment variables. If disabled, no imports or network calls happen at all.
- **Privacy by design:** No telemetry, no analytics SDKs, no mandatory cloud sync. You own your data completely.

---

## Related Skills

- `structure/SKILL.md` — detailed file-by-file walkthrough of the repo layout
- `frontend-patterns/SKILL.md` — component patterns, React Query usage, form state sync
- `coding-standards/SKILL.md` — linting rules, type conventions, migration best practices
- `notes/SKILL.md` — critical context, bug fixes, design decisions, debugging tips
