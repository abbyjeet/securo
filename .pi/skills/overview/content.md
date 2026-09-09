# Securo — Self-hosted personal finance manager

**License:** AGPL-3.0  
**Website:** https://usesecuro.com/  
**Demo:** https://demo.usesecuro.com/

## What is Securo?

A privacy-first, self-hosted personal finance application that gives users full control over their financial data without surrendering it to third parties. It supports bank synchronization via multiple providers (Pluggy for Brazilian banks, Enable Banking for European PSD2-compliant banks, SimpleFIN for US/international banks), multi-currency accounts with automatic FX conversion, budgeting, goal tracking, asset valuation, report generation, and optional AI agents with MCP tool-use.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.x (asyncpg driver), Celery + Redis for background tasks, Alembic for migrations, Pydantic v2 for schemas |
| Frontend | React 19, TypeScript 5.9, Vite 8, Tailwind CSS 4, TanStack Query, Zod validation, i18n (EN + PT-BR) |
| Database | PostgreSQL 16+ with pgvector extension (for AI agents' RAG knowledge base) |
| Queue | Redis + Celery workers |

## Key Features

- **Multi-account management** with running balances and fiscal-year-aware categorization
- **Bank synchronization** via Pluggy, Enable Banking, SimpleFIN — extensible architecture for new providers
- **Auto-categorization rules engine** that learns from user corrections
- **Recurring transactions** and budgeting with progress tracking
- **Asset management** with Tesouro Direto (Brazilian government bonds) integration
- **Multi-currency support** with on-demand FX rates via Open Exchange Rates
- **Reports:** Net Worth tracker, Income vs Expenses with category sparklines
- **Invoicing:** Generate and share PDF invoices from transaction selections
- **AI Agents** (optional): Self-hosted LLM chatbot over your data with MCP tool-use and per-agent RAG knowledge bases

## Quick Start

### Docker / Podman (Linux & macOS)

```bash
curl -fsSL https://usesecuro.com/install.sh | bash
```

This installs Docker or Podman, builds the images, and starts the full stack. Open `http://localhost:3000` in your browser to begin setting up your workspace.

### Manual (Docker Compose)

```bash
git clone https://github.com/securo-finance/securo.git && cd securo
docker compose up --build
```

Then visit [http://localhost:3000](http://localhost:3000).

## Bank Sync Providers (Optional)

Add credentials to your `.env` file and restart the stack for each provider you want to use. See `CONTRIBUTING.md#bank-sync-optional` for detailed setup instructions.

## AI Agents (Optional)

The agents feature is opt-in (`AGENTS_ENABLED=true`) so non-subscribers incur zero cost: no imports, no network calls, no background tasks when the flag is off. Set it and restart with `docker compose up -d --profile agents`.
